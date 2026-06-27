from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget,
    QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel,
    QSizePolicy, QMessageBox, QDialog, QFormLayout, QComboBox,
    QDialogButtonBox, QGraphicsDropShadowEffect, QScrollArea, QSpacerItem,
    QGridLayout
)
from PyQt5.QtGui import (
    QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap,
    QTextBlockFormat, QLinearGradient, QBrush, QPen, QPalette, QFontDatabase,
    QRadialGradient
)
from PyQt5.QtCore import (
    Qt, QSize, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect,
    QThread, QDateTime
)
from dotenv import dotenv_values, set_key
import sys
import os
import json
import time
import datetime
import math

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ── Environment ──────────────────────────────────────────────────────────────────
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname", "Jarvis")
Username = env_vars.get("Username", "User")
old_chat_message = ""

current_dir = os.getcwd()
TempDirPath  = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

# ── Palette ───────────────────────────────────────────────────────────────────────
C_BG        = "#090f16"   # Very deep navy-black (main background)
C_PANEL     = "#0d1a24"   # Slightly lighter navy (card/panel background)
C_SURFACE   = "#0f2030"   # Input/track background
C_BORDER    = "#0e2233"   # Subtle card border
C_ACCENT    = "#00c8e0"   # Bright cyan-teal (logo, titles, primary highlights)
C_ACCENT2   = "#00e5b0"   # Bright teal-green (secondary highlights, online dot)
C_TEXT      = "#d4f0f8"   # Near-white with slight cyan tint (primary text)
C_SUBTEXT   = "#4a7a8a"   # Muted teal-gray (secondary text, labels)
C_STOP      = "#ff3355"   # Red (stop/error, unchanged)
C_SUCCESS   = "#00e5b0"   # Teal-green (success/active states)
C_WARNING   = "#ffaa00"   # Amber (warning, unchanged)

# ── Weather config ───────────────────────────────────────────────────────────────
# Uses OpenWeatherMap's free Current Weather API.
# Add these two lines to your .env to enable live weather:
#   WeatherAPIKey=your_openweathermap_api_key
#   WeatherCity=Lahore
WeatherAPIKey = env_vars.get("WeatherAPIKey", "")
WeatherCity = env_vars.get("WeatherCity", "Lahore")

# ── Session stats (uptime / sessions / commands) ────────────────────────────────
StatsPath = os.path.join(current_dir, "Data", "Stats.json")
_session_start_ts = time.time()

