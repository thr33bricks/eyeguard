import os
import sys
import platform
from pathlib import Path

APP_NAME = "EyeGuardAI"


# =========================================================
# PATH HELPERS
# =========================================================

def get_executable_path():
    """
    Returns executable path when bundled with PyInstaller,
    otherwise returns current script path.
    """
    if getattr(sys, 'frozen', False):
        return sys.executable

    return os.path.abspath(sys.argv[0])


def is_windows():
    return platform.system() == "Windows"


def is_linux():
    return platform.system() == "Linux"


# =========================================================
# LINUX AUTOSTART
# =========================================================

def linux_autostart_file():
    return Path.home() / ".config" / "autostart" / "eyeguardai.desktop"


def enable_autostart_linux():
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)

    exec_path = get_executable_path()

    desktop_entry = f"""[Desktop Entry]
Type=Application
Version=1.0
Name={APP_NAME}
Comment=Eye protection assistant
Exec="{exec_path}"
Terminal=false
X-GNOME-Autostart-enabled=true
"""

    autostart_file = linux_autostart_file()

    with open(autostart_file, "w") as f:
        f.write(desktop_entry)

    # Optional but recommended
    os.chmod(autostart_file, 0o755)


def disable_autostart_linux():
    file = linux_autostart_file()

    if file.exists():
        file.unlink()


def is_autostart_enabled_linux():
    return linux_autostart_file().exists()


# =========================================================
# WINDOWS AUTOSTART
# =========================================================

if is_windows():
    import winreg

    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def enable_autostart_windows():
    exe_path = get_executable_path()

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        RUN_KEY,
        0,
        winreg.KEY_SET_VALUE
    )

    winreg.SetValueEx(
        key,
        APP_NAME,
        0,
        winreg.REG_SZ,
        f'"{exe_path}"'
    )

    winreg.CloseKey(key)


def disable_autostart_windows():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_SET_VALUE
        )

        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)

    except FileNotFoundError:
        pass


def is_autostart_enabled_windows():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_READ
        )

        value, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)

        return bool(value)

    except FileNotFoundError:
        return False


# =========================================================
# UNIFIED API
# =========================================================

def enable_autostart():
    if is_windows():
        enable_autostart_windows()

    elif is_linux():
        enable_autostart_linux()


def disable_autostart():
    if is_windows():
        disable_autostart_windows()

    elif is_linux():
        disable_autostart_linux()


def is_autostart_enabled():
    if is_windows():
        return is_autostart_enabled_windows()

    elif is_linux():
        return is_autostart_enabled_linux()

    return False