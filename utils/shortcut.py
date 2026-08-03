# ClipMind 全局快捷键模块
import ctypes
from PySide6.QtCore import QObject, QTimer, Signal
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12

class GlobalHotkey(QObject):
    activated = Signal()
    def __init__(self, hotkey_str="ctrl+shift+v", parent=None):
        super().__init__(parent)
        self._modifiers, self._vk = self._parse_hotkey(hotkey_str)
        self._pressed = False
        self._running = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)

    def _parse_hotkey(self, hotkey_str):
        parts = hotkey_str.lower().split("+")
        mod = 0
        vk = 0
        for part in parts:
            if part == "ctrl":
                mod |= MOD_CONTROL
            elif part == "shift":
                mod |= MOD_SHIFT
            elif part == "alt":
                mod |= MOD_ALT
            elif len(part) == 1 and "a" <= part <= "z":
                vk = ord(part.upper())
        return mod, vk or 0x56

    def register(self):
        if self._running: return
        self._pressed = False
        self._timer.start(150)
        self._running = True
        print("[ClipMind] 快捷键已生效: " + self._describe_hotkey())

    def unregister(self):
        self._timer.stop()
        self._running = False

    def _poll(self):
        getkey = ctypes.windll.user32.GetAsyncKeyState
        mod_down = True
        if self._modifiers & MOD_CONTROL:
            mod_down = mod_down and (getkey(VK_CONTROL) & 0x8000)
        if self._modifiers & MOD_SHIFT:
            mod_down = mod_down and (getkey(VK_SHIFT) & 0x8000)
        if self._modifiers & MOD_ALT:
            mod_down = mod_down and (getkey(VK_MENU) & 0x8000)
        key_down = getkey(self._vk) & 0x8000
        if mod_down and key_down and not self._pressed:
            self._pressed = True
            self.activated.emit()
        elif not (mod_down and key_down):
            self._pressed = False

    def _describe_hotkey(self):
        parts = []
        if self._modifiers & MOD_CONTROL: parts.append("Ctrl")
        if self._modifiers & MOD_SHIFT: parts.append("Shift")
        if self._modifiers & MOD_ALT: parts.append("Alt")
        if self._vk: parts.append(chr(self._vk))
        return "+".join(parts)
