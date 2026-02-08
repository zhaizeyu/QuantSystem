#!/usr/bin/env bash
# 启动 Web 项目：后端 FastAPI (8000) + 前端 Vite (5173)
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

BACKEND_PORT=8000
FRONTEND_PORT=5173

# 若端口已被占用则先停掉
if lsof -ti:$BACKEND_PORT >/dev/null 2>&1 || lsof -ti:$FRONTEND_PORT >/dev/null 2>&1; then
  echo "端口 $BACKEND_PORT 或 $FRONTEND_PORT 已被占用，先执行 stop 再启动。"
  "$SCRIPT_DIR/stop.sh" 2>/dev/null || true
  sleep 2
fi

echo "启动后端 (uvicorn :$BACKEND_PORT)..."
nohup uvicorn web.backend.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT >> "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$LOG_DIR/backend.pid"

echo "启动前端 (Vite :$FRONTEND_PORT)..."
(cd web/frontend && nohup npm run dev >> "$LOG_DIR/frontend.log" 2>&1 &)
sleep 3
if lsof -ti:$FRONTEND_PORT >/dev/null 2>&1; then
  lsof -ti:$FRONTEND_PORT > "$LOG_DIR/frontend.pid"
fi

sleep 1
if kill -0 $BACKEND_PID 2>/dev/null; then
  echo "后端已启动 PID=$BACKEND_PID, http://localhost:$BACKEND_PORT"
else
  echo "后端启动异常，请查看 $LOG_DIR/backend.log"
fi
if lsof -ti:$FRONTEND_PORT >/dev/null 2>&1; then
  echo "前端已启动, http://localhost:$FRONTEND_PORT"
else
  echo "前端启动中或异常，请查看 $LOG_DIR/frontend.log"
fi
echo "Web 项目已启动。停止请执行: ./web/stop.sh"
