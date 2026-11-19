import os
import sys
import json
import threading
import time
import traceback
from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QApplication
from modern_ui import ControlCenter
import winreg

import keyboard
import pystray
from PIL import Image, ImageDraw
import pyperclip
import pyautogui
import speech_recognition as sr

APP_NAME = "Bangla Voice Tray"
APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "BanglaVoiceTray")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
LOG_PATH = os.path.join(APP_DIR, "app.log")
os.makedirs(APP_DIR, exist_ok=True)

DEFAULTS = {
    "toggle_hotkey": "ctrl+shift+b",
    "language": "bn-BD",
    "start_with_windows": True,
    "paste_delay": 0.15,
    "microphone_device_index": None,
    "window_opacity": 0.98
}

def log(message):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + str(message) + "\n")
    except Exception:
        pass

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULTS, **data}
    except Exception:
        return DEFAULTS.copy()

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def set_startup(enabled):
    # Use a per-user Run key; no administrator rights required.
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                if getattr(sys, "frozen", False):
                    command = '"' + sys.executable + '"'
                else:
                    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                    if not os.path.exists(pythonw):
                        pythonw = sys.executable
                    command = '"' + pythonw + '" "' + os.path.abspath(__file__) + '"'
                winreg.SetValueEx(key, "BanglaVoiceTray", 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, "BanglaVoiceTray")
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        log("Startup registry error: " + repr(e))
        return False

def make_icon_image(active=False):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = (220, 45, 45, 255) if active else (0, 119, 210, 255)
    d.rounded_rectangle((4, 4, 60, 60), radius=15, fill=color)
    d.ellipse((24, 12, 40, 37), fill="white")
    d.rounded_rectangle((21, 24, 43, 43), radius=10, outline="white", width=4)
    d.line((32, 43, 32, 50), fill="white", width=4)
    d.line((23, 51, 41, 51), fill="white", width=4)
    return img

class _UiBridge(QObject):
    show_requested = Signal()
    quit_requested = Signal()

class _UiHost(QObject):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    @Slot()
    def show_dashboard(self):
        window = self.owner.dashboard_window
        if window is None:
            window = ControlCenter(self.owner)
            self.owner.dashboard_window = window
        if window.isMinimized():
            window.showNormal()
        else:
            window.show()
        window.raise_()
        window.activateWindow()

    @Slot()
    def quit_app(self):
        app = QApplication.instance()
        if app:
            app.quit()

