#!/usr/bin/env bash
# 安裝 Claude Code 用量監控
# 用法：bash install.sh [--autostart]
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOSTART=false
[[ "${1:-}" == "--autostart" ]] && AUTOSTART=true

echo "=== Claude 用量監控 — 安裝 ==="

# ── 1. 找或建立 Python 環境 ───────────────────────────────────────────────────
if   [ -x "$DIR/.conda/bin/python" ]; then
    PYTHON="$DIR/.conda/bin/python"
    echo "✓ 使用現有 conda 環境"
elif [ -x "$DIR/.venv/bin/python" ]; then
    PYTHON="$DIR/.venv/bin/python"
    echo "✓ 使用現有 venv"
else
    echo "→ 建立 .venv 虛擬環境…"
    python3 -m venv "$DIR/.venv"
    PYTHON="$DIR/.venv/bin/python"
fi

# ── 2. 安裝相依套件 ───────────────────────────────────────────────────────────
echo "→ 安裝相依套件（PyQt5、requests）…"
"$PYTHON" -m pip install --quiet --upgrade pip
"$PYTHON" -m pip install --quiet PyQt5 requests

# ── 3. 確認 claude credentials 存在 ──────────────────────────────────────────
CREDS="$HOME/.claude/.credentials.json"
if [ ! -f "$CREDS" ]; then
    echo "⚠  找不到 $CREDS"
    echo "   請先登入 Claude Code（執行一次 claude 指令），token 才能正常讀取。"
fi

# ── 4. 產生 .desktop 捷徑（使用當前絕對路徑）────────────────────────────────
DESKTOP_FILE="$DIR/claude-usage-pin.desktop"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Claude 用量監控
Comment=顯示 Claude Code 用量的浮動視窗
Exec=$DIR/run.sh
Icon=utilities-system-monitor
Terminal=false
Categories=Utility;
StartupNotify=false
EOF
echo "✓ 產生 $DESKTOP_FILE"

# ── 5. 安裝到 ~/.local/bin（讓任意終端可執行）────────────────────────────────
mkdir -p "$HOME/.local/bin"
ln -sf "$DIR/run.sh" "$HOME/.local/bin/claude-usage-pin"
echo "✓ 建立捷徑 ~/.local/bin/claude-usage-pin"

# ── 6. 選擇性：加入開機自動啟動 ──────────────────────────────────────────────
if $AUTOSTART; then
    mkdir -p "$HOME/.config/autostart"
    cp "$DESKTOP_FILE" "$HOME/.config/autostart/claude-usage-pin.desktop"
    echo "✓ 已加入開機自動啟動"
fi

echo ""
echo "=== 安裝完成 ==="
echo "執行方式："
echo "  ./run.sh                    # 直接執行"
echo "  claude-usage-pin            # 任意終端（需 ~/.local/bin 在 PATH）"
if ! $AUTOSTART; then
echo ""
echo "加入開機自動啟動："
echo "  bash install.sh --autostart"
fi