def _load_stats():
    try:
        with open(StatsPath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": 0, "commands": 0}

def _save_stats(stats):
    try:
        os.makedirs(os.path.dirname(StatsPath), exist_ok=True)
        with open(StatsPath, "w", encoding="utf-8") as f:
            json.dump(stats, f)
    except Exception:
        pass

def RegisterNewSession():
    stats = _load_stats()
    stats["sessions"] = stats.get("sessions", 0) + 1
    _save_stats(stats)
    return stats

def IncrementCommandCount():
    stats = _load_stats()
    stats["commands"] = stats.get("commands", 0) + 1
    _save_stats(stats)
    return stats

def GetStats():
    return _load_stats()

def GetUptimeString():
    elapsed = int(time.time() - _session_start_ts)
    h, rem = divmod(elapsed, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ── Helpers ───────────────────────────────────────────────────────────────────────
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    return '\n'.join(line.strip() for line in lines if line.strip())

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ['how','what','who','where','when','why','which','whom','can you',"what's","where's","how's"]
    if any(word + " " in new_query for word in question_words):
        new_query = new_query[:-1] + "?" if query_words[-1][-1] in ['.','?','!'] else new_query + "?"
    else:
        new_query = new_query[:-1] + '.' if query_words[-1][-1] in ['.','?','!'] else new_query + '.'
    return new_query.capitalize()

def TempDirectoryPath(Filename):
    return rf'{TempDirPath}\{Filename}'

def GraphicsDirectoryPath(Filename):
    return rf'{GraphicsDirPath}\{Filename}'

def SetMicrophoneStatus(Command):
    with open(TempDirectoryPath('Mic.data'), 'w', encoding='utf-8') as f:
        f.write(Command)

def GetMicrophoneStatus():
    try:
        with open(TempDirectoryPath('Mic.data'), 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "False"

def SetAsssistantStatus(Status):
    with open(TempDirectoryPath('Status.data'), 'w', encoding='utf-8') as f:
        f.write(Status)

def GetAssistantStatus():
    try:
        with open(TempDirectoryPath('Status.data'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Available..."

def ShowTextToScreen(Text):
    with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as f:
        f.write(Text)

def SetStopFlag(value: bool):
    with open(TempDirectoryPath('Stop.data'), 'w', encoding='utf-8') as f:
        f.write("True" if value else "False")

def GetStopFlag():
    try:
        with open(TempDirectoryPath('Stop.data'), 'r', encoding='utf-8') as f:
            return f.read().strip() == "True"
    except:
        return False

def MicButtonInitiated():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def DeleteChatHistory():
    try:
        data_path = os.path.join(current_dir, 'Data', 'ChatLog.json')
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as f:
            f.write(f"{Username}: Hello {Assistantname}, How are you?\n{Assistantname}: Welcome {Username}. I am doing well. How may I help you?")
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as f:
            f.write("")
        return True
    except Exception as e:
        print(f"Error deleting history: {e}")
        return False


# ── Styled Components ─────────────────────────────────────────────────────────────

class GlowButton(QPushButton):
    """A button with hover glow effect."""
    def __init__(self, text="", icon_path=None, color=C_ACCENT, parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(18, 18))
        self._apply_style(False)

    def _apply_style(self, hovered):
        alpha = "33" if not hovered else "55"
        border = self.color if hovered else C_BORDER
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color}{alpha};
                color: {C_TEXT};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
        """)

    def enterEvent(self, e):
        self._apply_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._apply_style(False)
        super().leaveEvent(e)


class IconButton(QPushButton):
    """Flat icon-only button for the title bar."""
    def __init__(self, icon_path=None, size=32, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(size - 10, size - 10))
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: {size//2}px;
            }}
            QPushButton:hover {{
                background-color: {C_BORDER};
            }}
        """)


class StatusPill(QLabel):
    """Animated status indicator pill."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setAlignment(Qt.AlignCenter)
        self._dot_count = 0
        self._base_text = ""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(500)
        self.setText("Available")
        self._update_style(C_SUCCESS)

    def _animate(self):
        if any(w in self._base_text for w in ["Listening", "Thinking", "Searching", "Answering"]):
            self._dot_count = (self._dot_count + 1) % 4
            dots = "." * self._dot_count
            super().setText(f"  ● {self._base_text.rstrip('.')}{dots}  ")

    def setText(self, text):
        self._base_text = text.rstrip('.')
        super().setText(f"  ● {self._base_text}  ")
        if "Listening" in text:
            self._update_style(C_ACCENT)
        elif "Thinking" in text or "Searching" in text:
            self._update_style(C_WARNING)
        elif "Answering" in text:
            self._update_style(C_ACCENT2)
        elif "Stop" in text or "Error" in text:
            self._update_style(C_STOP)
        else:
            self._update_style(C_SUCCESS)

    def _update_style(self, color):
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}22;
                color: {color};
                border: 1px solid {color}55;
                border-radius: 14px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.5px;
                padding: 0 6px;
                min-width: 140px;
            }}
        """)


# ── Weather (background thread, never blocks the GUI) ──────────────────────────────

class WeatherFetcher(QThread):
    weatherReady = pyqtSignal(dict)
    weatherFailed = pyqtSignal(str)

    def __init__(self, city=None, parent=None):
        super().__init__(parent)
        self.city = city or WeatherCity

    def run(self):
        if not WeatherAPIKey:
            self.weatherFailed.emit("no_key")
            return
        if not REQUESTS_AVAILABLE:
            self.weatherFailed.emit("no_requests")
            return
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": self.city, "appid": WeatherAPIKey, "units": "metric"}
            resp = requests.get(url, params=params, timeout=6)
            data = resp.json()
            if resp.status_code != 200:
                self.weatherFailed.emit(data.get("message", "error"))
                return
            self.weatherReady.emit({
                "temp": round(data["main"]["temp"], 1),
                "feels_like": round(data["main"]["feels_like"], 1),
                "humidity": data["main"]["humidity"],
                "wind": round(data["wind"]["speed"], 1),
                "condition": data["weather"][0]["main"],
                "city": data.get("name", self.city),
            })
        except Exception as e:
            self.weatherFailed.emit(str(e))


WEATHER_ICONS = {
    "Clear": "☀", "Clouds": "☁", "Rain": "🌧", "Drizzle": "🌦",
    "Thunderstorm": "⛈", "Snow": "❄", "Mist": "🌫", "Fog": "🌫", "Haze": "🌫",
}


# ── Small reusable sidebar building blocks ──────────────────────────────────────

class SidebarCard(QFrame):
    """A glass-panel card used in the left sidebar."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        # IMPORTANT: a bare `QFrame { ... }` rule cascades to every nested
        # QFrame in this widget's subtree (e.g. MetricBar's track/fill
        # bars), not just this widget -- that previously turned thin 6px
        # progress bars into bordered, rounded mini-panels and squashed
        # their labels. Scoping by objectName avoids that entirely.
        self.setObjectName("sidebarCard")
        self.setStyleSheet(f"""
            QFrame#sidebarCard {{
                background-color: {C_PANEL};
                border: 1px solid {C_BORDER};
                border-radius: 12px;
            }}
        """)
        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(14, 12, 14, 14)
        self.outer.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(6)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {C_ACCENT}; font-size: 9px; background: transparent; border: none;")
        head.addWidget(dot)
        label = QLabel(title.upper())
        label.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; background: transparent; border: none;")
        head.addWidget(label)
        head.addStretch()
        self.outer.addLayout(head)

    def body(self):
        return self.outer


class MetricBar(QWidget):
    """A labeled usage bar, e.g. CPU 47%."""
    def __init__(self, label, color=C_ACCENT, parent=None):
        super().__init__(parent)
        self.color = color
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        row = QHBoxLayout()
        self.name_lbl = QLabel(label)
        self.name_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        row.addWidget(self.name_lbl)
        row.addStretch()
        self.value_lbl = QLabel("--")
        self.value_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        row.addWidget(self.value_lbl)
        layout.addLayout(row)

        self.track = QFrame()
        self.track.setFixedHeight(6)
        self.track.setStyleSheet(f"background-color: {C_SURFACE}; border-radius: 3px;")
        track_layout = QHBoxLayout(self.track)
        track_layout.setContentsMargins(0, 0, 0, 0)
        self.fill = QFrame()
        self.fill.setFixedHeight(6)
        self.fill.setStyleSheet(f"background-color: {self.color}; border-radius: 3px;")
        track_layout.addWidget(self.fill, alignment=Qt.AlignLeft)
        layout.addWidget(self.track)

        self._pct = 0

    def setValue(self, pct, suffix="%"):
        pct = max(0, min(100, pct))
        self._pct = pct
        self.value_lbl.setText(f"{pct:.0f}{suffix}")
        total_w = max(self.track.width(), 1)
        self.fill.setFixedWidth(int(total_w * pct / 100))
        color = self.color
        if pct > 85:
            color = C_STOP
        elif pct > 65:
            color = C_WARNING
        self.fill.setStyleSheet(f"background-color: {color}; border-radius: 3px;")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.setValue(self._pct)


class SystemStatsCard(SidebarCard):
    # Rough ceiling used to translate network throughput into a 0-100% bar.
    # Real network "usage" has no natural percentage scale, so this maps
    # combined send+receive speed against a typical home-broadband ceiling.
    NETWORK_CEILING_MBPS = 50

    def __init__(self, parent=None):
        super().__init__("System Stats", parent)
        self.cpu_bar = MetricBar("CPU USAGE", C_ACCENT)
        self.ram_bar = MetricBar("RAM USAGE", C_ACCENT2)
        self.disk_bar = MetricBar("DISK USAGE", C_SUCCESS)
        self.network_bar = MetricBar("NETWORK", C_WARNING)
        self.body().addWidget(self.cpu_bar)
        self.body().addWidget(self.ram_bar)
        self.body().addWidget(self.disk_bar)
        self.body().addWidget(self.network_bar)

        self._last_net = None
        self._last_net_time = None
        if PSUTIL_AVAILABLE:
            try:
                self._last_net = psutil.net_io_counters()
                self._last_net_time = time.time()
            except Exception:
                pass

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)
        self.refresh()

    def refresh(self):
        if not PSUTIL_AVAILABLE:
            for bar in (self.cpu_bar, self.ram_bar, self.disk_bar, self.network_bar):
                bar.value_lbl.setText("N/A")
            return
        try:
            self.cpu_bar.setValue(psutil.cpu_percent(interval=None))
            self.ram_bar.setValue(psutil.virtual_memory().percent)
            self.disk_bar.setValue(psutil.disk_usage(os.path.abspath(os.sep)).percent)
            self._refresh_network()
        except Exception:
            pass

    def _refresh_network(self):
        now = time.time()
        counters = psutil.net_io_counters()
        if self._last_net is None or self._last_net_time is None:
            self._last_net, self._last_net_time = counters, now
            return
        elapsed = max(now - self._last_net_time, 0.001)
        sent = counters.bytes_sent - self._last_net.bytes_sent
        recv = counters.bytes_recv - self._last_net.bytes_recv
        mbps = ((sent + recv) * 8 / 1_000_000) / elapsed
        pct = min(100, (mbps / self.NETWORK_CEILING_MBPS) * 100)
        self.network_bar.setValue(pct)
        self._last_net, self._last_net_time = counters, now


class WeatherCard(SidebarCard):
    def __init__(self, parent=None):
        super().__init__("Weather", parent)
        self._current_city = WeatherCity

        # City search row
        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Enter city name...")
        self.city_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C_SURFACE}; color: {C_TEXT};
                border: 1px solid {C_BORDER}; border-radius: 8px;
                padding: 5px 10px; font-size: 11px;
            }}
            QLineEdit:focus {{ border-color: {C_ACCENT}; }}
        """)
        self.city_input.returnPressed.connect(self._searchCity)
        search_row.addWidget(self.city_input, stretch=1)

        search_btn = QPushButton("🔍")
        search_btn.setFixedSize(28, 28)
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_SURFACE}; border: 1px solid {C_BORDER};
                border-radius: 8px; font-size: 11px;
            }}
            QPushButton:hover {{ border-color: {C_ACCENT}; }}
        """)
        search_btn.clicked.connect(self._searchCity)
        search_row.addWidget(search_btn)
        self.body().addLayout(search_row)

        row = QHBoxLayout()
        self.icon_lbl = QLabel("⛅")
        self.icon_lbl.setStyleSheet("font-size: 30px; background: transparent; border: none;")
        row.addWidget(self.icon_lbl)

        temp_col = QVBoxLayout()
        temp_col.setSpacing(0)
        self.temp_lbl = QLabel("--°C")
        self.temp_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 22px; font-weight: 700; background: transparent; border: none;")
        temp_col.addWidget(self.temp_lbl)
        self.city_lbl = QLabel(WeatherCity)
        self.city_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 11px; background: transparent; border: none;")
        temp_col.addWidget(self.city_lbl)
        row.addLayout(temp_col)
        row.addStretch()
        self.body().addLayout(row)

        grid = QGridLayout()
        grid.setSpacing(4)

        def stat_label():
            l = QLabel("--")
            l.setStyleSheet(f"color: {C_TEXT}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
            return l

        def cap_label(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 10px; background: transparent; border: none;")
            return l

        self.humidity_lbl = stat_label()
        self.wind_lbl = stat_label()
        self.feels_lbl = stat_label()

        grid.addWidget(cap_label("HUMIDITY"), 0, 0)
        grid.addWidget(cap_label("WIND"), 0, 1)
        grid.addWidget(cap_label("FEELS LIKE"), 0, 2)
        grid.addWidget(self.humidity_lbl, 1, 0)
        grid.addWidget(self.wind_lbl, 1, 1)
        grid.addWidget(self.feels_lbl, 1, 2)
        self.body().addLayout(grid)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 10px; background: transparent; border: none;")
        self.status_lbl.setWordWrap(True)
        self.body().addWidget(self.status_lbl)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10 * 60 * 1000)  # refresh every 10 minutes
        self.refresh()

    def refresh(self):
        self.fetcher = WeatherFetcher(city=self._current_city)
        self.fetcher.weatherReady.connect(self._onReady)
        self.fetcher.weatherFailed.connect(self._onFailed)
        self.fetcher.start()

    def _searchCity(self):
        typed = self.city_input.text().strip()
        if not typed:
            return
        self._current_city = typed
        self.city_input.clear()
        self.status_lbl.setText("Looking up weather...")
        self.refresh()

    def _onReady(self, data):
        self.icon_lbl.setText(WEATHER_ICONS.get(data["condition"], "⛅"))
        self.temp_lbl.setText(f"{data['temp']}°C")
        self.city_lbl.setText(data["city"])
        self._current_city = data["city"]
        self.humidity_lbl.setText(f"{data['humidity']}%")
        self.wind_lbl.setText(f"{data['wind']} m/s")
        self.feels_lbl.setText(f"{data['feels_like']}°C")
        self.status_lbl.setText("")

    def _onFailed(self, reason):
        if reason == "no_key":
            self.status_lbl.setText("Add WeatherAPIKey to .env to enable live weather.")
        elif "city not found" in (reason or "").lower():
            self.status_lbl.setText(f'City "{self._current_city}" not found.')
        else:
            self.status_lbl.setText("Weather unavailable.")


class CameraCard(SidebarCard):
    """Visual placeholder only -- no webcam is actually opened."""
    def __init__(self, parent=None):
        super().__init__("Camera", parent)

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {C_STOP}; font-size: 9px; background: transparent; border: none;")
        status_row.addWidget(dot)
        status_lbl = QLabel("Camera OFF")
        status_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        status_row.addWidget(status_lbl)
        status_row.addStretch()
        self.body().addLayout(status_row)

        preview = QFrame()
        preview.setFixedHeight(90)
        preview.setStyleSheet(f"background-color: {C_SURFACE}; border: 1px dashed {C_BORDER}; border-radius: 8px;")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setSpacing(4)
        icon_lbl = QLabel("📷")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 22px; color: {C_SUBTEXT}; background: transparent; border: none;")
        preview_layout.addWidget(icon_lbl)
        no_signal_lbl = QLabel("No Signal")
        no_signal_lbl.setAlignment(Qt.AlignCenter)
        no_signal_lbl.setStyleSheet(f"font-size: 10px; color: {C_SUBTEXT}; background: transparent; border: none;")
        preview_layout.addWidget(no_signal_lbl)
        self.body().addWidget(preview)


class UptimeCard(SidebarCard):
    def __init__(self, parent=None):
        super().__init__("System Uptime", parent)

        self.uptime_lbl = QLabel("00:00:00")
        self.uptime_lbl.setStyleSheet(f"color: {C_ACCENT}; font-size: 20px; font-weight: 700; background: transparent; border: none; font-family: Consolas, monospace;")
        self.body().addWidget(self.uptime_lbl)

        running_lbl = QLabel("SYSTEM RUNNING TIME")
        running_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 9px; letter-spacing: 1px; background: transparent; border: none;")
        self.body().addWidget(running_lbl)

        grid = QGridLayout()
        grid.setSpacing(2)

        def cap_label(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 9px; letter-spacing: 1px; background: transparent; border: none;")
            return l

        self.sessions_lbl = QLabel("0")
        self.sessions_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 15px; font-weight: 700; background: transparent; border: none;")
        self.commands_lbl = QLabel("0")
        self.commands_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 15px; font-weight: 700; background: transparent; border: none;")

        grid.addWidget(cap_label("SESSIONS"), 0, 0)
        grid.addWidget(cap_label("COMMANDS"), 0, 1)
        grid.addWidget(self.sessions_lbl, 1, 0)
        grid.addWidget(self.commands_lbl, 1, 1)
        self.body().addLayout(grid)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

    def refresh(self):
        self.uptime_lbl.setText(GetUptimeString())
        stats = GetStats()
        self.sessions_lbl.setText(str(stats.get("sessions", 0)))
        self.commands_lbl.setText(str(stats.get("commands", 0)))


# ── Settings Dialog ───────────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setFixedSize(480, 480)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {C_PANEL}; border: 1px solid {C_BORDER}; border-radius: 16px; }}
            QLabel {{ color: {C_TEXT}; font-size: 13px; }}
            QLineEdit, QComboBox {{
                background-color: {C_SURFACE}; color: {C_TEXT};
                border: 1px solid {C_BORDER}; border-radius: 8px;
                padding: 8px 12px; font-size: 13px; min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus {{ border-color: {C_ACCENT}; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ color: {C_TEXT}; }}
            QComboBox QAbstractItemView {{
                background-color: {C_SURFACE}; color: {C_TEXT};
                border: 1px solid {C_BORDER}; selection-background-color: {C_ACCENT}33;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(16)

        # Title
        title = QLabel("⚙  Settings")
        title.setStyleSheet(f"color: {C_TEXT}; font-size: 18px; font-weight: 700;")
        main_layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {C_BORDER}; max-height: 1px;")
        main_layout.addWidget(sep)

        env = dotenv_values(".env")
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        label_style = f"color: {C_SUBTEXT}; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;"

        def make_label(text):
            l = QLabel(text.upper())
            l.setStyleSheet(label_style)
            return l

        self.username_input = QLineEdit(env.get("Username", ""))
        self.assistant_input = QLineEdit(env.get("Assistantname", ""))

        self.voice_combo = QComboBox()
        # (display label, edge-tts voice id, matching speech-recognition locale)
        self.VOICE_OPTIONS = [
            ("English (US) – Jenny, female",           "en-US-JennyNeural",    "en-US"),
            ("English (US) – Guy, male",               "en-US-GuyNeural",      "en-US"),
            ("English (UK) – Sonia, female",           "en-GB-SoniaNeural",    "en-GB"),
            ("Urdu (Pakistan) – Asad  ♂  [best male]", "ur-PK-AsadNeural",     "ur-PK"),
            ("Urdu (Pakistan) – Uzma  ♀",              "ur-PK-UzmaNeural",     "ur-PK"),
            ("Urdu (India)    – Salman ♂",             "ur-IN-SalmanNeural",   "ur-IN"),
            ("Urdu (India)    – Gul   ♀",              "ur-IN-GulNeural",      "ur-IN"),
            ("Hindi (India) – Swara, female",          "hi-IN-SwaraNeural",    "hi-IN"),
            ("Arabic – Zariyah, female",               "ar-SA-ZariyahNeural",  "ar-SA"),
        ]
        self.voice_combo.addItems([label for label, _, _ in self.VOICE_OPTIONS])
        current_voice = env.get("AssistantVoice", "en-US-JennyNeural")
        match_idx = next((i for i, (_, vid, _) in enumerate(self.VOICE_OPTIONS) if vid == current_voice), 0)
        self.voice_combo.setCurrentIndex(match_idx)
        # When the voice changes, snap the recognition language to match --
        # most people want both the assistant's voice and what it listens
        # for to be the same language, so this avoids a mismatched setup
        # (e.g. speaking Urdu while AssistantVoice is still English).
        self.voice_combo.currentIndexChanged.connect(self._syncLanguageToVoice)

        self.groq_input = QLineEdit(env.get("GroqAPIKey", ""))
        self.groq_input.setEchoMode(QLineEdit.Password)
        self.cohere_input = QLineEdit(env.get("CohereAPIKey", ""))
        self.cohere_input.setEchoMode(QLineEdit.Password)
        self.weather_key_input = QLineEdit(env.get("WeatherAPIKey", ""))
        self.weather_key_input.setEchoMode(QLineEdit.Password)
        self.weather_city_input = QLineEdit(env.get("WeatherCity", "Lahore"))

        self.lang_combo = QComboBox()
        # Full BCP-47 locale tags -- the browser speech-recognition engine
        # (Backend/SpeechToText.py) needs a full tag like "ur-PK", not a
        # bare "ur", to reliably recognize Urdu speech.
        langs = ["en-US", "en-GB", "ur-PK", "ur-IN", "hi-IN", "ar-SA", "fr-FR", "de-DE", "es-ES", "ja-JP", "zh-CN"]
        self.lang_combo.addItems(langs)
        cur = env.get("InputLanguage", "en-US")
        if cur in langs:
            self.lang_combo.setCurrentIndex(langs.index(cur))

        form.addRow(make_label("Your Name"), self.username_input)
        form.addRow(make_label("Assistant Name"), self.assistant_input)
        form.addRow(make_label("Voice"), self.voice_combo)
        form.addRow(make_label("Listening Language"), self.lang_combo)
        form.addRow(make_label("Groq API Key"), self.groq_input)
        form.addRow(make_label("Cohere API Key"), self.cohere_input)
        form.addRow(make_label("Weather API Key"), self.weather_key_input)
        form.addRow(make_label("Weather City"), self.weather_city_input)
        main_layout.addLayout(form)

        main_layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = GlowButton("Cancel", color=C_SUBTEXT)
        cancel_btn.clicked.connect(self.reject)
        save_btn = GlowButton("Save Settings", color=C_ACCENT)
        save_btn.setFixedWidth(140)
        save_btn.clicked.connect(self.saveSettings)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        main_layout.addLayout(btn_row)

    def _syncLanguageToVoice(self, index):
        if 0 <= index < len(self.VOICE_OPTIONS):
            _, _, locale = self.VOICE_OPTIONS[index]
            match_idx = self.lang_combo.findText(locale)
            if match_idx == -1:
                # Locale not in the preset list (e.g. ar-SA) -- add it so
                # the dropdown can still show/select it.
                self.lang_combo.addItem(locale)
                match_idx = self.lang_combo.findText(locale)
            self.lang_combo.setCurrentIndex(match_idx)

    def saveSettings(self):
        env_path = os.path.join(os.getcwd(), ".env")
        set_key(env_path, "Username", self.username_input.text())
        set_key(env_path, "Assistantname", self.assistant_input.text())
        _, voice_id, _ = self.VOICE_OPTIONS[self.voice_combo.currentIndex()]
        set_key(env_path, "AssistantVoice", voice_id)
        set_key(env_path, "InputLanguage", self.lang_combo.currentText())
        if self.groq_input.text():
            set_key(env_path, "GroqAPIKey", self.groq_input.text())
        if self.cohere_input.text():
            set_key(env_path, "CohereAPIKey", self.cohere_input.text())
        if self.weather_key_input.text():
            set_key(env_path, "WeatherAPIKey", self.weather_key_input.text())
        if self.weather_city_input.text():
            set_key(env_path, "WeatherCity", self.weather_city_input.text())
        msg = QMessageBox(self)
        msg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        msg.setStyleSheet(f"QMessageBox {{ background-color: {C_PANEL}; color: {C_TEXT}; border: 1px solid {C_BORDER}; border-radius: 12px; }} QPushButton {{ background: {C_ACCENT}33; color: {C_TEXT}; border: 1px solid {C_ACCENT}55; border-radius: 6px; padding: 6px 16px; }}")
        msg.setText("✓  Settings saved successfully.\nRestart Jarvis to apply changes.")
        msg.exec_()
        self.accept()


# ── Text Input Bar ────────────────────────────────────────────────────────────────

class TextInputBar(QWidget):
    messageSubmitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet(f"background-color: {C_PANEL}; border-top: 1px solid {C_BORDER};")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message...")
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C_SURFACE};
                color: {C_TEXT};
                border: 1px solid {C_BORDER};
                border-radius: 20px;
                padding: 8px 18px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {C_ACCENT};
            }}
            QLineEdit::placeholder {{
                color: {C_SUBTEXT};
            }}
        """)
        self.text_input.returnPressed.connect(self.submitMessage)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(40, 40)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {C_ACCENT},stop:1 {C_ACCENT2});
                color: white;
                border-radius: 20px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)
        send_btn.clicked.connect(self.submitMessage)

        layout.addWidget(self.text_input)
        layout.addWidget(send_btn)

    def submitMessage(self):
        text = self.text_input.text().strip()
        if text:
            self.text_input.clear()
            self.messageSubmitted.emit(text)