class BanglaVoiceTray:
    def __init__(self):
        self.config = load_config()
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.active = False
        self.busy = False
        self.stop_event = threading.Event()
        self.icon = None
        self.dashboard_window = None
        self._qt_app = None
        self._ui_bridge = None
        self._ui_host = None
        self._pending_dashboard = False
        self.hotkey_handle = None
        self.last_error = ""
        self.last_status = "প্রস্তুত · মাইক্রোফোন বন্ধ"
        self.settings_window_open = False
        self.settings_lock = threading.Lock()
        self.dashboard_window_open = False
        self.dashboard_lock = threading.Lock()
        self._register_hotkey()
        if self.config.get("start_with_windows", True):
            set_startup(True)

    def _register_hotkey(self):
        self.last_error = ""
        if self.hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self.hotkey_handle)
            except Exception:
                pass
            self.hotkey_handle = None
        try:
            handle = keyboard.add_hotkey(
                self.config["toggle_hotkey"], self.toggle_listening,
                suppress=False, trigger_on_release=False
            )
            self.hotkey_handle = handle
            log("Hotkey registered: " + self.config["toggle_hotkey"])
            return True
        except Exception as e:
            self.last_error = str(e)
            self.hotkey_handle = None
            log("Hotkey registration failed: " + repr(e))
            return False

    def notify(self, title, message):
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass

    def update_icon(self):
        if self.icon:
            try:
                self.icon.icon = make_icon_image(self.active)
            except Exception:
                log("Tray icon update failed: " + traceback.format_exc())

    def toggle_listening(self):
        # Stopping must work while the recorder is waiting for or processing audio.
        if self.active:
            self.active = False
            self.last_status = "প্রস্তুত · মাইক্রোফোন বন্ধ"
            self.update_icon()
            return

        if self.busy:
            return

        self.active = True
        self.last_status = "শুনছে · বন্ধ করতে icon বা shortcut চাপুন"
        self.update_icon()
        threading.Thread(target=self._record_once, daemon=True).start()

    def _record_once(self):
        self.busy = True
        try:
            device = self.config.get("microphone_device_index")
            with sr.Microphone(device_index=device) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.45)
                while self.active and not self.stop_event.is_set():
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=12)
                    except sr.WaitTimeoutError:
                        continue
                    if not self.active:
                        break
                    try:
                        text = self.recognizer.recognize_google(audio, language=self.config.get("language", "bn-BD"))
                        text = text.strip()
                        if text:
                            self._paste_text(text)
                    except sr.UnknownValueError:
                        self.last_status = "কথা বোঝা যায়নি · আবার বলুন"
                        self.notify(APP_NAME, "কথা বুঝতে পারিনি—আবার বলুন।")
                    except sr.RequestError as e:
                        self.last_status = "ইন্টারনেট / speech service-এ সমস্যা"
                        self.notify(APP_NAME, "ইন্টারনেট/স্পিচ সার্ভিসে সমস্যা হয়েছে।")
                        log("Speech API error: " + repr(e))
                        self.active = False
                        break
        except Exception as e:
            self.last_status = "মাইক্রোফোন চালু হয়নি · Settings ও log দেখুন"
            log("Microphone/record error: " + traceback.format_exc())
            self.notify(APP_NAME, "মাইক্রোফোন চালু হয়নি। Windows microphone permission চালু করুন বা Settings-এ input device বদলান।")
            self.active = False
        finally:
            self.busy = False
            if not self.active and not self.last_status.startswith("ইন্টারনেট") and not self.last_status.startswith("মাইক্রোফোন চালু হয়নি"):
                self.last_status = "প্রস্তুত · মাইক্রোফোন বন্ধ"
            self.update_icon()

    def _paste_text(self, text):
        # Clipboard-based paste is compatible with many, but not all, text fields.
        try:
            old = None
            try:
                old = pyperclip.paste()
            except Exception:
                pass
            pyperclip.copy(text)
            time.sleep(float(self.config.get("paste_delay", 0.15)))
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.25)
            # Do not restore clipboard by default: restoring too quickly can break paste.
            log("Transcribed and pasted " + str(len(text)) + " characters.")
            self.last_status = f"লেখা বসানো হয়েছে · {len(text)} অক্ষর"
        except Exception:
            log("Paste error: " + traceback.format_exc())
            self.notify(APP_NAME, "লেখা পেস্ট করা যায়নি। টেক্সট বক্সে ক্লিক করে আবার চেষ্টা করুন।")

    def open_settings(self, icon=None, item=None):
        self.open_dashboard()

    def open_dashboard(self, icon=None, item=None):
        if self._ui_bridge:
            self._ui_bridge.show_requested.emit()
        else:
            self._pending_dashboard = True

    def save_gui_settings(self, values):
        old = self.config.copy()
        new = old.copy()
        new.update(values)
        self.config = new
        if not self._register_hotkey():
            error = self.last_error
            self.config = old
            self._register_hotkey()
            return False, "এই shortcut register করা যায়নি। অন্য shortcut বেছে নিন।\n\n" + error
        if not set_startup(new.get("start_with_windows", True)):
            self.config = old
            self._register_hotkey()
            return False, "Windows startup setting সংরক্ষণ করা যায়নি।"
        try:
            save_config(new)
        except Exception as e:
            set_startup(old.get("start_with_windows", True))
            self.config = old
            self._register_hotkey()
            return False, "সেটিংস ফাইলে লেখা যায়নি।\n\n" + str(e)
        self.last_status = "সেটিংস সংরক্ষিত · shortcut: " + new["toggle_hotkey"]
        return True, ""

    def toggle_startup(self, icon=None, item=None):
        previous = bool(self.config.get("start_with_windows", True))
        enabled = not previous
        if not set_startup(enabled):
            self.last_status = "Windows startup setting পরিবর্তন করা যায়নি"
            self.open_settings()
            return
        self.config["start_with_windows"] = enabled
        try:
            save_config(self.config)
            self.last_status = "Windows startup " + ("চালু" if enabled else "বন্ধ")
        except Exception as e:
            set_startup(previous)
            self.config["start_with_windows"] = previous
            self.last_status = "সেটিংস save হয়নি · " + str(e)
            log("Startup config save failed: " + traceback.format_exc())
        self.open_settings()

    def show_status(self, icon=None, item=None):
        self.open_dashboard()

    def quit(self, icon=None, item=None):
        self.active = False
        self.stop_event.set()
        try:
            if self.hotkey_handle is not None:
                keyboard.remove_hotkey(self.hotkey_handle)
        except Exception:
            pass
        if self.icon:
            self.icon.stop()
        if self._ui_bridge:
            self._ui_bridge.quit_requested.emit()

    def run(self):
        menu = pystray.Menu(
            pystray.MenuItem("মাইক্রোফোন চালু/বন্ধ", self.toggle_listening, default=True),
            pystray.MenuItem("অবস্থা ও শর্টকাট দেখুন", self.show_status),
            pystray.MenuItem("সেটিংস…", self.open_settings),
            pystray.MenuItem("Windows startup চালু/বন্ধ", self.toggle_startup,
                             checked=lambda _item: bool(self.config.get("start_with_windows", True))),
            pystray.MenuItem("প্রস্থান", self.quit)
        )
        self._qt_app = QApplication.instance() or QApplication(sys.argv)
        self._qt_app.setApplicationName(APP_NAME)
        self._qt_app.setQuitOnLastWindowClosed(False)
        self._ui_bridge = _UiBridge()
        self._ui_host = _UiHost(self)
        self._ui_bridge.show_requested.connect(self._ui_host.show_dashboard, Qt.ConnectionType.QueuedConnection)
        self._ui_bridge.quit_requested.connect(self._ui_host.quit_app, Qt.ConnectionType.QueuedConnection)
        self.icon = pystray.Icon("BanglaVoiceTray", make_icon_image(self.active), APP_NAME, menu)
        threading.Thread(target=self.icon.run, name="BanglaVoiceTrayIcon", daemon=True).start()
        if self._pending_dashboard:
            self._ui_bridge.show_requested.emit()
        self._qt_app.exec()
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
        self.stop_event.set()

if __name__ == "__main__":
    try:
        app = BanglaVoiceTray()
        app.run()
    except Exception:
        log(traceback.format_exc())
        raise
