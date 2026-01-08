import json
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib  # 新增：导入matplotlib核心模块
import mediapipe as mp
import numpy as np
matplotlib.use('TkAgg')
# ================= 修复中文显示 =================
# 设置中文字体（Windows 系统）
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 黑体
matplotlib.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题
# ===============================================

# ================= 配置区域 =================
JSON_PATH = r"yoga_standard_mp.json"
# 使用 JSON 中正确的动作名称
TARGET_ACTION = "Akarna_Dhanurasana"
# ===========================================

# MediaPipe 官方定义的骨骼连接
MP_CONNECTIONS = mp.solutions.pose.POSE_CONNECTIONS


def visualize_json_3d():
    # 1. 读取 JSON 数据
    try:
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到文件: {JSON_PATH}")
        return

    # 2. 检查动作是否存在
    if TARGET_ACTION not in data:
        print(f"❌ 动作 '{TARGET_ACTION}' 不在数据库中。")
        print(f"✅ 数据库中包含的动作有: {list(data.keys())}")
        if len(data.keys()) > 0:
            demo_action = list(data.keys())[0]
            print(f"-> 自动切换演示动作: {demo_action}")
            samples = data[demo_action]
        else:
            return
    else:
        samples = data[TARGET_ACTION]

    if not samples:
        print("该动作下没有数据。")
        return

    # 3. 获取第一个样本的 3D 数据
    sample = samples[0]
    print(f"正在可视化: {sample['image_name']}")

    landmarks = sample['landmarks_3d']

    # 提取 x, y, z 并处理坐标系
    xs = [lm['x'] for lm in landmarks]
    ys = [lm['y'] for lm in landmarks]
    zs = [lm['z'] for lm in landmarks]

    # 4. 开始 3D 绘图
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # 设置视角
    ax.view_init(elev=10, azim=-90)

    # 绘制关键点
    ax.scatter(xs, zs, [-y for y in ys], c='r', marker='o', s=20)

    # 绘制骨骼
    for connection in MP_CONNECTIONS:
        start_idx = connection[0]
        end_idx = connection[1]

        x_pair = [xs[start_idx], xs[end_idx]]
        z_pair = [zs[start_idx], zs[end_idx]]
        y_pair = [-ys[start_idx], -ys[end_idx]]

        # 颜色区分：躯干黑色，四肢绿色
        color = 'black'
        if start_idx > 10 and end_idx > 10:
            color = 'green'

        ax.plot(x_pair, z_pair, y_pair, c=color, linewidth=2)

    # 5. 设置坐标轴标签
    ax.set_xlabel('X (左右)')
    ax.set_ylabel('Z (深度)')
    ax.set_zlabel('Y (高度)')

    # 强制坐标轴比例一致
    max_range = np.array([max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]).max() / 2.0
    mid_x = (max(xs) + min(xs)) * 0.5
    mid_y = (-max(ys) - min(ys)) * 0.5
    mid_z = (max(zs) + min(zs)) * 0.5

    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_z - max_range, mid_z + max_range)
    ax.set_zlim(mid_y - max_range, mid_y + max_range)

    plt.title(f"3D Skeleton Visualization: {TARGET_ACTION}")
    print("窗口已弹出。请用鼠标左键拖动旋转，查看 3D 效果！")
    plt.show()


if __name__ == "__main__":
    visualize_json_3d()