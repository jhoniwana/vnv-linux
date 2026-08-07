#!/usr/bin/env python3
"""Inyector de teclado vía uinput (evdev) — funciona en cualquier compositor.

Uso: uikey.py [key1 key2 ...]   (ej: tab enter ctrl+f5)
Teclas: tab enter space esc f5 ctrl alt shift up down left right
"""
import sys
import time
from evdev import UInput, ecodes as e

KEYS = {
    "tab": e.KEY_TAB, "enter": e.KEY_ENTER, "space": e.KEY_SPACE,
    "esc": e.KEY_ESC, "f5": e.KEY_F5, "f4": e.KEY_F4, "f6": e.KEY_F6,
    "left": e.KEY_LEFT, "right": e.KEY_RIGHT, "up": e.KEY_UP, "down": e.KEY_DOWN,
    "home": e.KEY_HOME, "end": e.KEY_END, "backspace": e.KEY_BACKSPACE,
    "ctrl": e.KEY_LEFTCTRL, "alt": e.KEY_LEFTALT, "shift": e.KEY_LEFTSHIFT,
    "super": e.KEY_LEFTMETA, "a": e.KEY_A, "n": e.KEY_N, "p": e.KEY_P,
}


def main():
    args = sys.argv[1:] or ["enter"]
    ui = UInput()
    try:
        for arg in args:
            parts = arg.lower().split("+")
            down = []
            for p in parts:
                if p not in KEYS:
                    print(f"tecla desconocida: {p}")
                    return 1
                down.append(KEYS[p])
            for k in down:
                ui.write(e.EV_KEY, k, 1)
            ui.syn()
            time.sleep(0.02)
            for k in reversed(down):
                ui.write(e.EV_KEY, k, 0)
            ui.syn()
            time.sleep(0.08)
    finally:
        ui.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
