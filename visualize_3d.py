import json
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# ================= 配置区域 =================
JSON_PATH = r"C:\D\oppo\Yoga-82\yoga_standard_yolo.json"
# 想要查看的动作名称 (请确保 JSON 里有这个 key)
TARGET_ACTION = "Bharadvaja's_Twist_pose_or_Bharadvajasana_I_"
# ===========================================

# COCO 17点 骨骼连接规则
SKELETON_CONNECTIONS = [
    (5, 6), (11, 12), (5, 11), (6, 12),  # 躯干
    (5, 7), (7, 9),  # 左臂
    (6, 8), (8, 10),  # 右臂
    (11, 13), (13, 15),  # 左腿
    (12, 14), (14, 16)  # 右腿
]

# 颜色配置
COLOR_LEFT = 'blue'
COLOR_RIGHT = 'red'
COLOR_BODY = 'black'


def visualize_action_3d():
    # 1. 读取数据
    try:
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到文件: {JSON_PATH}")
        return

    if TARGET_ACTION not in data:
        print(f"❌ 动作 '{TARGET_ACTION}' 不在数据库中。")
        print(f"可选动作: {list(data.keys())}")
        return

    # 2. 随机获取该动作的一张样本进行展示
    # (实际应用中可以做个循环展示，这里先展示第一张)
    samples = data[TARGET_ACTION]
    if not samples:
        print("该动作下没有数据。")
        return

    # 我们取置信度最高或者第一个样本
    sample = samples[0]
    print(f"正在可视化: {TARGET_ACTION} (来源图片: {sample['image_name']})")

    # 3. 解析关键点
    # YOLO 只有 x, y。为了在 3D 图里画出来，我们将 z 设为 0 (或者根据人体结构伪造一个深度，但这里先保持真实)
    # 这里的 x, y 是归一化的 (0-1)，为了绘图好看，我们把它放缩一下

    landmarks = sorted(sample['landmarks'], key=lambda x: x['id'])

    # 提取坐标
    xs = []
    ys = []
    zs = []  # 这是一个伪 3D，因为 YOLO 没有 Z 轴

    for lm in landmarks:
        # matplotlib 的坐标系习惯：
        # y 轴通常是高度（需要取反，因为图像坐标原点在左上角）
        # x 轴是宽度
        xs.append(lm['x'])
        ys.append(1.0 - lm['y'])  # 翻转 Y 轴，让人站起来
        zs.append(0)  # 暂时没有深度信息

    # 4. 开始绘图
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # 设置视角 (Elev=0 是平视)
    ax.view_init(elev=10, azim=-90)

    # 绘制关键点
    ax.scatter(xs, zs, ys, c='black', marker='o', s=50)

    # 绘制骨骼连线
    for connection in SKELETON_CONNECTIONS:
        start_idx, end_idx = connection

        # 获取起点和终点的坐标 (注意关键点索引可能不是连续的，要小心越界)
        # YOLO 输出 17 个点，索引是 0-16
        if start_idx < len(xs) and end_idx < len(xs):
            x_pair = [xs[start_idx], xs[end_idx]]
            y_pair = [ys[start_idx], ys[end_idx]]  # 高度
            z_pair = [zs[start_idx], zs[end_idx]]  # 深度 (0)

            # 简单的颜色区分
            color = COLOR_BODY
            if start_idx in [5, 7, 9, 11, 13, 15] or end_idx in [5, 7, 9, 11, 13, 15]:
                color = COLOR_LEFT  # 左侧肢体
            elif start_idx in [6, 8, 10, 12, 14, 16] or end_idx in [6, 8, 10, 12, 14, 16]:
                color = COLOR_RIGHT  # 右侧肢体

            # 也就是画线：(x1, x2), (z1, z2), (y1, y2) -> 注意 Matplotlib 3D 的轴顺序通常是 X, Z, Y (高度作为 Z)
            # 这里我们将 Y 列表传给绘图的 z 参数，让人站立
            ax.plot(x_pair, z_pair, y_pair, c=color, linewidth=3)

    # 5. 设置坐标轴与标签
    ax.set_xlabel('X Label (Width)')
    ax.set_ylabel('Z Label (Depth - Missing)')
    ax.set_zlabel('Y Label (Height)')

    # 调整比例，防止压扁
    ax.set_box_aspect([1, 0.2, 1])  # 因为 Z 是扁的，压扁一点看起来自然

    plt.title(f"Standard Action Visualization: {TARGET_ACTION}\n(Source: {sample['image_name']})")
    print("窗口已弹出。你可以用鼠标拖动旋转骨架！")
    plt.show()


if __name__ == "__main__":
    visualize_action_3d()