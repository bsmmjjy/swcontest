# 视频上传与推理接口
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import os
import shutil
from pathlib import Path

from ..database import get_db
from ..models import User, Video
from ..schemas import InferenceResponse, StandardPoseResponse
from ..services.ai_engine import PoseAnalyzer
from ..core.config import settings
from .auth import get_current_user, get_optional_current_user

router = APIRouter(prefix="", tags=["业务"])

# 初始化 AI 引擎
ai_engine = PoseAnalyzer(angles_json_path=str(settings.YOGA_ANGLES_JSON))

@router.post("/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    action_type: Optional[str] = Form(None),
    camera_angle: Optional[str] = Form(None),
    device: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传视频文件"""
    # 验证文件类型
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，仅支持: {', '.join(allowed_extensions)}"
        )
    
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    original_filename = settings.UPLOAD_DIR / f"{file_id}{file_ext}"
    
    # 保存文件
    try:
        with open(original_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )
    
    # 创建数据库记录
    try:
        video = Video(
            user_id=current_user.user_id,
            file_path=str(original_filename),
            action_type=action_type,
            camera_angle=camera_angle,
            device=device
        )
        db.add(video)
        db.commit()
        db.refresh(video)
    except Exception as e:
        db.rollback()
        # 删除已上传的文件
        if original_filename.exists():
            os.remove(original_filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库记录创建失败: {str(e)}"
        )
    
    return {
        "video_id": video.video_id,
        "file_path": video.file_path,
        "action_type": video.action_type,
        "created_at": video.created_at
    }

@router.post("/infer/sync", response_model=InferenceResponse)
async def sync_inference(
    file: UploadFile = File(...),
    actionType: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    同步推理接口：
    1. 保存上传的视频
    2. 调用 AI 引擎逐帧分析并绘制建议
    3. 返回处理后的视频 URL 和分析结果
    """
    # 1. 保存原始视频
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，仅支持: {', '.join(allowed_extensions)}"
        )
    
    file_id = str(uuid.uuid4())
    original_filename = settings.UPLOAD_DIR / f"{file_id}{file_ext}"
    
    try:
        with open(original_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )
    
    # 2. 定义输出路径
    processed_filename = settings.OUTPUT_DIR / f"processed_{file_id}.mp4"
    
    # 3. AI 处理
    try:
        result = ai_engine.process_video(
            input_path=str(original_filename),
            output_path=str(processed_filename),
            target_pose_name=actionType
        )
    except Exception as e:
        # 删除临时文件
        if original_filename.exists():
            os.remove(original_filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 分析失败: {str(e)}"
        )
    
    # 4. 创建数据库记录（如果用户已登录）
    if current_user:
        try:
            video = Video(
                user_id=current_user.user_id,
                file_path=str(original_filename),
                processed_path=str(processed_filename),
                action_type=actionType,
                score=result.get("score"),
                suggestions=result.get("suggestions", [])
            )
            db.add(video)
            db.commit()
        except Exception as e:
            db.rollback()
            # 注意：这里不删除文件，因为处理已完成，只是数据库记录失败
            print(f"警告: 数据库记录创建失败: {str(e)}")
    
    # 5. 构建返回结果
    # 构建相对路径，用于静态文件访问
    relative_path = str(processed_filename.relative_to(settings.BASE_DIR)).replace("\\", "/")
    video_url = f"{settings.BASE_URL}{settings.STATIC_URL}/{relative_path}"
    
    return InferenceResponse(
        status="completed",
        result={
            "action": actionType,
            "score": result.get("score"),
            "video_url": video_url,
            "suggestions": result.get("suggestions", [])
        },
        video_url=video_url,
        score=result.get("score"),
        suggestions=result.get("suggestions", [])
    )

@router.get("/standards")
def get_standards():
    """返回支持的动作列表供前端选择"""
    standards_list = []
    for action_id, angles in ai_engine.standards.items():
        # 生成显示名称（去除下划线和特殊字符）
        display_name = action_id.replace("_", " ").replace("'", "'")
        standards_list.append({
            "actionId": action_id,
            "displayName": display_name,
            "angles": angles,
            "primaryViews": ["front", "side"]  # 默认视角
        })
    return standards_list

@router.get("/standards/{action_id}")
def get_standard(action_id: str):
    """获取特定动作的标准数据"""
    if action_id not in ai_engine.standards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到动作: {action_id}"
        )
    
    display_name = action_id.replace("_", " ").replace("'", "'")
    return {
        "actionId": action_id,
        "displayName": display_name,
        "angles": ai_engine.standards[action_id],
        "primaryViews": ["front", "side"]
    }

@router.get("/health")
def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "AIMovement API",
        "version": "1.0.0"
    }
