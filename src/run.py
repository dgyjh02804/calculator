"""代数表达式计算器 - 启动入口
用法: cd src && python run.py
"""
import sys
import os

_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import tkinter as tk
from gui.app import AlgebraCalculatorGUI


def main():
    root = tk.Tk()
    app = AlgebraCalculatorGUI(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nProgram interrupted, exiting...")
        root.quit()


if __name__ == "__main__":
    main()
