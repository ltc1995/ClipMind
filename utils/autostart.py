import os
import sys
import winreg
APP_NAME = "ClipMind"
def get_registry_key() -> winreg.HKEYType:
    return winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
    )
def is_autostart_enabled() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        try:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return os.path.exists(value)
        finally:
            winreg.CloseKey(key)
    except FileNotFoundError:
        return False
def enable_autostart():
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'main.py')
        exe_path = f'"{pythonw}" "{script}"'
    try:
        key = get_registry_key()
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False
def disable_autostart():
    try:
        key = get_registry_key()
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False
