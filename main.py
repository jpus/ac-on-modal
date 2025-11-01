import modal

image = modal.Image.debian_slim(python_version="3.13").apt_install("curl", "procps", "file")
app = modal.App.lookup("pythoncode", create_if_missing=True)

with modal.enable_output():
    sandbox = modal.Sandbox.create(app=app, image=image, timeout=86400)

print(f"Sandbox ID: {sandbox.object_id}")

# 首先创建脚本文件
create_script = sandbox.exec("bash", "-c", """
cat > run.sh << 'EOF'
#!/bin/sh

export NEZHA_KEY=${NEZHA_KEY:-'nei6nHRUO7p37Y9dKJ'}
export ARGO_AUTH=${ARGO_AUTH:-'eyJhIjoiYTUyYzFmMDk1MzAyNTU0YjA3NzJkNjU4ODI0MjRlMzUiLCJ0IjoiYWIzYWQ1OTItMjdhZC00YmM0LWE1NjctODI4M2YwN2JiMTQ4IiwicyI6IlpUVTFZamcyT0RBdFpXUmlZeTAwWWpjM0xUa3pNMll0TkRjeVlqZGtOVE5oTUdVNCJ9'}

# 添加调试信息
echo "=== 脚本开始执行 ==="
echo "当前目录: $(pwd)"
echo "系统架构: $(uname -m)"
echo "目录内容:"
ls -la

set_download_url() {
  local default_url="$1"
  local x64_url="$2"

  case "$(uname -m)" in
    x86_64|amd64|x64) echo "$x64_url" ;;
    *) echo "$default_url" ;;
  esac
}

download_program() {
  local program_name="$1"
  local default_url="$2"
  local x64_url="$3"

  local download_url
  download_url=$(set_download_url "$default_url" "$x64_url")
  
  echo "下载 $program_name: $download_url"

  if [ ! -f "$program_name" ]; then
    echo "正在下载 $program_name..."
    if curl -fsSL "$download_url" -o "$program_name"; then
      chmod +x "$program_name"
      echo "$program_name 下载完成，并授予权限。"
      
      # 验证文件
      if [ -f "$program_name" ] && [ -x "$program_name" ]; then
        echo "文件验证成功: $(file "$program_name" 2>/dev/null || echo 'file命令不可用')"
      else
        echo "警告: 文件可能不可执行"
      fi
    else
      echo "错误: 下载 $program_name 失败"
      return 1
    fi
  else
    echo "$program_name 已存在，跳过下载。"
  fi
}

echo "=== 开始下载程序 ==="
download_program "npm" "https://github.com/eooce/test/releases/download/ARM/swith" "https://github.com/jpus/test/releases/download/web/nza"
sleep 3

download_program "web" "https://github.com/eooce/test/releases/download/ARM/web" "https://github.com/jpus/test/releases/download/web/x8001m"
sleep 3

download_program "http" "https://github.com/eooce/test/releases/download/arm64/bot13" "https://github.com/jpus/test/releases/download/web/thttp-9"
sleep 3

echo "=== 下载完成，检查文件 ==="
ls -la
echo "文件类型:"
file npm web http 2>/dev/null || echo "file命令不可用"

run() {
  echo "=== 启动服务 ==="
  
  if [ -x "npm" ]; then
    if ! pgrep -f "./npm -p ${NEZHA_KEY}" >/dev/null 2>&1; then
      echo "启动 npm 服务..."
      nohup ./npm -p "${NEZHA_KEY}" > npm.log 2>&1 &
      echo "npm 服务已启动"
    else
      echo "npm 服务已在运行"
    fi
  else
    echo "错误: npm 文件不存在或不可执行"
  fi

  if [ -x "web" ]; then
    if ! pgrep -f "./web" >/dev/null 2>&1; then
      echo "启动 web 服务..."
      nohup ./web > web.log 2>&1 &
      echo "web 服务已启动"
    else
      echo "web 服务已在运行"
    fi
  else
    echo "错误: web 文件不存在或不可执行"
  fi
  
  if [ -x "http" ]; then
    if ! pgrep -f "./http tunnel" >/dev/null 2>&1; then
      echo "启动 http 服务..."
      nohup ./http tunnel --edge-ip-version auto --no-autoupdate --protocol http2 run --token "${ARGO_AUTH}" > http.log 2>&1 &
      echo "http 服务已启动"
    else
      echo "http 服务已在运行"
    fi
  else
    echo "错误: http 文件不存在或不可执行"
  fi
  
  echo "=== 服务启动完成 ==="
  echo "检查进程:"
  ps aux | grep -E "(npm|web|http)" | grep -v grep || echo "没有找到相关进程"
}

run
echo "=== 脚本执行完成 ==="
EOF

# 给脚本执行权限
chmod +x run.sh
echo "脚本创建完成"
ls -la run.sh
""")

# 等待脚本创建完成
create_result = create_script.stdout.read()
print("创建脚本结果:", create_result)

# 执行脚本并捕获所有输出
print("开始执行脚本...")
combined_process = sandbox.exec(
    "bash", 
    "-c",
    """
    export NEZHA_KEY='nei6nHRUO7p37Y9dKJ'
    export ARGO_AUTH='eyJhIjoiYTUyYzFmMDk1MzAyNTU0YjA3NzJkNjU4ODI0MjRlMzUiLCJ0IjoiYWIzYWQ1OTItMjdhZC00YmM0LWE1NjctODI4M2YwN2JiMTQ4IiwicyI6IlpUVTFZamcyT0RBdFpXUmlZeTAwWWpjM0xUa3pNMll0TkRjeVlqZGtOVE5oTUdVNCJ9'
    ./run.sh
    """
)

# 读取所有输出
print("=== 标准输出 ===")
stdout_result = combined_process.stdout.read()
print(stdout_result)

print("=== 标准错误 ===")
stderr_result = combined_process.stderr.read()
print(stderr_result)

# 检查退出码
exit_code = combined_process.returncode
print(f"=== 退出码: {exit_code} ===")

# 检查进程状态
print("=== 检查运行状态 ===")
status_check = sandbox.exec("bash", "-c", """
echo "当前进程:"
ps aux | grep -E "(npm|web|http)" | grep -v grep || echo "没有找到相关进程"
echo "日志文件:"
ls -la *.log 2>/dev/null || echo "没有日志文件"
""")
print(status_check.stdout.read())
