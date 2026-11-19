"""Register the bundled Qt and shiboken directories before importing PySide6."""

import os
import sys


if sys.platform == "win32" and getattr(sys, "frozen", False):
    for folder in ("PySide6", "shiboken6"):
        dll_dir = os.path.join(sys._MEIPASS, folder)
        if os.path.isdir(dll_dir):
            os.add_dll_directory(dll_dir)
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")

