import json
import numpy as np
import math

# ================= 配置 =================
INPUT_JSON = r"C:\D\oppo\Yoga-82\yoga_standard_mp.json"
OUTPUT_JSON = r"C:\D\oppo\Yoga-82\yoga_angles.json"
# =======================================

# 关节定义 (基于 MediaPipe 33点拓扑)
JOINTS = {
    # 关节名: [端点1, 顶点(关节中心), 端点2]
    "left_elbow": [11, 13, 15],  # 左肩 - 左肘 - 左腕
    "right_elbow": [12, 14, 16],  # 右肩 - 右肘 - 右腕
    "left_shoulder": [23, 11, 13],  # 左髋 - 左肩 - 左肘
    "right_shoulder": [24, 12, 14],  # 右髋 - 右肩 - 右肘
    "left_knee": [23, 25, 27],  # 左髋 - 左膝 - 左踝
    "right_knee": [24, 26, 28],  # 右髋 - 右膝 - 右踝
    "left_hip": [11, 23, 25],  # 左肩 - 左髋 - 左膝
    "right_hip": [12, 24, 26],  # 右肩 - 右髋 - 右膝
}


def calculate_angle_3d(a, b, c):
    """
    计算以 b 为顶点的 3D 角度 (0-180度)
    """
    # 转为 numpy 数组
    a = np.array([a['x'], a['y'], a['z']])
    b = np.array([b['x'], b['y'], b['z']])
    c = np.array([c['x'], c['y'], c['z']])

    # 向量 BA 和 BC
    ba = a - b
    bc = c - b

    # 计算余弦值
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    # 防止分母为 0
    if norm_ba == 0 or norm_bc == 0:
        return 0.0

    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)

    # 防止数值误差导致超出 [-1, 1]
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)

    # 反余弦得到弧度，再转角度
    angle = np.degrees(np.arccos(cosine_angle))
    return angle


def process_angles():
    try:
        with open(INPUT_JSON, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f" 找不到输入文件: {INPUT_JSON}")
        return

    angle_database = {}
    print(f"检测到 {len(data)} 个动作，开始计算高精度平均标准...")

    for action_name, samples in data.items():
        if not samples:
            continue

        print(f"正在处理: {action_name} (样本数: {len(samples)}) ...")

        # 1. 收集该动作下所有样本的所有关节角度
        # 结构: {'left_elbow': [170, 175, 168...], 'right_knee': [...]}
        all_samples_angles = {k: [] for k in JOINTS.keys()}

        valid_sample_count = 0

        for sample in samples:
            landmarks = sample['landmarks_3d']

            # 简单的完整性检查：确保关键点都在
            # MediaPipe 至少有 33 个点，我们用到的最大索引是 28
            if len(landmarks) < 29:
                continue

            for joint_name, (idx1, idx2, idx3) in JOINTS.items():
                p1 = landmarks[idx1]
                p2 = landmarks[idx2]
                p3 = landmarks[idx3]

                # 只有当可见性(visibility)还可以时才计算，避免由于遮挡产生的离谱数据
                # 如果数据里没有 'v' 字段，默认通过
                v1 = p1.get('v', 1.0)
                v2 = p2.get('v', 1.0)
                v3 = p3.get('v', 1.0)

                # 可见性阈值 (例如 0.5)，太低的点算出来的角度不可信
                if v1 > 0.5 and v2 > 0.5 and v3 > 0.5:
                    angle = calculate_angle_3d(p1, p2, p3)
                    # 过滤掉 0 度这种明显异常的
                    if angle > 1.0:
                        all_samples_angles[joint_name].append(angle)

            valid_sample_count += 1

        # 2. 计算平均值 (Mean)
        action_standard_angles = {}
        for joint, angles_list in all_samples_angles.items():
            if angles_list:
                # 【核心逻辑】求平均值
                avg_angle = np.mean(angles_list)

                # (可选进阶：如果你想更严谨，可以加上中位数 Median，抗干扰更强)
                # avg_angle = np.median(angles_list)

                action_standard_angles[joint] = round(float(avg_angle), 2)
            else:
                # 如果所有样本里这个关节都看不见（比如只有半身照），设为 -1 标识无效
                action_standard_angles[joint] = -1.0

        angle_database[action_name] = action_standard_angles

    # 保存结果
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(angle_database, f, indent=4)

    print("-" * 30)
    print(f" 高精度角度数据库已生成: {OUTPUT_JSON}")
    print("现在这个数据库代表了所有训练图片的‘平均标准姿态’。")


if __name__ == "__main__":
    process_angles()