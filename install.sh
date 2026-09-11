#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but not installed."
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required but not installed."
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
cd backend
python -m pip install -r requirements.txt
cd ../frontend
npm install

echo "AegisPTR installation complete."
echo "Run ./start.sh to launch the application."
