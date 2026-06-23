#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/.conda/bin/python" "$DIR/claude_usage_pin.py" "$@"
