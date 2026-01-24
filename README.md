# AIMovement - AI 运动教练系统

基于 MediaPipe 和 FastAPI 的智能瑜伽动作分析系统，支持实时视频分析和动作纠正建议。

## 项目概述

AIMovement 是一个完整的 AI 运动教练系统，包含：
- **后端 API**：基于 FastAPI 的 RESTful API 服务
- **前端应用**：基于 UniApp 的跨平台移动应用
- **AI 引擎**：使用 MediaPipe 进行姿态检测和角度分析

## 项目结构

```
oppo/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── models.py        # 数据库模型
│   │   ├── schemas.py       # 数据验证模型
│   │   ├── database.py      # 数据库连接
│   │   ├── core/            # 核心配置
│   │   ├── services/        # 业务服务
│   │   └── routers/         # API 路由
│   ├── data/                # 数据文件
│   ├── uploads/             # 上传文件目录
│   ├── outputs/             # 输出文件目录
│   └── requirements.txt     # Python 依赖
│
├── uniapp/                  # 前端应用
│   └── AIMovement/
│       ├── src/
│       │   ├── pages/       # 页面
│       │   ├── services/    # API 服务
│       │   └── App.vue      # 应用入口
│       └── package.json     # 前端依赖
│
└── Yoga-82/                 # 瑜伽数据集
    └── yoga_angles.json     # 标准角度数据
```

## 快速开始

### 后端启动

1. 安装 Python 依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 启动服务：
```bash
python run.py
```

服务将在 http://localhost:8000 启动

3. 访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 前端启动

1. 安装依赖：
```bash
cd uniapp/AIMovement
npm install
```

2. 配置 API 地址（在 `src/services/api.js` 中修改 `BASE_URL`）

3. 运行开发服务器（根据你的 UniApp 配置）

## 核心功能

### 1. 用户认证
- 用户注册
- 用户登录（JWT Token）
- 用户信息查询

### 2. 视频分析
- 视频上传
- 实时姿态检测
- 角度计算与对比
- 动作评分
- 纠正建议生成

### 3. 标准动作库
- 82 种瑜伽动作标准数据
- 动作列表查询
- 动作详情查询

## API 接口

### 认证接口
- `POST /api/v1/auth/register` - 注册
- `POST /api/v1/auth/login` - 登录
- `GET /api/v1/auth/me` - 获取当前用户

### 业务接口
- `POST /api/v1/upload/video` - 上传视频
- `POST /api/v1/infer/sync` - 同步视频分析
- `GET /api/v1/standards` - 获取动作列表
- `GET /api/v1/standards/{action_id}` - 获取动作详情

详细 API 文档请访问：http://localhost:8000/docs

## 技术栈

### 后端
- **FastAPI** - 现代 Python Web 框架
- **SQLAlchemy** - ORM 数据库操作
- **MediaPipe** - 姿态检测
- **OpenCV** - 视频处理
- **JWT** - 身份认证
- **Pydantic** - 数据验证

### 前端
- **UniApp** - 跨平台应用框架
- **Vue.js** - 前端框架

## 数据格式

### 标准动作数据格式

```json
{
  "Akarna_Dhanurasana": {
    "left_elbow": 130.03,
    "right_elbow": 122.26,
    "left_shoulder": 102.82,
    "right_shoulder": 84.59,
    "left_knee": 144.5,
    "right_knee": 117.37,
    "left_hip": 65.37,
    "right_hip": 52.45
  }
}
```

## 开发说明

### 环境要求
- Python 3.8+
- Node.js 14+
- SQLite（默认）或 PostgreSQL/MySQL

### 配置说明

创建 `backend/.env` 文件（可选）：
```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./aimovement.db
BASE_URL=http://localhost:8000
```

### 数据库迁移

数据库表会在首次启动时自动创建。如需重置：
```bash
rm backend/aimovement.db
python backend/run.py
```

## 使用示例

### 1. 用户注册并登录

```bash
# 注册
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "pass123", "email": "user1@example.com"}'

# 登录
curl -X POST "http://localhost:8000/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "pass123"}'
```

### 2. 视频分析

```bash
curl -X POST "http://localhost:8000/api/v1/infer/sync" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@video.mp4" \
  -F "actionType=Akarna_Dhanurasana"
```

### 3. 获取动作列表

```bash
curl "http://localhost:8000/api/v1/standards"
```

## 注意事项

1. **视频格式**：支持 MP4、AVI、MOV、MKV、WEBM
2. **动作名称**：必须与 `yoga_angles.json` 中的 key 完全匹配
3. **文件大小**：建议不超过 100MB
4. **处理时间**：取决于视频长度，可能需要几分钟

## 故障排除

### 后端问题
- **导入错误**：确保在 `backend` 目录下运行
- **MediaPipe 错误**：检查依赖是否正确安装
- **文件权限**：确保 `uploads/` 和 `outputs/` 目录可写

### 前端问题
- **API 连接失败**：检查 `BASE_URL` 配置
- **CORS 错误**：确保后端 CORS 配置正确

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交 Issue 和 Pull Request！
