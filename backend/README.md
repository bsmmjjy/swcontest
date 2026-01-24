# AIMovement 后端 API

基于 FastAPI 的 AI 运动教练后端服务，使用 MediaPipe 进行瑜伽动作分析。

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── models.py            # 数据库模型 (SQLAlchemy)
│   ├── schemas.py           # Pydantic 数据验证模型
│   ├── database.py          # 数据库连接
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py      # JWT 和密码加密
│   │   └── config.py        # 配置 (文件路径等)
│   ├── services/
│   │   ├── __init__.py
│   │   └── ai_engine.py     # 核心 AI 分析逻辑 (MediaPipe + 角度计算)
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # 登录注册接口
│       └── business.py     # 视频上传与推理接口
├── data/                    # 存放 JSON 数据
│   └── yoga_angles.json
├── uploads/                 # 存放用户上传的视频
├── outputs/                 # 存放 AI 处理后的视频
├── requirements.txt
├── run.py                   # 启动脚本
└── README.md
```

## 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

## 环境配置

创建 `.env` 文件（可选，使用默认值也可以）：

```env
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///./aimovement.db
BASE_URL=http://localhost:8000
```

## 启动服务

### 方式一：使用启动脚本

```bash
cd backend
python run.py
```

### 方式二：使用 uvicorn 直接启动

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/v1/health

## API 接口

### 认证接口

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录（OAuth2 表单）
- `POST /api/v1/auth/login/json` - 用户登录（JSON 格式）
- `GET /api/v1/auth/me` - 获取当前用户信息

### 业务接口

- `POST /api/v1/upload/video` - 上传视频文件
- `POST /api/v1/infer/sync` - 同步视频推理分析
- `GET /api/v1/standards` - 获取所有标准动作列表
- `GET /api/v1/standards/{action_id}` - 获取特定动作的标准数据
- `GET /api/v1/health` - 健康检查

## 使用示例

### 1. 用户注册

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com"
  }'
```

### 2. 用户登录

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### 3. 视频推理分析

```bash
curl -X POST "http://localhost:8000/api/v1/infer/sync" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@your_video.mp4" \
  -F "actionType=Akarna_Dhanurasana"
```

### 4. 获取标准动作列表

```bash
curl "http://localhost:8000/api/v1/standards"
```

## 数据库

默认使用 SQLite 数据库，文件位于项目根目录的 `aimovement.db`。

如需使用 PostgreSQL 或 MySQL，修改 `.env` 文件中的 `DATABASE_URL`：

```env
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## 注意事项

1. **视频格式**：支持 MP4、AVI、MOV、MKV、WEBM 格式
2. **动作名称**：`actionType` 参数必须与 `yoga_angles.json` 中的 key 完全匹配
3. **文件大小**：建议视频文件不超过 100MB
4. **处理时间**：视频处理时间取决于视频长度和分辨率，可能需要几分钟

## 开发说明

- 开发模式会自动重载代码更改
- API 文档可通过 Swagger UI 访问：http://localhost:8000/docs
- 所有上传的视频保存在 `uploads/` 目录
- 处理后的视频保存在 `outputs/` 目录

## 故障排除

1. **导入错误**：确保在 `backend` 目录下运行，或设置正确的 Python 路径
2. **MediaPipe 错误**：确保已安装所有依赖，特别是 `opencv-python` 和 `mediapipe`
3. **文件权限错误**：确保 `uploads/` 和 `outputs/` 目录有写入权限
4. **数据库错误**：删除 `aimovement.db` 文件重新创建数据库
