# Claude Code 用量監控

Ubuntu / Linux 桌面的小型浮動視窗，即時顯示 Claude Code 的 5 小時與 7 天用量。

## 功能

- 置頂浮動視窗，不遮擋主要工作區
- 可用滑鼠任意拖拉位置
- 5h / 7d 用量進度條，顏色隨用量變化（綠 → 橘 → 紅）
- 顯示重置時間與額外用量餘額
- 每 2 分鐘自動在背景更新
- 關閉視窗 → 縮到系統工具列圖示（程式持續執行）
- 工具列圖示左鍵單擊切換顯示 / 隱藏；右鍵有「立即更新」與「結束」

## 需求

- Python 3.10 以上
- Ubuntu 20.04+ 或任何支援 System Tray 的 Linux
- 已登入 Claude Code（token 位於 `~/.claude/.credentials.json`）

## 安裝

### 推薦：pipx（隔離乾淨，移除不殘留）

```bash
# 尚未安裝 pipx 的話
sudo apt install pipx
pipx ensurepath

# 安裝
pipx install git+https://github.com/JiHungLin/claude-code-usage-pin.git
```

安裝完成後直接執行：

```bash
claude-usage-pin
```

移除時完全乾淨：

```bash
pipx uninstall claude-usage-pin
```

---

### 備用：clone 後本機執行

```bash
git clone https://github.com/JiHungLin/claude-code-usage-pin.git
cd claude-code-usage-pin
bash install.sh           # 建 venv、裝套件、產生 .desktop 捷徑
./run.sh
```

加入開機自動啟動：

```bash
bash install.sh --autostart
```

## 加入開機自動啟動（pipx 安裝後）

```bash
# 產生 autostart 捷徑
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/claude-usage-pin.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Claude 用量監控
Exec=claude-usage-pin
Terminal=false
EOF
```

## 資料來源

Token 讀取自 `~/.claude/.credentials.json`（Claude Code 登入後自動產生）。  
用量資料來自 Anthropic OAuth API：`https://api.anthropic.com/api/oauth/usage`

## 授權

MIT
