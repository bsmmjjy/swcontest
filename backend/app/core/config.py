# 配置 (文件路径等)
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AIMovement API"
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./aimovement.db")
    
    # 文件路径配置
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    DATA_DIR: Path = BASE_DIR / "data"
    YOGA_ANGLES_JSON: Path = DATA_DIR / "yoga_angles.json"
    
    # CORS 配置
    CORS_ORIGINS: list = ["*"]  # 生产环境应指定具体域名
    
    # 静态文件配置
    STATIC_URL: str = "/static"
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.OUTPUT_DIR.mkdir(exist_ok=True)
settings.DATA_DIR.mkdir(exist_ok=True)
