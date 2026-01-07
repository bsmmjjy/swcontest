import os
import requests
import concurrent.futures
"""
@inproceedings{verma2020yoga,
  title={Yoga-82: A New Dataset for Fine-grained Classification of Human Poses},
  author={Verma, Manisha and Kumawat, Sudhakar and Nakashima, Yuta and Raman, Shanmuganathan},
  booktitle={IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW)},
  pages={4472-4479},
  year={2020}
}
"""
# ================= 配置区域 =================
# txt 文件所在的文件夹路径
LINKS_DIR = r"C:\D\oppo\Yoga-82\yoga_dataset_links"
# 图片保存的总目录
OUTPUT_DIR = r"C:\D\oppo\Yoga-82\data"

# 并发线程数 (根据你的网速调整，建议 10-50 之间)
MAX_WORKERS = 20

# 伪装请求头，防止被反爬虫拦截
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


# ===========================================

def download_image(url, save_path):
    """
    下载单个图片的函数
    """
    # 如果文件已经存在，跳过（支持断点续传）
    if os.path.exists(save_path):
        # 检查文件大小，如果文件是空的（0字节），则重新下载
        if os.path.getsize(save_path) > 0:
            print(f"[跳过] 已存在: {save_path}")
            return

    try:
        # 设置超时时间为 10 秒
        response = requests.get(url, headers=HEADERS, timeout=10, stream=True)

        # 检查状态码 (200 表示成功)
        if response.status_code == 200:
            # 确保父文件夹存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"[成功] {os.path.basename(save_path)}")
        else:
            print(f"[失败] HTTP {response.status_code}: {url}")

    except Exception as e:
        print(f"[错误] {e}: {url}")


def parse_txt_and_get_tasks(txt_file_path):
    """
    解析 txt 文件，返回 (url, save_path) 的任务列表
    """
    tasks = []
    txt_filename = os.path.basename(txt_file_path)
    # 比如 Akarna_Dhanurasana.txt -> Akarna_Dhanurasana
    # 虽然 txt 内容里包含了文件夹名，但我们以 txt 文件名为基准来处理比较稳妥

    try:
        with open(txt_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # 分割每行数据。通常是 "路径/文件名.jpg   URL"
                # 使用 split() 默认按空格或制表符分割
                parts = line.split()

                if len(parts) >= 2:
                    # parts[0] 是相对路径 (如 Akarna_Dhanurasana/680.jpg)
                    # parts[1] 是 URL
                    rel_path = parts[0]
                    url = parts[1]

                    # 组合完整的保存路径
                    full_save_path = os.path.join(OUTPUT_DIR, rel_path)

                    tasks.append((url, full_save_path))
    except Exception as e:
        print(f"读取文件出错 {txt_file_path}: {e}")

    return tasks


def main():
    # 1. 检查输入目录是否存在
    if not os.path.exists(LINKS_DIR):
        print(f"错误: 找不到路径 {LINKS_DIR}")
        return

    # 2. 获取所有的 .txt 文件
    txt_files = [f for f in os.listdir(LINKS_DIR) if f.endswith('.txt')]
    print(f"找到 {len(txt_files)} 个任务文件，准备开始处理...")

    all_download_tasks = []

    # 3. 解析所有 txt 文件，收集下载任务
    for txt_file in txt_files:
        txt_path = os.path.join(LINKS_DIR, txt_file)
        tasks = parse_txt_and_get_tasks(txt_path)
        all_download_tasks.extend(tasks)

    print(f"总计发现 {len(all_download_tasks)} 张图片需要下载。")
    print(f"正在启动 {MAX_WORKERS} 个线程进行下载 (这可能需要一些时间)...")
    print("-" * 50)

    # 4. 使用线程池并发下载
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务到线程池
        futures = [executor.submit(download_image, url, path) for url, path in all_download_tasks]

        # 等待完成
        concurrent.futures.wait(futures)

    print("-" * 50)
    print("下载任务全部结束！")


if __name__ == "__main__":
    main()