# ── Chat Bubble Area ──────────────────────────────────────────────────────────────

class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {C_PANEL}; border: 1px solid {C_BORDER}; border-radius: 12px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header: "Conversation" + Clear / Export ──
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet(f"background: transparent; border: none; border-bottom: 1px solid {C_BORDER};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 12, 0)

        title = QLabel("Conversation")
        title.setStyleSheet(f"color: {C_TEXT}; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; background: transparent; border: none;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        clear_btn = QPushButton("🗑  Clear")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {C_SUBTEXT}; border: none; font-size: 11px; padding: 4px 8px; }}
            QPushButton:hover {{ color: {C_WARNING}; }}
        """)
        clear_btn.clicked.connect(self.clearDisplay)
        h_layout.addWidget(clear_btn)

        export_btn = QPushButton("⤓  Export")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {C_SUBTEXT}; border: none; font-size: 11px; padding: 4px 8px; }}
            QPushButton:hover {{ color: {C_ACCENT}; }}
        """)
        export_btn.clicked.connect(self.exportConversation)
        h_layout.addWidget(export_btn)

        layout.addWidget(header)

        # ── Chat display ──
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        self.chat_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {C_PANEL};
                color: {C_TEXT};
                padding: 14px 16px;
                border: none;
                selection-background-color: {C_ACCENT}44;
            }}
            QScrollBar:vertical {{
                background: {C_PANEL}; width: 6px; margin: 0; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {C_BORDER}; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {C_ACCENT}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        font = QFont("Segoe UI", 10)
        self.chat_text_edit.setFont(font)
        layout.addWidget(self.chat_text_edit, stretch=1)

        # ── Text input ──
        self.input_bar = TextInputBar()
        self.input_bar.messageSubmitted.connect(self.handleTextInput)
        layout.addWidget(self.input_bar)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.start(50)

    def handleTextInput(self, text):
        with open(TempDirectoryPath('TextInput.data'), 'w', encoding='utf-8') as f:
            f.write(text)
        self.addMessage(f"{Username}: {text}", C_ACCENT)

    def loadMessages(self):
        global old_chat_message
        try:
            with open(TempDirectoryPath('Responses.data'), 'r', encoding='utf-8') as f:
                messages = f.read()
            if messages and messages != old_chat_message:
                self.addMessage(messages, C_TEXT)
                old_chat_message = messages
        except FileNotFoundError:
            pass

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        fmt = QTextCharFormat()
        fmtb = QTextBlockFormat()
        fmtb.setTopMargin(8)
        fmtb.setLeftMargin(4)
        fmtb.setBottomMargin(2)
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.setBlockFormat(fmtb)
        cursor.movePosition(cursor.End)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)
        self.chat_text_edit.ensureCursorVisible()

    def clearDisplay(self):
        reply = QMessageBox(self)
        reply.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        reply.setStyleSheet(f"""
            QMessageBox {{ background-color: {C_PANEL}; color: {C_TEXT}; border: 1px solid {C_BORDER}; border-radius: 12px; padding: 8px; }}
            QLabel {{ color: {C_TEXT}; font-size: 13px; padding: 8px; }}
            QPushButton {{
                background: {C_SURFACE}; color: {C_TEXT};
                border: 1px solid {C_BORDER}; border-radius: 6px;
                padding: 6px 20px; font-size: 12px; min-width: 70px;
            }}
            QPushButton:hover {{ border-color: {C_ACCENT}; color: {C_ACCENT}; }}
        """)
        reply.setText("Clear conversation?")
        reply.setInformativeText("This cannot be undone.")
        yes = reply.addButton("Clear", QMessageBox.AcceptRole)
        reply.addButton("Cancel", QMessageBox.RejectRole)
        reply.exec_()
        if reply.clickedButton() == yes:
            if DeleteChatHistory():
                self.chat_text_edit.clear()
                global old_chat_message
                old_chat_message = ""
                SetAsssistantStatus("History cleared.")
                QTimer.singleShot(2000, lambda: SetAsssistantStatus("Available..."))

    def exportConversation(self):
        try:
            export_dir = os.path.join(current_dir, "Data")
            os.makedirs(export_dir, exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(export_dir, f"Conversation_{stamp}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.chat_text_edit.toPlainText())
            self._notify(f"Exported to Data/Conversation_{stamp}.txt")
        except Exception as e:
            self._notify(f"Export failed: {e}")

    def _notify(self, text):
        SetAsssistantStatus(text[:60])
        QTimer.singleShot(2500, lambda: SetAsssistantStatus("Available..."))


# ── AI Core Orb ───────────────────────────────────────────────────────────────────

class AICore(QWidget):
    """Animated reactor-style core, like the reference HUD. Pure QPainter,
    no image assets needed, so it scales crisply at any size."""

    STATE_COLORS = {
        "idle": C_ACCENT,
        "listening": C_ACCENT,
        "thinking": C_WARNING,
        "searching": C_WARNING,
        "answering": C_ACCENT2,
        "stopped": C_STOP,
        "error": C_STOP,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(260, 260)
        self._angle = 0
        self._pulse = 0.0
        self._pulse_dir = 1
        self._state = "idle"
        self._color = QColor(C_ACCENT)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick)
        self.anim_timer.start(30)

    def setState(self, state_text):
        state_text = (state_text or "").lower()
        if "listen" in state_text:
            key = "listening"
        elif "think" in state_text:
            key = "thinking"
        elif "search" in state_text:
            key = "searching"
        elif "answer" in state_text:
            key = "answering"
        elif "stop" in state_text or "error" in state_text:
            key = "stopped"
        else:
            key = "idle"
        if key != self._state:
            self._state = key
            self._color = QColor(self.STATE_COLORS.get(key, C_ACCENT))

    def _tick(self):
        speed = 1.4 if self._state in ("listening", "answering") else 0.6
        self._angle = (self._angle + speed) % 360
        self._pulse += 0.04 * self._pulse_dir
        if self._pulse > 1.0:
            self._pulse, self._pulse_dir = 1.0, -1
        elif self._pulse < 0.0:
            self._pulse, self._pulse_dir = 0.0, 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        base_r = min(self.width(), self.height()) / 2 - 6

        color = self._color
        pulse_extra = 5 * self._pulse

        # 4 concentric faint background glow halos (wide, very transparent)
        for i, frac in enumerate([1.0, 0.78, 0.58, 0.40]):
            alpha = 18 - i * 3
            glow_pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha))
            glow_pen.setWidth(12 - i * 2)
            p.setPen(glow_pen)
            p.setBrush(Qt.NoBrush)
            r = base_r * frac + pulse_extra * 0.3
            p.drawEllipse(QRect(int(cx - r), int(cy - r), int(r * 2), int(r * 2)))

        # Ring 1 (outermost) -- solid, bright
        pen1 = QPen(QColor(color.red(), color.green(), color.blue(), 200))
        pen1.setWidth(2)
        p.setPen(pen1)
        p.setBrush(Qt.NoBrush)
        r1 = base_r * 0.96
        p.drawEllipse(QRect(int(cx - r1), int(cy - r1), int(r1 * 2), int(r1 * 2)))

        # Ring 2 -- rotating dashed
        p.save()
        p.translate(cx, cy)
        p.rotate(self._angle)
        pen2 = QPen(QColor(color.red(), color.green(), color.blue(), 170))
        pen2.setWidth(2)
        pen2.setStyle(Qt.DashLine)
        p.setPen(pen2)
        r2 = base_r * 0.74
        p.drawEllipse(QRect(int(-r2), int(-r2), int(r2 * 2), int(r2 * 2)))
        p.restore()

        # Ring 3 -- counter-rotating, solid
        p.save()
        p.translate(cx, cy)
        p.rotate(-self._angle * 1.4)
        pen3 = QPen(QColor(color.red(), color.green(), color.blue(), 130))
        pen3.setWidth(1)
        p.setPen(pen3)
        r3 = base_r * 0.54 + pulse_extra * 0.2
        p.drawEllipse(QRect(int(-r3), int(-r3), int(r3 * 2), int(r3 * 2)))
        p.restore()

        # Ring 4 (innermost solid ring)
        pen4 = QPen(QColor(color.red(), color.green(), color.blue(), 100))
        pen4.setWidth(1)
        p.setPen(pen4)
        r4 = base_r * 0.36 + pulse_extra * 0.15
        p.drawEllipse(QRect(int(cx - r4), int(cy - r4), int(r4 * 2), int(r4 * 2)))

        # Core radial glow
        grad = QRadialGradient(cx, cy, base_r * 0.38)
        c1 = QColor(color.red(), color.green(), color.blue(), 220)
        c2 = QColor(color.red(), color.green(), color.blue(), 0)
        grad.setColorAt(0, c1)
        grad.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), 60))
        grad.setColorAt(1, c2)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        core_r = base_r * 0.38 + pulse_extra * 0.4
        p.drawEllipse(QRect(int(cx - core_r), int(cy - core_r), int(core_r * 2), int(core_r * 2)))

        # Bright solid center dot
        p.setBrush(QColor(color.red(), color.green(), color.blue(), 240))
        inner_r = base_r * 0.16
        p.drawEllipse(QRect(int(cx - inner_r), int(cy - inner_r), int(inner_r * 2), int(inner_r * 2)))

        # Animated dots inside core (subtle "thinking" indicator)
        if self._state in ("thinking", "searching"):
            for i in range(4):
                a = math.radians(self._angle * 3 + i * 90)
                dx = cx + math.cos(a) * inner_r * 0.5
                dy = cy + math.sin(a) * inner_r * 0.5
                p.setBrush(QColor(C_BG))
                p.drawEllipse(QRect(int(dx - 2), int(dy - 2), 4, 4))

        p.end()


