# 数据库连接
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import os

# 数据库 URL (SQLite 作为默认数据库，生产环境可改为 PostgreSQL/MySQL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aimovement.db")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()

# 依赖注入：获取数据库会话
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
