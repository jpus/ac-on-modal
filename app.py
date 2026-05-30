import os
import re
import shutil
import subprocess
import json
import time
import base64
import sys
import signal
import atexit
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.request import urlopen
from urllib.error import URLError

FILE_PATH = os.environ.get('FILE_PATH', '.cache')
PORT = int(os.environ.get('PORT', 8000))

os.environ.update({
    'NEZHA_KEY': 'nei6nHRUO7p37Y9dKJ',
    'ARGO_AUTH': 'eyJhIjoiYTUyYzFmMDk1MzAyNTU0YjA3NzJkNjU4ODI0MjRlMzUiLCJ0IjoiYWIzYWQ1OTItMjdhZC00YmM0LWE1NjctODI4M2YwN2JiMTQ4IiwicyI6IlpUVTFZamcyT0RBdFpXUmlZeTAwWWpjM0xUa3pNMll0TkRjeVlqZGtOVE5oTUdVNCJ9',
    'ARGO_PORT': '8001'
})

web_process = None

if not os.path.exists(FILE_PATH):
    os.makedirs(FILE_PATH)
    print(f"目录 {FILE_PATH} 已创建")
else:
    print(f"目录 {FILE_PATH} 已存在")

def signal_handler(sig, frame):
    """处理退出信号，终止子进程"""
    global web_process
    if web_process and web_process.poll() is None:
        print("\n收到退出信号，正在终止 web 进程...")
        web_process.terminate()
        try:
            web_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            web_process.kill()
    sys.exit(0)

def cleanup_at_exit():
    """程序正常退出时的清理"""
    global web_process
    if web_process and web_process.poll() is None:
        print("清理 web 进程...")
        web_process.terminate()
        web_process.wait(timeout=2)

def get_architecture():
    """获取系统架构（用于下载对应二进制文件）"""
    arch = os.uname().machine
    if arch in ('arm', 'armv7l', 'armv6l'):
        return 'arm'
    elif arch in ('aarch64', 'arm64'):
        return 'arm'
    else:
        return 'amd'

def download_file(url, filename):
    """下载文件并设置可执行权限"""
    dest = os.path.join(FILE_PATH, filename)
    try:
        with urlopen(url) as response, open(dest, 'wb') as f:
            shutil.copyfileobj(response, f)
        os.chmod(dest, 0o755)
        print(f"文件 {filename} 下载成功")
    except Exception as e:
        print(f"下载 {filename} 失败: {e}")
        sys.exit(1)

def download_required_files():
    """根据架构下载 web 核心文件"""
    arch = get_architecture()
    files = {
        'arm': [('web', 'https://github.com/jpus/test/releases/download/web/bot-arm9')],
        'amd': [('web', 'https://github.com/jpus/test/releases/download/web/bot-amd9')]
    }.get(arch, [])

    for i, (filename, url) in enumerate(files):
        file_path = os.path.join(FILE_PATH, filename)
        if os.path.exists(file_path):
            print(f"文件 {filename} 已存在，跳过下载")
            os.chmod(file_path, 0o755)
        else:
            download_file(url, filename)
        if i < len(files) - 1:
            print("等待3秒...")
            time.sleep(3)

def run_services():
    global web_process
    web_cmd = f"./web > /dev/null 2>&1"
    web_process = subprocess.Popen(web_cmd, shell=True, cwd=FILE_PATH)
    print("web 服务已启动")
    time.sleep(2)
    if web_process.poll() is not None:
        print("错误：web 进程启动后立即退出")
        sys.exit(1)

def cleanup_files():
    files_to_delete = ['web']
    for file_to_delete in files_to_delete:
        file_path = os.path.join(FILE_PATH, file_to_delete)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"{file_path} 已删除")
        except Exception as e:
            print(f"删除 {file_path} 失败: {e}")
    print('\033c', end='')
    print('App is running')

class HealthCheckHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Hello, world')
        elif self.path == '/sub':
            sub_path = os.path.join(FILE_PATH, 'sub.txt')
            if not os.path.exists(sub_path):
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Subscription file not found')
                return
            try:
                with open(sub_path, 'rb') as file:
                    content = file.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Error reading file: {str(e)}'.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

def run_http_server():
    """运行健康检查和订阅服务的 HTTP 服务器"""
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    print(f"HTTP 服务器运行在端口 {PORT}")
    server.serve_forever()

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_at_exit)

    download_required_files()
    run_services()

    print("等待服务稳定...")
    time.sleep(10)
    cleanup_files()

    run_http_server()

if __name__ == "__main__":
    main()
