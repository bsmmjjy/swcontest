# Pydantic 数据验证模型
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# ========== 用户相关 ==========
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    user_id: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str

# ========== 视频相关 ==========
class VideoBase(BaseModel):
    action_type: Optional[str] = None
    camera_angle: Optional[str] = None
    device: Optional[str] = None

class VideoCreate(VideoBase):
    file_path: str

class VideoResponse(VideoBase):
    video_id: str
    user_id: str
    file_path: str
    processed_path: Optional[str] = None
    created_at: datetime
    score: Optional[float] = None
    suggestions: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

# ========== AI 分析相关 ==========
class InferenceRequest(BaseModel):
    video_id: Optional[str] = None
    action_type: str
    file_path: Optional[str] = None

class InferenceResponse(BaseModel):
    status: str
    result: Dict[str, Any]
    video_url: Optional[str] = None
    score: Optional[float] = None
    suggestions: Optional[List[str]] = None

class StandardPoseResponse(BaseModel):
    action_id: str
    display_name: Optional[str] = None
    angles: Dict[str, float]
    primary_views: Optional[List[str]] = None

# ========== 会话相关 ==========
class SessionCreate(BaseModel):
    user_id: str
    action_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime
    action_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
