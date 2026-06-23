#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 依序嘗試：conda 環境 → venv → 系統 python3
if   [ -x "$DIR/.conda/bin/python" ]; then PYTHON="$DIR/.conda/bin/python"
elif [ -x "$DIR/.venv/bin/python"  ]; then PYTHON="$DIR/.venv/bin/python"
else PYTHON="python3"; fi

exec "$PYTHON" "$DIR/claude_usage_pin.py" "$@"
