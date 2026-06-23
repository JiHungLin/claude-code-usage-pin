#!/usr/bin/env python3
"""Claude Code 用量浮動視窗 — 置頂、可拖拉、關閉後收至工具列。"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from PyQt5.QtCore import QPoint, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QLabel,
    QMenu,
    QProgressBar,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
TOKEN_MIN_TTL_MS = 5 * 60 * 1000
REFRESH_INTERVAL_MS = 120_000  # 2 分鐘


# ── 資料抓取 ─────────────────────────────────────────────────────────────────

def _load_token() -> str | None:
    try:
        creds = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
        oauth = creds.get("claudeAiOauth", {})
        token = oauth.get("accessToken")
        expires_at_ms = oauth.get("expiresAt", 0)
        if not token:
            return None
        if expires_at_ms and (expires_at_ms - time.time() * 1000) < TOKEN_MIN_TTL_MS:
            return None
        return token
    except Exception:
        return None


def _fetch_usage() -> dict | None:
    token = _load_token()
    if not token:
        return None
    try:
        resp = requests.get(
            USAGE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20",
            },
            timeout=10.0,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


class FetchThread(QThread):
    """在背景執行緒抓取資料，避免 UI 卡住。"""
    result = pyqtSignal(object)

    def run(self):
        self.result.emit(_fetch_usage())


# ── 工具列圖示 ────────────────────────────────────────────────────────────────

def _make_tray_icon(pct: float = 0.0) -> QIcon:
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)

    if pct >= 80:
        color = QColor("#f44336")
    elif pct >= 60:
        color = QColor("#FF9800")
    else:
        color = QColor("#4CAF50")

    p.setBrush(color)
    p.setPen(Qt.NoPen)
    p.drawEllipse(4, 4, size - 8, size - 8)

    p.setPen(QPen(Qt.white))
    font = QFont("Sans Serif", 15, QFont.Bold)
    p.setFont(font)
    p.drawText(0, 0, size, size, Qt.AlignCenter, f"{int(pct)}%")
    p.end()
    return QIcon(pixmap)


# ── 主視窗 ────────────────────────────────────────────────────────────────────

_BAR_STYLE = """
QProgressBar {{
    background-color: rgba(60,60,60,200);
    border-radius: 6px;
    border: none;
    color: white;
    font-size: 10px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {color};
    border-radius: 6px;
}}
"""

_WIN_STYLE = """
QWidget#root {
    background-color: rgba(28, 28, 32, 215);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,30);
}
"""


class FloatingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_pos = QPoint()
        self._fetch_thread: FetchThread | None = None
        self._setup_window()
        self._setup_ui()
        self._setup_tray()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._start_fetch)
        self._timer.start(REFRESH_INTERVAL_MS)
        self._start_fetch()

    # ── 視窗設定 ──────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setObjectName("root")
        self.setWindowTitle("Claude 用量")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(270)
        self.setStyleSheet(_WIN_STYLE)

    # ── UI 元件 ───────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        title = QLabel("◉  Claude 用量")
        title.setStyleSheet("color:#cfcfcf; font-size:13px; font-weight:bold;")
        layout.addWidget(title)

        # 5h
        layout.addSpacing(4)
        self._lbl_5h = QLabel("5 小時（Current Session）")
        self._lbl_5h.setStyleSheet("color:#999; font-size:10px;")
        layout.addWidget(self._lbl_5h)

        self._bar_5h = QProgressBar()
        self._bar_5h.setFixedHeight(16)
        self._bar_5h.setRange(0, 100)
        self._set_bar(self._bar_5h, "#4CAF50")
        layout.addWidget(self._bar_5h)

        self._lbl_reset = QLabel("")
        self._lbl_reset.setStyleSheet("color:#666; font-size:10px;")
        layout.addWidget(self._lbl_reset)

        # 7d
        layout.addSpacing(4)
        self._lbl_7d = QLabel("7 天")
        self._lbl_7d.setStyleSheet("color:#999; font-size:10px;")
        layout.addWidget(self._lbl_7d)

        self._bar_7d = QProgressBar()
        self._bar_7d.setFixedHeight(16)
        self._bar_7d.setRange(0, 100)
        self._set_bar(self._bar_7d, "#2196F3")
        layout.addWidget(self._bar_7d)

        # 額外用量
        layout.addSpacing(4)
        self._lbl_extra = QLabel("")
        self._lbl_extra.setStyleSheet("color:#aaa; font-size:10px;")
        self._lbl_extra.setWordWrap(True)
        self._lbl_extra.hide()
        layout.addWidget(self._lbl_extra)

        # 狀態列
        layout.addSpacing(2)
        self._lbl_status = QLabel("載入中…")
        self._lbl_status.setStyleSheet("color:#555; font-size:10px;")
        layout.addWidget(self._lbl_status)

    @staticmethod
    def _set_bar(bar: QProgressBar, color: str):
        bar.setStyleSheet(_BAR_STYLE.format(color=color))

    # ── 工具列 ────────────────────────────────────────────────────────────────

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(_make_tray_icon(), self)
        self._tray.setToolTip("Claude 用量監控")

        menu = QMenu()

        act_toggle = QAction("顯示 / 隱藏視窗", self)
        act_toggle.triggered.connect(self._toggle)
        menu.addAction(act_toggle)

        act_refresh = QAction("立即更新", self)
        act_refresh.triggered.connect(self._start_fetch)
        menu.addAction(act_refresh)

        menu.addSeparator()

        act_quit = QAction("結束", self)
        act_quit.triggered.connect(QApplication.quit)
        menu.addAction(act_quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_click)
        self._tray.show()

    def _toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _on_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # 左鍵單擊
            self._toggle()

    # ── 資料更新 ──────────────────────────────────────────────────────────────

    def _start_fetch(self):
        if self._fetch_thread and self._fetch_thread.isRunning():
            return
        self._lbl_status.setText("更新中…")
        self._fetch_thread = FetchThread()
        self._fetch_thread.result.connect(self._on_data)
        self._fetch_thread.start()

    def _on_data(self, data: dict | None):
        if data is None:
            self._lbl_status.setText("無資料（token 可能已過期）")
            self._tray.setIcon(_make_tray_icon(0))
            self._tray.setToolTip("Claude 用量監控 — 無法取得資料")
            return

        five_h = data.get("five_hour", {})
        seven_d = data.get("seven_day", {})
        extra   = data.get("extra_usage", {})

        five_pct  = float(five_h.get("utilization") or 0)
        seven_pct = float(seven_d.get("utilization") or 0)

        # 進度條
        self._bar_5h.setValue(int(five_pct))
        self._bar_5h.setFormat(f"{five_pct:.0f}%")
        if five_pct >= 80:
            self._set_bar(self._bar_5h, "#f44336")
        elif five_pct >= 60:
            self._set_bar(self._bar_5h, "#FF9800")
        else:
            self._set_bar(self._bar_5h, "#4CAF50")

        self._bar_7d.setValue(int(seven_pct))
        self._bar_7d.setFormat(f"{seven_pct:.0f}%")

        # 重置時間
        resets_str = five_h.get("resets_at") or seven_d.get("resets_at")
        if resets_str:
            try:
                resets_at = datetime.fromisoformat(resets_str).astimezone()
                self._lbl_reset.setText(f"重置：{resets_at.strftime('%m/%d %H:%M')}")
            except Exception:
                self._lbl_reset.setText("")
        else:
            self._lbl_reset.setText("")

        # 額外用量
        extra_used  = extra.get("used_credits")
        extra_limit = extra.get("monthly_limit")
        if extra_used is not None and extra_limit:
            used    = extra_used / 100
            limit   = extra_limit / 100
            balance = limit - used
            pct     = used / limit * 100 if limit else 0
            if balance > 0:
                self._lbl_extra.setText(f"額外：${used:.2f} / ${limit:.0f}  ({pct:.0f}%)  餘 ${balance:.2f}")
            else:
                self._lbl_extra.setText("額外用量：已耗盡")
            self._lbl_extra.show()
        else:
            self._lbl_extra.hide()

        # 狀態列
        now = datetime.now().astimezone()
        nxt = now + timedelta(seconds=REFRESH_INTERVAL_MS // 1000)
        self._lbl_status.setText(f"更新 {now.strftime('%H:%M')} ・ 下次 {nxt.strftime('%H:%M')}")

        # 工具列圖示
        self._tray.setIcon(_make_tray_icon(five_pct))
        self._tray.setToolTip(
            f"Claude 用量\n5h: {five_pct:.0f}%   7d: {seven_pct:.0f}%"
        )

        self.adjustSize()

    # ── 視窗事件 ──────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        """關閉時改為隱藏，程式繼續在工具列執行。"""
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "Claude 用量監控",
            "已最小化至工具列，點擊圖示可重新開啟。",
            QSystemTrayIcon.Information,
            2000,
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def paintEvent(self, event):
        # 讓 WA_TranslucentBackground + border-radius 正確渲染
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(28, 28, 32, 215))
        p.setPen(QPen(QColor(255, 255, 255, 30), 1))
        p.drawRoundedRect(self.rect(), 10, 10)
        p.end()


# ── 進入點 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("錯誤：系統不支援工具列圖示（System Tray）", file=sys.stderr)
        sys.exit(1)

    win = FloatingWindow()
    win.show()
    sys.exit(app.exec_())
