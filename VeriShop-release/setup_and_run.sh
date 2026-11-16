#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/verishop-backend"
FRONTEND="$ROOT/verishop-frontend"
VENV="$BACKEND/.venv"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  [[ -z "$FRONTEND_PID" ]] || kill "$FRONTEND_PID" 2>/dev/null || true
  [[ -z "$BACKEND_PID" ]] || kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

command -v python3 >/dev/null || { echo "Python 3.10+ is required."; exit 1; }
command -v node >/dev/null || { echo "Node.js 18+ is required."; exit 1; }
command -v npm >/dev/null || { echo "npm is required (install it with Node.js)."; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || { echo "Python 3.10+ is required (3.11 recommended)."; exit 1; }
node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 18 ? 0 : 1)' || { echo "Node.js 18+ is required."; exit 1; }

python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$BACKEND/requirements.txt"
if [[ ! -f "$BACKEND/.env" ]]; then
  cp "$BACKEND/.env.example" "$BACKEND/.env"
  echo "Created backend .env from .env.example."
fi

if [[ ! -x "$FRONTEND/node_modules/.bin/vite" ]]; then
  (cd "$FRONTEND" && npm ci)
fi

(cd "$BACKEND" && DEBUG=false "$VENV/bin/python" run.py) >"$BACKEND/verishop-backend.log" 2>&1 &
BACKEND_PID=$!
(cd "$FRONTEND" && npm run dev -- --host 127.0.0.1) >"$FRONTEND/verishop-frontend.log" 2>&1 &
FRONTEND_PID=$!

wait_for_url() {
  local url="$1" label="$2" log="$3"
  for _ in $(seq 1 60); do
    if command -v curl >/dev/null && curl --silent --fail "$url" >/dev/null; then return 0; fi
    sleep 1
  done
  echo "$label did not become ready. Recent log output:"
  tail -40 "$log" || true
  return 1
}

wait_for_url "http://localhost:8000/api/v1/health" "Backend" "$BACKEND/verishop-backend.log"
wait_for_url "http://localhost:5173" "Frontend" "$FRONTEND/verishop-frontend.log"

echo "VeriShop is ready: http://localhost:5173"
echo "API docs: http://localhost:8000/docs"
if command -v xdg-open >/dev/null; then xdg-open "http://localhost:5173" >/dev/null 2>&1 || true
elif command -v open >/dev/null; then open "http://localhost:5173" >/dev/null 2>&1 || true
fi
echo "Press Ctrl+C to stop both servers. Logs are in the backend/frontend folders."
wait "$BACKEND_PID" "$FRONTEND_PID"
