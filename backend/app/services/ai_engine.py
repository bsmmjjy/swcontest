import cv2
import mediapipe as mp
import numpy as np
import json
import os
from typing import Dict, List, Any

# MediaPipe 初始化
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


class PoseAnalyzer:
    def __init__(self, angles_json_path: str):
        """初始化姿态分析器，加载标准角度数据"""
        if not os.path.exists(angles_json_path):
            raise FileNotFoundError(f"角度数据文件不存在: {angles_json_path}")
        
        # 加载瑜伽角度数据
        with open(angles_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 处理可能的 JSON 格式（可能是列表或字典）
            if isinstance(data, list) and len(data) > 0:
                self.standards = data[0] if isinstance(data[0], dict) else {}
            elif isinstance(data, dict):
                self.standards = data
            else:
                self.standards = {}

        # 定义关节名称与 MediaPipe 索引的映射关系
        # MediaPipe Index: 11=左肩, 13=左肘, 15=左腕, 23=左髋, 25=左膝, 27=左踝...
        self.joint_map = {
            "left_elbow": [11, 13, 15],  # 左肩-左肘-左腕
            "right_elbow": [12, 14, 16],  # 右肩-右肘-右腕
            "left_shoulder": [23, 11, 13],  # 左髋-左肩-左肘
            "right_shoulder": [24, 12, 14],  # 右髋-右肩-右肘
            "left_knee": [23, 25, 27],  # 左髋-左膝-左踝
            "right_knee": [24, 26, 28],  # 右髋-右膝-右踝
            "left_hip": [11, 23, 25],  # 左肩-左髋-左膝
            "right_hip": [12, 24, 26]  # 右肩-右髋-右膝
        }

    def calculate_angle(self, a: List[float], b: List[float], c: List[float]) -> float:
        """计算三点之间的角度 (b为顶点)"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle
        return angle

    def process_video(self, input_path: str, output_path: str, target_pose_name: str) -> Dict[str, Any]:
        """
        核心功能：读取视频，逐帧分析，绘制建议，保存视频
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            target_pose_name: 目标动作名称（需匹配 JSON 中的 key）
        
        Returns:
            包含处理结果、分数和建议的字典
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入视频文件不存在: {input_path}")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {input_path}")

        # 获取视频属性
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30  # 默认 30fps

        # 视频写入器 (使用 mp4v 编码，兼容性较好)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            cap.release()
            raise ValueError(f"无法创建输出视频文件: {output_path}")

        pose_tracker = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )

        # 获取该动作的标准角度数据
        target_standards = self.standards.get(target_pose_name, {})
        if not target_standards:
            # 如果没找到标准动作，给出警告但继续处理
            print(f"警告: 未找到动作 '{target_pose_name}' 的标准数据，将跳过角度对比")

        # 存储分析数据
        all_diffs = []  # 所有帧的偏差值
        analysis_summary = []  # 存储总分析报告
        frame_count = 0
        detected_frames = 0  # 检测到姿态的帧数

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # 1. 姿态检测
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose_tracker.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            frame_suggestions = []  # 当前帧的建议
            frame_diffs = []  # 当前帧的偏差

            if results.pose_landmarks:
                detected_frames += 1
                landmarks = results.pose_landmarks.landmark

                # 2. 遍历所有关注的关节，计算角度并对比
                for joint_name, point_indices in self.joint_map.items():
                    if joint_name in target_standards:
                        # 获取三个关键点坐标
                        p1 = [landmarks[point_indices[0]].x, landmarks[point_indices[0]].y]
                        p2 = [landmarks[point_indices[1]].x, landmarks[point_indices[1]].y]
                        p3 = [landmarks[point_indices[2]].x, landmarks[point_indices[2]].y]

                        # 检查关键点可见性（z 值或 visibility）
                        if (landmarks[point_indices[0]].visibility < 0.5 or
                            landmarks[point_indices[1]].visibility < 0.5 or
                            landmarks[point_indices[2]].visibility < 0.5):
                            continue  # 跳过不可见的关节

                        # 计算当前角度
                        current_angle = self.calculate_angle(p1, p2, p3)
                        standard_angle = target_standards[joint_name]

                        # 3. 偏差判断 (设定容差，例如 ±15度)
                        diff = abs(current_angle - standard_angle)
                        threshold = 15.0
                        frame_diffs.append(diff)

                        # 4. 可视化反馈
                        # 获取关节在图像上的像素坐标用于绘图
                        cx, cy = int(p2[0] * width), int(p2[1] * height)

                        if diff > threshold:
                            color = (0, 0, 255)  # 红色代表偏差大
                            suggestion = f"调整 {joint_name.replace('_', ' ')}"
                            if suggestion not in frame_suggestions:
                                frame_suggestions.append(suggestion)
                            if suggestion not in analysis_summary:
                                analysis_summary.append(suggestion)
                        else:
                            color = (0, 255, 0)  # 绿色代表标准

                        # 在关节处画圈和写角度
                        cv2.circle(image, (cx, cy), 10, color, -1)
                        angle_text = f"{int(current_angle)}°"
                        cv2.putText(image, angle_text, (cx + 15, cy),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                # 绘制骨架
                mp_drawing.draw_landmarks(
                    image, 
                    results.pose_landmarks, 
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
                
                # 记录偏差
                if frame_diffs:
                    all_diffs.extend(frame_diffs)

            # 5. 在左上角显示建议
            y_pos = 30
            for text in frame_suggestions[:5]:  # 最多显示5条建议
                cv2.putText(image, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                y_pos += 30

            # 显示动作名称
            cv2.putText(image, f"Action: {target_pose_name}", (10, height - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            out.write(image)

        # 释放资源
        cap.release()
        out.release()
        pose_tracker.close()

        # 计算分数（基于平均偏差）
        if all_diffs:
            avg_diff = np.mean(all_diffs)
            # 分数计算：偏差越小分数越高，满分100
            # 假设平均偏差15度为60分，0偏差为100分
            score = max(0, min(100, 100 - (avg_diff / 15.0) * 40))
        else:
            score = 0  # 如果没有检测到姿态，分数为0
            if frame_count > 0:
                analysis_summary.append("未检测到人体姿态，请确保视频中包含完整的人体")

        return {
            "processed_video": output_path,
            "score": round(score, 2),
            "suggestions": list(set(analysis_summary)) if analysis_summary else ["动作标准，继续保持！"],
            "frame_count": frame_count,
            "detected_frames": detected_frames,
            "avg_diff": round(np.mean(all_diffs), 2) if all_diffs else 0
        }
