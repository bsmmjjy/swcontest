# 数据库模型 (SQLAlchemy)
from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")

class Video(Base):
    __tablename__ = "videos"
    
    video_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True, index=True)
    file_path = Column(String(500), nullable=False)
    processed_path = Column(String(500), nullable=True)  # 处理后的视频路径
    action_type = Column(String(200), nullable=True)  # 动作类型
    camera_angle = Column(String(50), nullable=True)  # 相机角度
    device = Column(String(100), nullable=True)  # 设备信息
    score = Column(Float, nullable=True)  # AI 评分
    suggestions = Column(JSON, nullable=True)  # 建议列表
    extra_metadata = Column(JSON, nullable=True)  # 其他元数据（metadata 是 SQLAlchemy 保留字）
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="videos")
