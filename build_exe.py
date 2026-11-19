"""Build a portable Windows folder without collecting unrelated Qt/ICU DLLs."""

import os
import sys
from pathlib import Path


def main():
    # PyInstaller scans PATH when resolving native dependencies. The Codex
    # runtime's Poppler directory ships a different ICU build than Qt uses;
    # collecting it beside Qt6Core.dll makes the frozen app fail at import.
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    os.environ["PATH"] = os.pathsep.join(
        entry for entry in path_entries if "poppler" not in entry.lower()
    )

    from PyInstaller.__main__ import run

    args = [
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--noupx",
        "--distpath",
        "dist-v1.1.4-final",
        "--workpath",
        "build-v1.1.4-final",
        "--specpath",
        "build-v1.1.4-final",
        "--name",
        "BanglaVoiceTray",
        "--runtime-hook",
        "pyside_dll_path.py",
        "--collect-all",
        "pystray",
        "--collect-all",
        "speech_recognition",
        "--collect-all",
        "certifi",
        "main.py",
    ]

    # This managed Python runtime patches ssl.py to load an extra CA policy
    # file next to itself. Keep that policy file beside bundled ssl.py so
    # SSLContext construction does not fail in the frozen app.
    ssl_policy = Path(sys.base_prefix) / "Lib" / "codex-rejected-cas.pem"
    if ssl_policy.is_file():
        args.extend(["--add-data", f"{ssl_policy};."])

    run(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