class ClockWidget(QLabel):
    """Top bar live clock + date."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"color: {C_TEXT}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        self.setAlignment(Qt.AlignCenter)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

    def refresh(self):
        now = datetime.datetime.now()
        self.setText(now.strftime("%I:%M:%S %p   •   %B %d, %Y"))


# ── Initial / Home Screen ─────────────────────────────────────────────────────────

def _spaced(text):
    """Adds letter-spacing-friendly gaps for the assistant name display."""
    return " ".join(list(text))


class InitialScreen(QWidget):
    """The main dashboard: left sidebar (stats), center (AI core + controls),
    right (conversation). Mirrors the reference HUD layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {C_BG};")

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # ── Left sidebar ──
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(14)

        self.stats_card = SystemStatsCard()
        self.weather_card = WeatherCard()
        self.camera_card = CameraCard()
        self.uptime_card = UptimeCard()

        sb_layout.addWidget(self.stats_card)
        sb_layout.addWidget(self.weather_card)
        sb_layout.addWidget(self.camera_card)
        sb_layout.addWidget(self.uptime_card)
        sb_layout.addStretch()

        root.addWidget(sidebar)

        # ── Center column ──
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center_layout.addStretch(2)

        self.core = AICore()
        center_layout.addWidget(self.core, alignment=Qt.AlignCenter)

        center_layout.addSpacing(12)

        # Format name as J.A.R.V.I.S style if it looks like an acronym
        raw_name = Assistantname.upper()
        if "." not in raw_name:
            formatted_name = ".".join(list(raw_name))
        else:
            formatted_name = raw_name

        name_lbl = QLabel(formatted_name)
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(f"""
            color: {C_TEXT};
            font-size: 26px;
            font-weight: 800;
            letter-spacing: 8px;
            background: transparent;
            border: none;
        """)
        center_layout.addWidget(name_lbl)

        center_layout.addSpacing(10)

        self.status_pill = StatusPill()
        center_layout.addWidget(self.status_pill, alignment=Qt.AlignCenter)

        center_layout.addStretch(3)

        # Bottom control row: camera (placeholder/disabled), mic, keyboard
        controls = QHBoxLayout()
        controls.setSpacing(14)
        controls.addStretch()

        self.mic_btn = QLabel()
        self.mic_btn.setFixedSize(56, 56)
        self.mic_btn.setAlignment(Qt.AlignCenter)
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_on = False
        self._style_mic()
        self.mic_btn.mousePressEvent = self.toggleMic
        controls.addWidget(self.mic_btn)

        self.kb_btn = QLabel("⌨")
        self.kb_btn.setFixedSize(56, 56)
        self.kb_btn.setAlignment(Qt.AlignCenter)
        self.kb_btn.setCursor(Qt.PointingHandCursor)
        self.kb_btn.setStyleSheet(f"background-color: {C_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 28px; color: {C_SUBTEXT}; font-size: 20px;")
        self.kb_btn.mousePressEvent = self._focusTextInput
        controls.addWidget(self.kb_btn)

        controls.addStretch()
        center_layout.addLayout(controls)

        center_layout.addSpacing(6)
        hint = QLabel("Tap the mic to talk, or type a message on the right")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 11px; letter-spacing: 0.5px; background: transparent; border: none;")
        center_layout.addWidget(hint)
        center_layout.addStretch(1)

        root.addWidget(center, stretch=1)

        # ── Right: conversation panel ──
        self.chat = ChatSection()
        self.chat.setFixedWidth(380)
        root.addWidget(self.chat)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateStatus)
        self.timer.start(100)

    def _focusTextInput(self, event=None):
        self.chat.input_bar.text_input.setFocus()

    def updateStatus(self):
        try:
            with open(TempDirectoryPath('Status.data'), 'r', encoding='utf-8') as f:
                status = f.read().strip()
            if status:
                self.status_pill.setText(status)
                self.core.setState(status)
        except Exception:
            pass

    def _style_mic(self):
        if self.mic_on:
            color = C_ACCENT
            icon = GraphicsDirectoryPath('Mic_on.png')
        else:
            color = C_SUBTEXT
            icon = GraphicsDirectoryPath('Mic_off.png')
        self.mic_btn.setStyleSheet(f"background-color: {color}1f; border: 1px solid {color}66; border-radius: 28px;")
        if os.path.exists(icon):
            pix = QPixmap(icon).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.mic_btn.setPixmap(pix)
        else:
            self.mic_btn.setText("🎙" if self.mic_on else "🎙")

    def toggleMic(self, event=None):
        self.mic_on = not self.mic_on
        if self.mic_on:
            MicButtonClosed()
        else:
            MicButtonInitiated()
        self._style_mic()




