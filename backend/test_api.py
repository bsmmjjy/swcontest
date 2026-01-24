#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 接口测试脚本
"""
import requests
import json
import sys
from pathlib import Path
import io

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 测试结果
test_results = []

def test_endpoint(name, method, url, headers=None, data=None, files=None, expected_status=200):
    """测试接口"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files)
            else:
                response = requests.post(url, headers=headers, json=data)
        else:
            print(f"[ERROR] {name}: 不支持的请求方法 {method}")
            return None
        
        status_ok = response.status_code == expected_status
        status_icon = "[PASS]" if status_ok else "[FAIL]"
        
        print(f"{status_icon} {name}")
        print(f"   状态码: {response.status_code} (期望: {expected_status})")
        
        try:
            result = response.json()
            print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}...")
        except:
            print(f"   响应: {response.text[:200]}...")
        
        test_results.append({
            "name": name,
            "status": "PASS" if status_ok else "FAIL",
            "status_code": response.status_code,
            "expected": expected_status
        })
        
        return response
    except Exception as e:
        print(f"[ERROR] {name}: 错误 - {str(e)}")
        test_results.append({
            "name": name,
            "status": "ERROR",
            "error": str(e)
        })
        return None

def main():
    print("=" * 60)
    print("开始测试 AIMovement API 接口")
    print("=" * 60)
    print()
    
    # 1. 健康检查
    print("1. 测试健康检查接口")
    test_endpoint(
        "健康检查",
        "GET",
        f"{BASE_URL}{API_PREFIX}/health"
    )
    print()
    
    # 2. 获取标准动作列表
    print("2. 测试获取标准动作列表")
    standards_response = test_endpoint(
        "获取标准动作列表",
        "GET",
        f"{BASE_URL}{API_PREFIX}/standards"
    )
    print()
    
    # 3. 获取特定动作（如果列表不为空）
    if standards_response and standards_response.status_code == 200:
        try:
            standards = standards_response.json()
            if isinstance(standards, list) and len(standards) > 0:
                action_id = standards[0].get("actionId", "")
                if action_id:
                    print("3. 测试获取特定动作")
                    test_endpoint(
                        f"获取动作: {action_id}",
                        "GET",
                        f"{BASE_URL}{API_PREFIX}/standards/{action_id}"
                    )
                    print()
        except:
            pass
    
    # 4. 用户注册
    print("4. 测试用户注册")
    register_data = {
        "username": f"testuser_{hash(str(sys.argv)) % 10000}",
        "password": "testpass123",
        "email": "test@example.com"
    }
    register_response = test_endpoint(
        "用户注册",
        "POST",
        f"{BASE_URL}{API_PREFIX}/auth/register",
        data=register_data,
        expected_status=201
    )
    print()
    
    # 5. 用户登录
    print("5. 测试用户登录")
    login_response = test_endpoint(
        "用户登录",
        "POST",
        f"{BASE_URL}{API_PREFIX}/auth/login/json",
        data={
            "username": register_data["username"],
            "password": register_data["password"]
        }
    )
    
    token = None
    if login_response and login_response.status_code == 200:
        try:
            login_data = login_response.json()
            token = login_data.get("access_token")
            if token:
                print(f"   [OK] 获取到 Token: {token[:20]}...")
        except:
            pass
    print()
    
    # 6. 获取当前用户信息
    if token:
        print("6. 测试获取当前用户信息")
        test_endpoint(
            "获取当前用户信息",
            "GET",
            f"{BASE_URL}{API_PREFIX}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print()
    
    # 7. 测试视频上传（需要 token）
    if token:
        print("7. 测试视频上传接口")
        # 创建一个测试文件（如果不存在）
        test_file = Path("test_video.txt")
        if not test_file.exists():
            test_file.write_text("This is a test file for video upload")
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": ("test_video.txt", f, "text/plain")}
                data = {
                    "action_type": "Akarna_Dhanurasana",
                    "camera_angle": "front",
                    "device": "test"
                }
                test_endpoint(
                    "视频上传",
                    "POST",
                    f"{BASE_URL}{API_PREFIX}/upload/video",
                    headers={"Authorization": f"Bearer {token}"},
                    data=data,
                    files=files
                )
        except Exception as e:
            print(f"   [SKIP] 视频上传测试跳过: {str(e)}")
        print()
    
    # 8. 测试视频推理（可选认证）
    print("8. 测试视频推理接口（无认证）")
    test_file = Path("test_video.txt")
    if test_file.exists():
        try:
            with open(test_file, "rb") as f:
                files = {"file": ("test_video.txt", f, "text/plain")}
                data = {"actionType": "Akarna_Dhanurasana"}
                test_endpoint(
                    "视频推理（无认证）",
                    "POST",
                    f"{BASE_URL}{API_PREFIX}/infer/sync",
                    data=data,
                    files=files,
                    expected_status=500  # 预期会失败，因为不是真正的视频文件
                )
        except Exception as e:
            print(f"   [SKIP] 视频推理测试跳过: {str(e)}")
    print()
    
    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    errors = sum(1 for r in test_results if r["status"] == "ERROR")
    total = len(test_results)
    
    print(f"总计: {total} 个测试")
    print(f"[PASS] 通过: {passed}")
    print(f"[FAIL] 失败: {failed}")
    print(f"[ERROR] 错误: {errors}")
    print()
    
    for result in test_results:
        status_icon = "[PASS]" if result["status"] == "PASS" else "[FAIL]" if result["status"] == "FAIL" else "[ERROR]"
        print(f"{status_icon} {result['name']}: {result['status']}")
        if result["status"] == "FAIL":
            print(f"   期望状态码: {result.get('expected')}, 实际: {result.get('status_code')}")
        if result["status"] == "ERROR":
            print(f"   错误信息: {result.get('error')}")

if __name__ == "__main__":
    main()
