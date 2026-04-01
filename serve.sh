#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="$SCRIPT_DIR/docs"
PORT="${1:-8080}"

if [[ ! -d "$DOCS_DIR" ]]; then
  echo "docs 目录不存在：$DOCS_DIR" >&2
  exit 1
fi

if [[ ! "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
  echo "端口号必须是 1-65535 之间的整数，当前输入：$PORT" >&2
  exit 1
fi

port_is_available() {
  python3 - "$1" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.bind(("127.0.0.1", port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

REQUESTED_PORT="$PORT"
while ! port_is_available "$PORT"; do
  ((PORT += 1))
  if (( PORT > 65535 )); then
    echo "从端口 $REQUESTED_PORT 开始未找到可用端口" >&2
    exit 1
  fi
done

if (( PORT != REQUESTED_PORT )); then
  echo "端口 $REQUESTED_PORT 已被占用，改用 $PORT"
fi

echo "正在提供静态站点：$DOCS_DIR"
echo "访问地址：http://127.0.0.1:$PORT"

exec python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$DOCS_DIR"