# ── Title Bar ─────────────────────────────────────────────────────────────────────

class CustomTopBar(QWidget):
    def __init__(self, parent, home_screen):
        super().__init__(parent)
        self.home_screen = home_screen
        self._drag_pos = None
        self.setFixedHeight(56)
        self.setObjectName("topBar")
        self.setStyleSheet(f"""
            QWidget#topBar {{
                background-color: {C_PANEL};
                border-bottom: 1px solid {C_BORDER};
            }}
        """)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 10, 0)
        layout.setSpacing(10)

        # ── Left: logo + online status ──
        left = QHBoxLayout()
        left.setSpacing(8)
        raw_logo = Assistantname.upper()
        formatted_logo = ".".join(list(raw_logo)) if "." not in raw_logo else raw_logo
        logo = QLabel(formatted_logo)
        logo.setStyleSheet(f"""
            color: {C_ACCENT};
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 3px;
            background: transparent;
            border: none;
        """)
        left.addWidget(logo)

        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {C_SUCCESS}; font-size: 9px; background: transparent; border: none;")
        left.addWidget(status_dot)
        online_lbl = QLabel("Online")
        online_lbl.setStyleSheet(f"color: {C_SUCCESS}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        left.addWidget(online_lbl)

        left_widget = QWidget()
        left_widget.setLayout(left)
        layout.addWidget(left_widget)

        layout.addStretch(1)

        # ── Center: live clock ──
        self.clock = ClockWidget()
        layout.addWidget(self.clock)

        layout.addStretch(1)

        # ── Right: weather pill ──
        self.weather_pill = QLabel("--°C")
        self.weather_pill.setStyleSheet(f"""
            color: {C_TEXT}; font-size: 12px; font-weight: 600;
            background-color: {C_SURFACE}; border: 1px solid {C_BORDER};
            border-radius: 12px; padding: 4px 12px; background-clip: padding;
        """)
        layout.addWidget(self.weather_pill)
        self._wire_weather_pill()

        layout.addSpacing(10)

        # Action buttons
        self.stop_btn = GlowButton("⏹  Stop", color=C_STOP)
        self.stop_btn.setFixedWidth(82)
        self.stop_btn.clicked.connect(self.stopJarvis)
        layout.addWidget(self.stop_btn)

        settings_btn = GlowButton("⚙", color=C_ACCENT2)
        settings_btn.setFixedWidth(38)
        settings_btn.clicked.connect(self.openSettings)
        layout.addWidget(settings_btn)

        layout.addSpacing(10)

        # Window controls
        min_btn = IconButton(rf"{GraphicsDirPath}\Minimize.png", 30)
        min_btn.clicked.connect(self.minimizeWindow)

        self.max_btn = IconButton(rf"{GraphicsDirPath}\Maximize.png", 30)
        self.max_btn.clicked.connect(self.maximizeWindow)

        close_btn = IconButton(rf"{GraphicsDirPath}\Close.png", 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-radius: 15px; }}
            QPushButton:hover {{ background-color: {C_STOP}44; }}
        """)
        close_btn.clicked.connect(self.closeWindow)

        layout.addWidget(min_btn)
        layout.addWidget(self.max_btn)
        layout.addWidget(close_btn)

    def _wire_weather_pill(self):
        """Keep the top-bar weather pill in sync with the sidebar weather card."""
        def sync():
            card = self.home_screen.weather_card
            self.weather_pill.setText(f"{card.temp_lbl.text()}  {card.city_lbl.text()}")
        self._pill_timer = QTimer(self)
        self._pill_timer.timeout.connect(sync)
        self._pill_timer.start(2000)
        QTimer.singleShot(1500, sync)

    # ── Drag to move ──
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.parent().frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos:
            self.parent().move(e.globalPos() - self._drag_pos)

    # ── Actions ──
    def stopJarvis(self):
        try:
            SetStopFlag(True)
            SetMicrophoneStatus("False")
            SetAsssistantStatus("Stopped.")
            self.stop_btn.setText("⏹  Stopped")
            self.stop_btn.setEnabled(False)
            # Re-enable the button quickly so the user isn't stuck, but don't
            # clear the actual stop flag until the backend confirms it has
            # settled back to idle -- otherwise a still-running task could get
            # un-stopped while it's mid-flight.
            QTimer.singleShot(800, self._reenableStopButton)
            self._stop_watch_timer = QTimer(self)
            self._stop_watch_timer.timeout.connect(self._checkBackendIdle)
            self._stop_watch_timer.start(150)
        except Exception as e:
            # If anything above fails, surface it loudly instead of the
            # button silently doing nothing -- this print goes to the
            # console window Main.py is running in.
            print(f"[STOP BUTTON ERROR] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    def _reenableStopButton(self):
        self.stop_btn.setText("⏹  Stop")
        self.stop_btn.setEnabled(True)

    def _checkBackendIdle(self):
        status = GetAssistantStatus().strip()
        if status == "Available...":
            SetStopFlag(False)
            if hasattr(self, "_stop_watch_timer"):
                self._stop_watch_timer.stop()

    def openSettings(self):
        SettingsDialog(self).exec_()

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
        else:
            self.parent().showMaximized()

    def closeWindow(self):
        self.parent().close()


# ── Main Window ───────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        desktop = QApplication.desktop()
        self.setGeometry(0, 0, desktop.screenGeometry().width(), desktop.screenGeometry().height())
        self.setStyleSheet(f"background-color: {C_BG};")

        self.home = InitialScreen()
        top_bar = CustomTopBar(self, self.home)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(self.home)

        # Init temp files
        os.makedirs(TempDirPath, exist_ok=True)
        SetStopFlag(False)
        with open(TempDirectoryPath('TextInput.data'), 'w', encoding='utf-8') as f:
            f.write("")


def GraphicalUserInterface():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(C_BG))
    palette.setColor(QPalette.WindowText, QColor(C_TEXT))
    app.setPalette(palette)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
