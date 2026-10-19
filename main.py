import os
import sys
import json
import threading
import time
import traceback
import tkinter as tk
from tkinter import messagebox, ttk
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
    "microphone_device_index": None
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

class BanglaVoiceTray:
    def __init__(self):
        self.config = load_config()
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.active = False
        self.busy = False
        self.stop_event = threading.Event()
        self.icon = None
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
            self.notify(APP_NAME, "মাইক্রোফোন চালু হয়নি। Settings ও app.log দেখুন।")
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
        with self.settings_lock:
            if self.settings_window_open:
                return
            self.settings_window_open = True
        threading.Thread(target=self._settings_window, daemon=True).start()

    def open_dashboard(self, icon=None, item=None):
        with self.dashboard_lock:
            if self.dashboard_window_open:
                return
            self.dashboard_window_open = True
        threading.Thread(target=self._dashboard_window, daemon=True).start()

    def _dashboard_window(self):
        root = None
        try:
            root = tk.Tk()
            root.title("Bangla Voice Type · Dashboard")
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            window_width = min(1040, max(820, int(screen_width * 0.88)))
            window_height = min(780, max(620, int(screen_height * 0.84)))
            root.geometry(f"{window_width}x{window_height}")
            root.minsize(800, 600)
            root.configure(bg="#08111f")
            root.resizable(True, True)
            try:
                root.attributes("-alpha", 0.985)
            except tk.TclError:
                pass

            colors = {
                "bg": "#08111f", "panel": "#101c2d", "panel2": "#1a2a40",
                "line": "#355072", "text": "#f8fbff", "muted": "#c2d0e0",
                "blue": "#1677e8", "cyan": "#59d6ff", "red": "#ff5668",
                "green": "#45dba2", "yellow": "#ffd166"
            }
            style = ttk.Style(root)
            style.theme_use("clam")
            style.configure("Dash.TCombobox", fieldbackground=colors["panel2"], background=colors["panel2"],
                            foreground=colors["text"], arrowcolor=colors["cyan"], bordercolor=colors["line"], padding=8)
            style.map("Dash.TCombobox", fieldbackground=[("readonly", colors["panel2"])],
                      foreground=[("readonly", colors["text"])])

            header = tk.Frame(root, bg=colors["bg"])
            header.pack(fill="x", padx=26, pady=(22, 18))
            mark = tk.Canvas(header, width=62, height=62, bg=colors["bg"], highlightthickness=0)
            mark.pack(side="left", padx=(0, 14))
            mark.create_oval(3, 3, 59, 59, fill=colors["blue"], outline="")
            mark.create_oval(23, 12, 39, 37, fill="white", outline="")
            mark.create_line(19, 31, 19, 37, 31, 44, 43, 37, 43, 31, fill="white", width=3, smooth=True)
            mark.create_line(31, 44, 31, 51, fill="white", width=3)
            mark.create_line(24, 52, 38, 52, fill="white", width=3)
            title_box = tk.Frame(header, bg=colors["bg"])
            title_box.pack(side="left", fill="x", expand=True)
            tk.Label(title_box, text="Bangla Voice Type", bg=colors["bg"], fg=colors["text"],
                     font=("Segoe UI", 24, "bold")).pack(anchor="w")
            tk.Label(title_box, text="একটি অ্যাপ · system-wide বাংলা voice typing", bg=colors["bg"],
                     fg=colors["muted"], font=("Segoe UI", 11)).pack(anchor="w", pady=(2, 0))
            tk.Label(header, text="WINDOWS 11  ·  FREE", bg=colors["panel"], fg=colors["green"],
                     font=("Segoe UI", 9, "bold"), padx=14, pady=10,
                     highlightbackground=colors["line"], highlightthickness=1).pack(side="right", anchor="n")

            body = tk.Frame(root, bg=colors["bg"])
            body.pack(fill="both", expand=True, padx=26)
            body.grid_columnconfigure(0, weight=7)
            body.grid_columnconfigure(1, weight=4)
            body.grid_rowconfigure(0, weight=1)

            main_panel = tk.Frame(body, bg=colors["panel"], highlightbackground=colors["line"], highlightthickness=1)
            main_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
            side_panel = tk.Frame(body, bg=colors["panel"], highlightbackground=colors["line"], highlightthickness=1)
            side_panel.grid(row=0, column=1, sticky="nsew")

            language_names = {"bn-BD": "বাংলা (বাংলাদেশ)", "en-US": "English (US)", "hi-IN": "हिन्दी (भारत)"}
            language_codes = {v: k for k, v in language_names.items()}
            language_var = tk.StringVar(value=language_names.get(self.config.get("language", "bn-BD"), language_names["bn-BD"]))
            language_box = ttk.Combobox(main_panel, textvariable=language_var, values=list(language_codes),
                                        state="readonly", style="Dash.TCombobox", width=24)
            language_box.pack(anchor="nw", padx=22, pady=(22, 0))

            mic_canvas = tk.Canvas(main_panel, width=270, height=250, bg=colors["panel"], highlightthickness=0,
                                   cursor="hand2")
            mic_canvas.pack(pady=(3, 0))
            state_label = tk.Label(main_panel, text="", bg=colors["panel"], fg=colors["text"],
                                   font=("Segoe UI", 17, "bold"))
            state_label.pack(pady=(0, 3))
            instruction_label = tk.Label(main_panel, text="", bg=colors["panel"], fg=colors["muted"],
                                         font=("Segoe UI", 10))
            instruction_label.pack()
            tk.Label(main_panel, text="শুরু করতে microphone-এ ক্লিক করুন", bg=colors["panel"],
                     fg=colors["cyan"], font=("Segoe UI", 10, "bold")).pack(pady=(17, 5))

            last_drawn_state = [None]

            def draw_microphone():
                active = self.active
                accent = colors["red"] if active else colors["blue"]
                if last_drawn_state[0] != active:
                    mic_canvas.delete("all")
                    glow = "#552632" if active else "#123b68"
                    mic_canvas.create_oval(17, 8, 253, 244, outline=glow, width=3)
                    mic_canvas.create_oval(31, 22, 239, 230, outline=accent, width=2)
                    mic_canvas.create_oval(49, 40, 221, 212, fill=colors["panel2"], outline=colors["line"], width=2)
                    mic_canvas.create_oval(65, 56, 205, 196, fill=accent, outline="")
                    mic_canvas.create_oval(116, 77, 154, 129, fill="white", outline="")
                    mic_canvas.create_rectangle(116, 101, 154, 130, fill="white", outline="")
                    mic_canvas.create_line(104, 111, 104, 128, 111, 144, 135, 151, 159, 144, 166, 128, 166, 111,
                                           fill="white", width=5, smooth=True)
                    mic_canvas.create_line(135, 151, 135, 165, fill="white", width=5)
                    mic_canvas.create_line(120, 166, 150, 166, fill="white", width=5)
                    last_drawn_state[0] = active
                state_label.configure(text="শুনছি…" if active else "বন্ধ · প্রস্তুত",
                                      fg=colors["red"] if active else colors["text"])
                instruction_label.configure(text="বন্ধ করতে আবার ক্লিক করুন" if active else "আপনার কথা বলুন")

            mic_canvas.bind("<Button-1>", lambda _event: self.toggle_listening())

            tk.Label(side_panel, text="বর্তমান অবস্থা", bg=colors["panel"], fg=colors["text"],
                     font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(20, 12))
            live_status = tk.Label(side_panel, text="", bg=colors["panel2"], fg=colors["cyan"],
                                   font=("Segoe UI", 10, "bold"), padx=12, pady=10, anchor="w")
            live_status.pack(fill="x", padx=18)
            tk.Label(side_panel, text="একটি shortcut-এ চালু / বন্ধ", bg=colors["panel"], fg=colors["muted"],
                     font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(17, 2))
            hotkey_text = " + ".join(part.upper() for part in self.config.get("toggle_hotkey", "ctrl+shift+b").split("+"))
            hotkey_label = tk.Label(side_panel, text=hotkey_text, bg=colors["panel"], fg=colors["text"],
                                    font=("Segoe UI", 16, "bold"))
            hotkey_label.pack(anchor="w", padx=20, pady=(0, 16))
            settings_button = tk.Button(side_panel, text="⚙  সেটিংস খুলুন", command=self.open_settings,
                                        bg=colors["blue"], activebackground=colors["cyan"], activeforeground="white",
                                        fg="white", font=("Segoe UI", 10, "bold"), relief="flat",
                                        padx=14, pady=10, cursor="hand2")
            settings_button.pack(fill="x", padx=18, pady=(0, 16))
            tk.Label(side_panel, text="কাজ করে যেকোনো text field-এ\nলেখা cursor-এর জায়গায় বসে।",
                     bg=colors["panel"], fg=colors["muted"], font=("Segoe UI", 10), justify="left").pack(anchor="w", padx=20)
            tk.Label(side_panel, text="Speech recognition অনলাইনে Google-এর মাধ্যমে হয়।",
                     bg=colors["panel"], fg=colors["muted"], font=("Segoe UI", 8), wraplength=250,
                     justify="left").pack(anchor="w", padx=20, pady=(20, 8))

            footer = tk.Frame(root, bg=colors["panel2"], highlightbackground=colors["line"], highlightthickness=1)
            footer.pack(fill="x", padx=26, pady=(12, 18))
            footer_status = tk.Label(footer, text="●  SYSTEM-WIDE · READY", bg=colors["panel2"], fg=colors["green"],
                                     font=("Segoe UI", 9, "bold"), padx=14, pady=10)
            footer_status.pack(side="left")
            tk.Label(footer, text="Cursor যেখানে থাকবে, transcript সেখানেই paste হবে",
                     bg=colors["panel2"], fg=colors["muted"], font=("Segoe UI", 9)).pack(side="left", padx=(4, 8))

            def on_language_change(_event=None):
                selected = language_codes.get(language_var.get())
                if selected:
                    self.config["language"] = selected
                    try:
                        save_config(self.config)
                        self.last_status = "ভাষা সংরক্ষিত · " + language_var.get()
                    except Exception as e:
                        self.last_status = "ভাষা save হয়নি · " + str(e)
                        log("Language save failed: " + traceback.format_exc())

            language_box.bind("<<ComboboxSelected>>", on_language_change)

            def refresh_dashboard():
                if not root.winfo_exists():
                    return
                draw_microphone()
                live_status.configure(text=("●  MICROPHONE ON  ·  LISTENING" if self.active else "●  MICROPHONE OFF  ·  READY"),
                                      fg=colors["red"] if self.active else colors["cyan"])
                footer_status.configure(text="●  " + self.last_status.upper(),
                                        fg=colors["red"] if self.active else colors["green"])
                hotkey_text = " + ".join(part.upper() for part in self.config.get("toggle_hotkey", "ctrl+shift+b").split("+"))
                hotkey_label.configure(text=hotkey_text)
                root.after(450, refresh_dashboard)

            def close_dashboard():
                root.destroy()

            root.protocol("WM_DELETE_WINDOW", close_dashboard)
            self.dashboard_window = root
            refresh_dashboard()
            root.mainloop()
        except Exception:
            log("Dashboard error: " + traceback.format_exc())
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass
        finally:
            self.dashboard_window = None
            with self.dashboard_lock:
                self.dashboard_window_open = False

    def _settings_window(self):
        # Prevent the active shortcut from firing while the user is recording a new one.
        if self.hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self.hotkey_handle)
            except Exception:
                pass
            self.hotkey_handle = None

        old_config = self.config.copy()
        root = None
        try:
            root = tk.Tk()
            root.title("Bangla Voice Tray · Control Center")
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            window_width = min(840, max(680, int(screen_width * 0.72)))
            window_height = min(860, max(680, int(screen_height * 0.90)))
            root.geometry(f"{window_width}x{window_height}")
            root.minsize(640, 640)
            root.configure(bg="#08111f")
            root.resizable(True, True)
            try:
                root.attributes("-alpha", 0.985)
            except tk.TclError:
                pass

            colors = {
                "bg": "#08111f", "panel": "#101c2d", "panel2": "#1a2a40",
                "line": "#355072", "text": "#f8fbff", "muted": "#c2d0e0",
                "cyan": "#59d6ff", "blue": "#1677e8", "red": "#ff5668",
                "green": "#45dba2", "button": "#1677e8"
            }
            style = ttk.Style(root)
            style.theme_use("clam")
            style.configure("Dark.TCombobox", fieldbackground=colors["panel2"], background=colors["panel2"],
                            foreground=colors["text"], arrowcolor=colors["cyan"], bordercolor=colors["line"],
                            padding=7, selectbackground=colors["panel2"], selectforeground=colors["text"])
            style.map("Dark.TCombobox", fieldbackground=[("readonly", colors["panel2"])],
                      foreground=[("readonly", colors["text"])])
            style.configure("Dark.TCheckbutton", background=colors["panel"], foreground=colors["text"],
                            font=("Segoe UI", 10), padding=4)
            style.map("Dark.TCheckbutton", background=[("active", colors["panel"])],
                      foreground=[("active", colors["text"])])
            style.configure("Dark.TSpinbox", fieldbackground=colors["panel2"], background=colors["panel2"],
                            foreground=colors["text"], arrowcolor=colors["cyan"], bordercolor=colors["line"],
                            padding=7)

            def label(parent, text, size=10, color=None, weight="normal", **kwargs):
                return tk.Label(parent, text=text, bg=kwargs.pop("bg", colors["panel"]),
                                fg=color or colors["text"], font=("Segoe UI", size, weight), **kwargs)

            header = tk.Frame(root, bg=colors["bg"])
            header.pack(fill="x", padx=24, pady=(20, 14))
            tk.Label(header, text="●", bg=colors["bg"], fg=colors["cyan"], font=("Segoe UI", 25, "bold")).pack(side="left", padx=(0, 12))
            titles = tk.Frame(header, bg=colors["bg"])
            titles.pack(side="left", fill="x", expand=True)
            label(titles, "Bangla Voice Tray", 20, colors["text"], "bold", bg=colors["bg"]).pack(anchor="w")
            label(titles, "VOICE CONTROL CENTER  ·  বাংলা ভয়েস টাইপিং", 9, colors["muted"], bg=colors["bg"]).pack(anchor="w", pady=(2, 0))

            status_card = tk.Frame(root, bg=colors["panel"], highlightbackground=colors["line"], highlightthickness=1)
            status_card.pack(fill="x", padx=24, pady=(0, 12))
            status_text = "MICROPHONE ON  ·  LISTENING" if self.active else "MICROPHONE OFF  ·  READY"
            status_color = colors["red"] if self.active else colors["cyan"]
            status_badge = tk.Label(status_card, text="●  " + status_text, bg=colors["panel2"], fg=status_color,
                                    font=("Segoe UI", 10, "bold"), padx=12, pady=8)
            status_badge.pack(anchor="w", padx=14, pady=(13, 6))
            detail_label = label(status_card, self.last_status, 10, colors["muted"])
            detail_label.pack(anchor="w", padx=16, pady=(0, 13))

            card = tk.Frame(root, bg=colors["panel"], highlightbackground=colors["line"], highlightthickness=1)
            card.pack(fill="x", padx=24, pady=6)
            label(card, "SHORTCUT", 9, colors["cyan"], "bold").pack(anchor="w", padx=16, pady=(13, 2))
            label(card, "মাইক্রোফোন চালু / বন্ধ করার key বেছে নিন", 11, colors["text"], "bold").pack(anchor="w", padx=16)
            hotkey_var = tk.StringVar(value=self.config.get("toggle_hotkey", DEFAULTS["toggle_hotkey"]))
            hotkey_entry = tk.Entry(card, textvariable=hotkey_var, font=("Segoe UI", 12, "bold"),
                                    bg=colors["panel2"], fg=colors["text"], insertbackground=colors["cyan"],
                                    readonlybackground=colors["panel2"], relief="flat", justify="center")
            hotkey_entry.pack(fill="x", padx=16, pady=(9, 5), ipady=9)
            hotkey_entry.configure(state="readonly")
            hint = label(card, "বক্সে ক্লিক করে একটি key বা একসঙ্গে দুটি key চাপুন · যেমন F8, Ctrl + B, Ctrl + Shift", 9, colors["muted"])
            hint.pack(anchor="w", padx=16, pady=(0, 13))

            modifier_names = ((0x4, "ctrl"), (0x1, "shift"), (0x20000, "alt"))
            modifier_keys = {"shift_l": "shift", "shift_r": "shift", "control_l": "ctrl",
                             "control_r": "ctrl", "alt_l": "alt", "alt_r": "alt"}
            key_aliases = {"return": "enter", "escape": "esc", "prior": "page up", "next": "page down",
                           "backspace": "backspace", "caps_lock": "caps lock", "print": "print screen"}
            capture_pressed = []

            def capture_hotkey(event):
                raw_key = event.keysym.lower()
                key = modifier_keys.get(raw_key, key_aliases.get(raw_key, raw_key))
                if key not in capture_pressed:
                    capture_pressed.append(key)
                # Modifiers are listed first; other simultaneously held keys keep press order.
                active_modifiers = [name for mask, name in modifier_names if event.state & mask]
                if key in ("ctrl", "shift", "alt") and key not in active_modifiers:
                    active_modifiers.append(key)
                ordered = []
                for name in ("ctrl", "alt", "shift"):
                    if name in active_modifiers:
                        ordered.append(name)
                for name in capture_pressed:
                    if name not in ordered:
                        ordered.append(name)
                hotkey_var.set("+".join(ordered))
                return "break"

            def release_capture_key(event):
                raw_key = event.keysym.lower()
                key = modifier_keys.get(raw_key, key_aliases.get(raw_key, raw_key))
                if key in capture_pressed:
                    capture_pressed.remove(key)
                return "break"

            hotkey_entry.bind("<KeyPress>", capture_hotkey)
            hotkey_entry.bind("<KeyRelease>", release_capture_key)
            hotkey_entry.bind("<<Paste>>", lambda _event: "break")
            hotkey_entry.bind("<FocusIn>", lambda _event: hint.configure(text="এখন একটি key বা একসঙ্গে দুটি key চাপুন…", fg=colors["cyan"]))
            hotkey_entry.bind("<FocusOut>", lambda _event: hint.configure(text="বক্সে ক্লিক করে একটি key বা একসঙ্গে দুটি key চাপুন · যেমন F8, Ctrl + B, Ctrl + Shift", fg=colors["muted"]))

            options = tk.Frame(root, bg=colors["panel"], highlightbackground=colors["line"], highlightthickness=1)
            options.pack(fill="x", padx=24, pady=6)
            label(options, "PREFERENCES", 9, colors["cyan"], "bold").grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(13, 10))
            label(options, "ডিকটেশনের ভাষা", 10, colors["muted"]).grid(row=1, column=0, sticky="w", padx=16, pady=5)
            language_names = {"bn-BD": "বাংলা (বাংলাদেশ)", "en-US": "English (US)", "hi-IN": "हिन्दी (भारत)"}
            language_codes = {v: k for k, v in language_names.items()}
            language_var = tk.StringVar(value=language_names.get(self.config.get("language", "bn-BD"), language_names["bn-BD"]))
            language_box = ttk.Combobox(options, textvariable=language_var, values=list(language_codes),
                                        state="readonly", style="Dark.TCombobox", width=24)
            language_box.grid(row=1, column=1, sticky="e", padx=16, pady=5)
            label(options, "মাইক্রোফোন", 10, colors["muted"]).grid(row=2, column=0, sticky="w", padx=16, pady=5)
            device_names = ["System default"]
            device_indexes = {"System default": None}
            try:
                for index, name in enumerate(sr.Microphone.list_microphone_names()):
                    display = f"{index + 1}. {name}"
                    device_names.append(display)
                    device_indexes[display] = index
            except Exception as e:
                log("Microphone list unavailable: " + repr(e))
            selected_device = "System default"
            configured_index = self.config.get("microphone_device_index")
            if configured_index is not None:
                selected_device = next((name for name, index in device_indexes.items() if index == configured_index), "System default")
            device_var = tk.StringVar(value=selected_device)
            device_box = ttk.Combobox(options, textvariable=device_var, values=device_names,
                                      state="readonly", style="Dark.TCombobox", width=24)
            device_box.grid(row=2, column=1, sticky="e", padx=16, pady=5)
            label(options, "পেস্ট delay (সেকেন্ড)", 10, colors["muted"]).grid(row=3, column=0, sticky="w", padx=16, pady=5)
            delay_var = tk.StringVar(value=str(self.config.get("paste_delay", 0.15)))
            delay_box = ttk.Spinbox(options, textvariable=delay_var, from_=0.0, to=2.0, increment=0.05,
                                    style="Dark.TSpinbox", width=12)
            delay_box.grid(row=3, column=1, sticky="e", padx=16, pady=5)
            startup_var = tk.BooleanVar(value=self.config.get("start_with_windows", True))
            startup_button = tk.Button(options, command=lambda: toggle_startup(), relief="flat",
                                       font=("Segoe UI", 10, "bold"), anchor="w", padx=14, pady=11,
                                       cursor="hand2", bd=0)
            startup_button.grid(row=4, column=0, columnspan=2, sticky="ew", padx=12, pady=(7, 13))

            def refresh_startup_button():
                enabled = bool(startup_var.get())
                startup_button.configure(
                    text=("✓  Windows চালু হলে অ্যাপ চালু হবে  ·  চালু" if enabled
                          else "○  Windows চালু হলে অ্যাপ চালু হবে  ·  বন্ধ"),
                    bg=("#073d35" if enabled else "#273246"),
                    fg=("#62e6b7" if enabled else colors["muted"]),
                    activebackground=("#0b5145" if enabled else "#35445a"),
                    activeforeground=colors["text"])

            def toggle_startup():
                startup_var.set(not startup_var.get())
                refresh_startup_button()

            refresh_startup_button()
            options.grid_columnconfigure(0, weight=1)

            label(root, "Speech Recognition অনলাইনে Google-এর মাধ্যমে কাজ করে।", 9, colors["muted"], bg=colors["bg"]).pack(anchor="w", padx=26, pady=(8, 4))
            footer = tk.Frame(root, bg=colors["bg"])
            footer.pack(fill="x", padx=24, pady=(9, 16))
            save_button = tk.Button(footer, text="শর্টকাট ও সেটিংস সংরক্ষণ", command=lambda: save(), bg=colors["button"],
                                    activebackground="#1495eb", activeforeground="white", fg="white",
                                    font=("Segoe UI", 10, "bold"), relief="flat", padx=18, pady=10, cursor="hand2")
            save_button.pack(side="right")
            cancel_button = tk.Button(footer, text="বন্ধ করুন", command=lambda: close_settings(), bg=colors["panel2"],
                                      activebackground=colors["line"], activeforeground="white", fg=colors["text"],
                                      font=("Segoe UI", 10), relief="flat", padx=16, pady=10, cursor="hand2")
            cancel_button.pack(side="right", padx=(0, 8))

            def close_settings():
                if self.hotkey_handle is None:
                    self._register_hotkey()
                root.destroy()

            def restore_previous():
                self.config = old_config.copy()
                if self.hotkey_handle is not None:
                    try:
                        keyboard.remove_hotkey(self.hotkey_handle)
                    except Exception:
                        pass
                    self.hotkey_handle = None

            def save():
                new_hotkey = hotkey_var.get().strip().lower()
                if not new_hotkey:
                    messagebox.showerror("Shortcut required", "একটি key বা combination বেছে নিন।", parent=root)
                    return
                try:
                    delay = float(delay_var.get())
                    if not 0 <= delay <= 2:
                        raise ValueError("Paste delay 0 থেকে 2 সেকেন্ডের মধ্যে হতে হবে।")
                except ValueError as e:
                    messagebox.showerror("ভুল মান", str(e), parent=root)
                    return

                new_config = old_config.copy()
                new_config.update({
                    "toggle_hotkey": new_hotkey,
                    "language": language_codes.get(language_var.get(), "bn-BD"),
                    "microphone_device_index": device_indexes.get(device_var.get()),
                    "paste_delay": delay,
                    "start_with_windows": bool(startup_var.get())
                })
                self.config = new_config
                if not self._register_hotkey():
                    error = self.last_error
                    restore_previous()
                    self._register_hotkey()
                    if self.hotkey_handle is not None:
                        keyboard.remove_hotkey(self.hotkey_handle)
                        self.hotkey_handle = None
                    messagebox.showerror("Shortcut unavailable", "এই shortcut register করা যায়নি। অন্য একটি key বেছে নিন।\n\n" + error, parent=root)
                    return
                if not set_startup(new_config["start_with_windows"]):
                    restore_previous()
                    self._register_hotkey()
                    if self.hotkey_handle is not None:
                        keyboard.remove_hotkey(self.hotkey_handle)
                        self.hotkey_handle = None
                    messagebox.showerror("Startup setting failed", "Windows startup setting সংরক্ষণ করা যায়নি।", parent=root)
                    return
                try:
                    save_config(new_config)
                except Exception as e:
                    set_startup(old_config.get("start_with_windows", True))
                    restore_previous()
                    self._register_hotkey()
                    if self.hotkey_handle is not None:
                        keyboard.remove_hotkey(self.hotkey_handle)
                        self.hotkey_handle = None
                    messagebox.showerror("Save failed", "সেটিংস ফাইলে লেখা যায়নি।\n\n" + str(e), parent=root)
                    return

                self.last_status = "সেটিংস সংরক্ষিত · shortcut: " + new_hotkey
                root.destroy()

            root.protocol("WM_DELETE_WINDOW", close_settings)
            root.mainloop()
        except Exception:
            log("Settings window error: " + traceback.format_exc())
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass
        finally:
            if self.hotkey_handle is None:
                self._register_hotkey()
            with self.settings_lock:
                self.settings_window_open = False

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

    def run(self):
        menu = pystray.Menu(
            pystray.MenuItem("মাইক্রোফোন চালু/বন্ধ", self.toggle_listening, default=True),
            pystray.MenuItem("অবস্থা ও শর্টকাট দেখুন", self.show_status),
            pystray.MenuItem("সেটিংস…", self.open_settings),
            pystray.MenuItem("Windows startup চালু/বন্ধ", self.toggle_startup,
                             checked=lambda _item: bool(self.config.get("start_with_windows", True))),
            pystray.MenuItem("প্রস্থান", self.quit)
        )
        self.icon = pystray.Icon("BanglaVoiceTray", make_icon_image(self.active), APP_NAME, menu)
        self.icon.run()

if __name__ == "__main__":
    try:
        app = BanglaVoiceTray()
        app.run()
    except Exception:
        log(traceback.format_exc())
        raise




