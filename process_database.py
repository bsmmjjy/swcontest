import os
import json
import torch
from ultralytics import YOLO
from tqdm import tqdm

# ================= 配置区域 =================
DATA_ROOT = r"C:\D\oppo\Yoga-82\data"
OUTPUT_JSON = r"C:\D\oppo\Yoga-82\yoga_standard_yolo.json"

# 自动选择设备: 如果有 CUDA (NVIDIA显卡) 就用 '0'，否则用 'cpu'
DEVICE = '0' if torch.cuda.is_available() else 'cpu'
print(f"正在加载 YOLOv8-Pose 模型 (使用设备: {DEVICE})...")

# 加载模型到指定设备
model = YOLO('yolov8n-pose.pt')


# ===========================================

def build_database():
    database = {}

    if not os.path.exists(DATA_ROOT):
        print(f"错误：找不到路径 {DATA_ROOT}")
        return

    action_folders = [f for f in os.listdir(DATA_ROOT) if os.path.isdir(os.path.join(DATA_ROOT, f))]

    total_images = 0
    valid_images = 0

    print(f"检测到 {len(action_folders)} 个动作分类，开始处理...")

    for action_name in action_folders:
        action_path = os.path.join(DATA_ROOT, action_name)
        image_files = [f for f in os.listdir(action_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if not image_files:
            continue

        database[action_name] = []

        # tqdm 进度条
        for img_file in tqdm(image_files, desc=f"处理 {action_name}"):
            total_images += 1
            img_full_path = os.path.join(action_path, img_file)

            try:
                # === 关键修改 ===
                # device=DEVICE: 显式指定使用 GPU 或 CPU
                results = model(img_full_path, device=DEVICE, verbose=False)

                # 检查是否检测到了人
                if results[0].keypoints is not None and results[0].keypoints.data.shape[1] > 0:
                    # 注意：如果用了 GPU，数据在显存里，必须先 .cpu() 才能转 .numpy()
                    kpts = results[0].keypoints.data[0].cpu().numpy()

                    h, w = results[0].orig_shape

                    landmarks = []
                    for i in range(17):
                        x, y, conf = kpts[i]
                        landmarks.append({
                            "id": i,
                            "x": float(x / w),  # 归一化
                            "y": float(y / h),
                            "c": float(conf)
                        })

                    database[action_name].append({
                        "image_name": img_file,
                        "landmarks": landmarks
                    })
                    valid_images += 1

            except Exception as e:
                # print(f"错误: {e}")
                continue

    print("-" * 30)
    print(f"处理完成！有效入库: {valid_images}/{total_images}")

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(database, f)

    print(f"数据库已保存至: {OUTPUT_JSON}")


if __name__ == "__main__":
    # 再次确认一下当前 PyTorch 的状态
    print(f"PyTorch 版本: {torch.__version__}")
    print(f"CUDA 是否可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"显卡型号: {torch.cuda.get_device_name(0)}")

    build_database()