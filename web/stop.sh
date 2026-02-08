#!/usr/bin/env bash
# 停止 Web 项目：结束占用 8000（后端）与 5173（前端）的进程
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=5173

stop_port() {
  local port=$1
  local name=$2
  local pids
  pids=$(lsof -ti:$port 2>/dev/null) || true
  if [ -n "$pids" ]; then
    echo "$pids" | xargs kill -9 2>/dev/null || true
    echo "已停止 $name (端口 $port)"
  else
    echo "$name (端口 $port) 未在运行"
  fi
}

stop_port $BACKEND_PORT "后端"
stop_port $FRONTEND_PORT "前端"

# 清理 PID 与日志目录中的 pid 文件（可选，避免 start 误判）
rm -f "$SCRIPT_DIR/logs/backend.pid" "$SCRIPT_DIR/logs/frontend.pid" 2>/dev/null || true
echo "Web 项目已停止。"
