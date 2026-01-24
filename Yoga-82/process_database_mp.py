import cv2
import mediapipe as mp
import os
import json
import numpy as np
from tqdm import tqdm

# ================= 配置区域 =================
# 你的图片数据根目录
DATA_ROOT = r"C:\D\oppo\Yoga-82\data"
# 输出的 JSON 文件路径
OUTPUT_JSON = r"C:\D\oppo\Yoga-82\yoga_standard_mp.json"

# MediaPipe 初始化
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=True,  # 静态图片模式 (精度更高，且不依赖上一帧)
    model_complexity=2,  # 2 = Heavy 模型 (精度最高，适合做标准库)
    enable_segmentation=False,  # 不需要抠图，只取点
    min_detection_confidence=0.5
)


# ===========================================

def build_database():
    database = {}

    if not os.path.exists(DATA_ROOT):
        print(f"[ERROR] 错误：找不到数据目录 {DATA_ROOT}")
        return

    # 获取所有动作文件夹
    action_folders = [f for f in os.listdir(DATA_ROOT) if os.path.isdir(os.path.join(DATA_ROOT, f))]

    total_imgs = 0
    valid_imgs = 0

    print(f"检测到 {len(action_folders)} 个动作分类，开始构建 3D 标准库...")

    for action_name in action_folders:
        action_path = os.path.join(DATA_ROOT, action_name)
        image_files = [f for f in os.listdir(action_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if not image_files:
            continue

        database[action_name] = []

        # 进度条
        for img_file in tqdm(image_files, desc=f"处理 {action_name}"):
            total_imgs += 1
            img_full_path = os.path.join(action_path, img_file)

            # 1. 读取图片
            image = cv2.imread(img_full_path)
            if image is None:
                continue

            # 2. 转换颜色 (MediaPipe 需要 RGB)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # 3. 推理
            results = pose.process(image_rgb)

            # 4. 提取数据
            if results.pose_landmarks:
                # --- A. 归一化坐标 (2D 绘图与评分用) ---
                # x, y 是 0.0 ~ 1.0 的比例值
                norm_landmarks = []
                for lm in results.pose_landmarks.landmark:
                    norm_landmarks.append({
                        "x": lm.x,
                        "y": lm.y,
                        "z": lm.z,  # 这里的 z 是相对深度 (以髋关节为原点)
                        "v": lm.visibility  # 可见度
                    })

                # --- B. 真实世界 3D 坐标 (3D 重建核心) ---
                # x, y, z 单位大约是“米”，原点在臀部中心
                # 这是 MediaPipe 独有的，非常适合你的 3D 展示需求
                world_landmarks = []
                if results.pose_world_landmarks:
                    for lm in results.pose_world_landmarks.landmark:
                        world_landmarks.append({
                            "x": lm.x,
                            "y": lm.y,
                            "z": lm.z,
                            "v": lm.visibility
                        })

                # 存入数据库
                database[action_name].append({
                    "image_name": img_file,
                    "landmarks_2d": norm_landmarks,  # 用于屏幕绘制和打分
                    "landmarks_3d": world_landmarks  # 用于 3D 空间重建
                })
                valid_imgs += 1

    # 保存
    print("-" * 30)
    print(f"处理完成！")
    print(f"原始图片: {total_imgs} | 有效入库: {valid_imgs}")

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(database, f)

    print(f"[OK] 标准动作库已保存至: {OUTPUT_JSON}")


if __name__ == "__main__":
    build_database()