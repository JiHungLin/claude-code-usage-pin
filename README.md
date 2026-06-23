# Claude Code 用量監控

Ubuntu / Linux 桌面的小型浮動視窗，即時顯示 Claude Code 的 5 小時與 7 天用量。

![視窗截圖示意](https://via.placeholder.com/270x130/1c1c20/cfcfcf?text=Claude+%E7%94%A8%E9%87%8F+%E8%A6%96%E7%AA%97)

## 功能

- 置頂浮動視窗，不遮擋主要工作區
- 可用滑鼠任意拖拉位置
- 5h / 7d 用量進度條，顏色隨用量變化（綠 → 橘 → 紅）
- 顯示重置時間與額外用量餘額
- 每 2 分鐘自動在背景更新
- 關閉視窗 → 縮到系統工具列圖示（程式持續執行）
- 工具列圖示左鍵單擊切換顯示 / 隱藏；右鍵有「立即更新」與「結束」

## 需求

| 項目 | 版本 |
|------|------|
| Python | 3.10 以上 |
| 作業系統 | Ubuntu 20.04+ / 任何支援 System Tray 的 Linux |
| Claude Code | 需已登入（token 位於 `~/.claude/.credentials.json`） |

> **注意：** 本工具使用 Claude Code 的 OAuth token，請確保已執行過 `claude` 指令完成登入。

## 安裝

```bash
git clone https://github.com/JiHungLin/claude-code-usage-pin.git
cd claude-code-usage-pin
bash install.sh
```

安裝腳本會自動：
1. 在專案目錄建立 `.venv` 虛擬環境（若已有 `.conda` 或 `.venv` 則直接使用）
2. 安裝 `PyQt5` 與 `requests`
3. 在 `~/.local/bin/claude-usage-pin` 建立捷徑
4. 產生對應本機路徑的 `.desktop` 捷徑檔案

### 加入開機自動啟動

```bash
bash install.sh --autostart
```

## 執行

```bash
# 方式一：直接執行腳本
./run.sh

# 方式二：透過 PATH 捷徑（需 ~/.local/bin 在 PATH 中）
claude-usage-pin
```

## 專案結構

```
claude-code-usage-pin/
├── claude_usage_pin.py   # 主程式（PyQt5 浮動視窗）
├── run.sh                # 啟動腳本，自動偵測 Python 環境
├── install.sh            # 一鍵安裝腳本
└── .gitignore
```

## 資料來源

Token 讀取自 `~/.claude/.credentials.json`（Claude Code 登入後自動產生）。  
用量資料來自 Anthropic OAuth API：`https://api.anthropic.com/api/oauth/usage`

## 授權

MIT
