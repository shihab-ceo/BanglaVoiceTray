"""Register the bundled Qt and shiboken directories before importing PySide6."""

import os
import sys


# Keep these handles alive for the process lifetime. Closing a handle removes
# its directory from the Windows DLL search path.
_DLL_DIRECTORY_HANDLES = []

if sys.platform == "win32" and getattr(sys, "frozen", False):
    dll_dirs = []
    for folder in ("PySide6", "shiboken6"):
        dll_dir = os.path.join(sys._MEIPASS, folder)
        if os.path.isdir(dll_dir):
            _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(dll_dir))
            dll_dirs.append(dll_dir)

    if dll_dirs:
        os.environ["PATH"] = os.pathsep.join(dll_dirs + [os.environ.get("PATH", "")])

