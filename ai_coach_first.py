import cv2
import mediapipe as mp
import numpy as np
import json
import time

# ================= 配置区域 =================
# 1. 角度数据库路径
ANGLES_JSON_PATH = r"C:\D\oppo\Yoga-82\yoga_angles.json"

# 2. 你想练习的动作 (必须是 JSON 里有的 key)
TARGET_ACTION = "Tree_Pose"

# 3. 容忍度 (超过这个角度差就开始报错)
THRESHOLD = 20.0
# ===========================================

# MediaPipe 初始化
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    static_image_mode=False,  # 视频流模式
    model_complexity=1,  # 1=Lite/2=Heavy (1更快，实时性好)
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 关节定义 (保持和之前 extract_angles.py 一致)
JOINTS = {
    "left_elbow": [11, 13, 15],
    "right_elbow": [12, 14, 16],
    "left_shoulder": [23, 11, 13],
    "right_shoulder": [24, 12, 14],
    "left_knee": [23, 25, 27],
    "right_knee": [24, 26, 28],
    "left_hip": [11, 23, 25],
    "right_hip": [12, 24, 26],
}


def load_standard_angles():
    try:
        with open(ANGLES_JSON_PATH, 'r') as f:
            data = json.load(f)
            if TARGET_ACTION in data:
                print(f"[OK] 已加载标准动作: {TARGET_ACTION}")
                return data[TARGET_ACTION]
            else:
                print(f"[ERROR] 数据库里没有动作: {TARGET_ACTION}")
                return None
    except Exception as e:
        print(f"[ERROR] 读取 JSON 失败: {e}")
        return None


def calculate_angle_3d(a, b, c):
    """ 计算 3D 角度 """
    a = np.array([a.x, a.y, a.z])
    b = np.array([b.x, b.y, b.z])
    c = np.array([c.x, c.y, c.z])

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba == 0 or norm_bc == 0:
        return 0.0

    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    angle = np.degrees(np.arccos(cosine_angle))
    return angle


def main():
    standard_angles = load_standard_angles()
    if standard_angles is None:
        return

    cap = cv2.VideoCapture(0)

    # 简单的 FPS 计数
    p_time = 0

    print("[INFO] 摄像头已启动，请站在摄像头前...")
    print("按 'q' 退出程序")

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        # 镜像翻转，像照镜子一样
        image = cv2.flip(image, 1)
        h, w, _ = image.shape

        # 转 RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image_rgb)
        image.flags.writeable = True

        # 转回 BGR 用于显示
        image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        # 核心逻辑
        if results.pose_world_landmarks:
            landmarks = results.pose_world_landmarks.landmark

            # 用于绘制骨架的 2D 坐标 (用于画图)
            landmarks_2d = results.pose_landmarks.landmark

            error_messages = []
            total_score = 100

            # 遍历每一个关键关节进行检查
            for joint_name, (idx1, idx2, idx3) in JOINTS.items():
                # 计算用户的实时角度
                user_angle = calculate_angle_3d(
                    landmarks[idx1], landmarks[idx2], landmarks[idx3]
                )

                # 获取标准角度
                std_angle = standard_angles.get(joint_name, -1)

                if std_angle == -1: continue  # 如果标准库里没有这个数据，跳过

                # 计算偏差
                diff = abs(user_angle - std_angle)

                # 获取 2D 坐标用于在屏幕上显示角度文字
                # 关节中心点
                cx, cy = int(landmarks_2d[idx2].x * w), int(landmarks_2d[idx2].y * h)

                # 判定颜色
                color = (0, 255, 0)  # 绿色 (Good)
                if diff > THRESHOLD:
                    color = (0, 0, 255)  # 红色 (Bad)
                    total_score -= 10  # 扣分

                    # 生成指导意见
                    if user_angle < std_angle:
                        msg = f"Extend {joint_name}!"  # 需要伸展
                    else:
                        msg = f"Bend {joint_name}!"  # 需要弯曲
                    error_messages.append(msg)

                # 在关节旁边显示实时角度
                cv2.putText(image, str(int(user_angle)), (cx, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # 可视化圆圈
                cv2.circle(image, (cx, cy), 8, color, -1)

            # --- 绘制 UI ---
            # 1. 绘制基本骨架
            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
            )

            # 2. 显示总分
            score_color = (0, 255, 0)
            if total_score < 80: score_color = (0, 255, 255)  # 黄
            if total_score < 60: score_color = (0, 0, 255)  # 红

            cv2.rectangle(image, (0, 0), (250, 150), (0, 0, 0), -1)  # 背景黑框
            cv2.putText(image, f"Score: {max(0, total_score)}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, score_color, 2)

            # 3. 显示指导建议 (只显示前 2 条，避免刷屏)
            y_offset = 80
            if not error_messages:
                cv2.putText(image, "Perfect!", (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                for msg in error_messages[:2]:
                    cv2.putText(image, msg, (10, y_offset),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    y_offset += 30

        # 计算 FPS
        c_time = time.time()
        fps = 1 / (c_time - p_time)
        p_time = c_time
        cv2.putText(image, f"FPS: {int(fps)}", (w - 100, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow('AI Yoga Coach', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()