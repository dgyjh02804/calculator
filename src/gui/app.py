"""代数表达式计算器 — 主 GUI 应用"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import re
import threading
import time
import os
import json
from datetime import datetime
from core.solver import AlgebraicCalculator
from gui.config import ConfigManager, LogManager, DebugCallback
from gui.widgets import LogViewerWindow, TestProgressWindow, TestSelectionDialog
from gui.test_data import get_test_categories


class AlgebraCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("代数表达式计算器 V2.0.2(稳定版) --------------------对数+高次方程 --------------------   构建时间: 6.5  ")
        # 根据屏幕分辨率自适应窗口大小
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # 窗口大小占屏幕的 75%，但不超过 1400x1000，不小于 900x650
        win_width = min(max(int(screen_width * 0.75), 900), 1400)
        win_height = min(max(int(screen_height * 0.75), 650), 1000)
        self.root.geometry(f"{win_width}x{win_height}")
        self.root.minsize(800, 600)

        # 创建计算器实例
        self.calculator = AlgebraicCalculator()

        # 存储历史记录
        self.history = []

        # 加载配置文件
        self.config_manager = ConfigManager("algebra_calculator_config.json")

        # Debug模式状态和级别（从配置文件加载）
        saved_level = self.config_manager.get("debug_level", 2)
        saved_enabled = self.config_manager.get("debug_enabled", True)
        self.debug_enabled = tk.BooleanVar(value=saved_enabled)
        self.debug_level = tk.IntVar(value=saved_level)
        self.debug_level_var = tk.StringVar(value=f"级别:{['无','简易','正常','详细'][saved_level]}")

        # 历史过滤
        self.history_filter_var = tk.BooleanVar(value=False)
        self._history_entries = []

        # 创建日志管理器
        self.log_manager = LogManager("logs/algebra_calculator.log")

        # 表达式化简测试（按子类别分组）
        self.expression_categories, self.equation_categories, self.other_categories = get_test_categories()


        # Debug回调
        self.debug_callback = None

        # 测试相关
        self.test_progress_window = None
        self.test_thread = None
        self.test_cancelled = False

        # 计算相关
        self.calculation_thread = None
        self.calculation_running = False

        # 设置样式
        self.setup_styles()

        # 创建GUI组件
        self.create_widgets()

        # 绑定键盘事件
        self.bind_events()

        # 初始化debug回调（使用配置文件中的速度设置）
        saved_speed = self.config_manager.get("debug_speed", "正常")
        self.debug_callback = DebugCallback(self.debug_text, self.debug_level.get(),
                                            display_speed=saved_speed)

        # 启动定时器处理debug消息队列
        self.process_debug_queue()

    def process_debug_queue(self):
        """定期处理debug消息队列，间隔和批量大小由速度设置决定"""
        if self.debug_callback:
            self.debug_callback.process_queue()
            # 更新待处理消息计数
            pending = self.debug_callback.get_pending_count()
            if pending > 0:
                self.debug_counter_var.set(f"{pending} 条待显示")
            elif self.debug_callback.lines:
                self.debug_counter_var.set(f"{len(self.debug_callback.lines)} 条信息")
        # 使用动态延迟
        delay = self.debug_callback.delay_ms if self.debug_callback else 100
        self.root.after(delay, self.process_debug_queue)

    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 配置按钮样式
        style.configure('Number.TButton', font=('Arial', 12), padding=5)
        style.configure('Operator.TButton', font=('Arial', 12, 'bold'), padding=5,
                        background='#e0e0e0')
        style.configure('Variable.TButton', font=('Arial', 12, 'italic'), padding=5,
                        background='#d0f0d0')
        style.configure('Equal.TButton', font=('Arial', 12, 'bold'), padding=5,
                        background='#4CAF50', foreground='white')
        style.configure('Clear.TButton', font=('Arial', 12), padding=5,
                        background='#f44336', foreground='white')
        style.configure('Solve.TButton', font=('Arial', 12, 'bold'), padding=5,
                        background='#2196F3', foreground='white')
        style.configure('Debug.TButton', font=('Arial', 12), padding=5,
                        background='#FF9800', foreground='white')
        style.configure('Log.TButton', font=('Arial', 12), padding=5,
                        background='#9C27B0', foreground='white')

    def create_widgets(self):
        """创建GUI组件"""
        # 主框架容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左右分栏：用 grid 实现等比缩放（避免 PanedWindow 的竖线问题）
        main_container.grid_columnconfigure(0, weight=65)
        main_container.grid_columnconfigure(1, weight=35)
        main_container.grid_rowconfigure(0, weight=1)

        left_panel = ttk.Frame(main_container)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 3))

        right_panel = ttk.Frame(main_container)
        right_panel.grid(row=0, column=1, sticky='nsew', padx=(3, 0))

        # 标题
        title_label = ttk.Label(left_panel, text="代数表达式计算器",
                                font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))

        # 控制面板
        control_frame = ttk.Frame(left_panel)
        control_frame.pack(fill=tk.X, pady=(0, 8))
        for c in range(5):
            control_frame.grid_columnconfigure(c, weight=1)

        # 设置按钮
        settings_btn = ttk.Button(control_frame, text="⚙ 设置",
                                  command=self.show_settings, style='Debug.TButton')
        settings_btn.grid(row=0, column=0, sticky='ew', padx=(0, 8))

        # 日志
        view_logs_btn = ttk.Button(control_frame, text="查看日志",
                                   command=self.view_logs, style='Log.TButton')
        view_logs_btn.grid(row=0, column=1, sticky='ew', padx=(0, 8))

        # 操作按钮
        clear_debug_btn = ttk.Button(control_frame, text="清Debug",
                                     command=self.clear_debug, style='Debug.TButton')
        clear_debug_btn.grid(row=0, column=2, sticky='ew', padx=(0, 3))
        clear_history_btn = ttk.Button(control_frame, text="清历史",
                                       command=self.clear_history)
        clear_history_btn.grid(row=0, column=3, sticky='ew', padx=(0, 3))
        run_tests_btn = ttk.Button(control_frame, text="测试",
                                   command=self.run_tests)
        run_tests_btn.grid(row=0, column=4, sticky='ew', padx=(0, 3))

        # 表达式输入框架
        expr_frame = ttk.LabelFrame(left_panel, text="输入表达式", padding=10)
        expr_frame.pack(fill=tk.X, pady=(0, 10))

        # 表达式输入框
        self.expression_var = tk.StringVar()
        self.expression_entry = ttk.Entry(expr_frame, textvariable=self.expression_var,
                                          font=('Arial', 12))
        self.expression_entry.pack(fill=tk.X, pady=(0, 10))

        # 操作按钮框架 - grid 等比缩放
        op_buttons_frame = ttk.Frame(expr_frame)
        op_buttons_frame.pack(fill=tk.X)
        for c in range(4):
            op_buttons_frame.grid_columnconfigure(c, weight=1)

        self.calc_btn = ttk.Button(op_buttons_frame, text="化简计算",
                                   command=self.calculate, style='Equal.TButton')
        self.calc_btn.grid(row=0, column=0, sticky='ew', padx=(0, 3))

        self.solve_btn = ttk.Button(op_buttons_frame, text="解方程",
                                    command=self.solve_equation, style='Solve.TButton')
        self.solve_btn.grid(row=0, column=1, sticky='ew', padx=(0, 3))

        self.factor_btn = ttk.Button(op_buttons_frame, text="因式分解",
                                     command=self.factor_expression, style='Solve.TButton')
        self.factor_btn.grid(row=0, column=2, sticky='ew', padx=(0, 3))

        clear_btn = ttk.Button(op_buttons_frame, text="清空输入",
                               command=self.clear_expression, style='Clear.TButton')
        clear_btn.grid(row=0, column=3, sticky='ew')

        # 结果显示框架
        result_frame = ttk.LabelFrame(left_panel, text="计算结果", padding=10)
        result_frame.pack(fill=tk.X, pady=(0, 10))

        self.result_text = scrolledtext.ScrolledText(result_frame, height=4,
                                                     font=('Arial', 12), wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 按钮面板
        buttons_frame = ttk.LabelFrame(left_panel, text="快速输入", padding=10)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

        # 数字按钮行
        num_frame = ttk.Frame(buttons_frame)
        num_frame.pack(fill=tk.X, pady=(0, 5))

        num_buttons = [
            ('7', 0), ('8', 1), ('9', 2), ('/', 3),
            ('4', 0), ('5', 1), ('6', 2), ('*', 3),
            ('1', 0), ('2', 1), ('3', 2), ('-', 3),
            ('0', 0), ('.', 1), ('^', 2), ('+', 3)
        ]

        for i in range(4):
            for j in range(4):
                idx = i * 4 + j
                if idx < len(num_buttons):
                    text, column = num_buttons[idx]
                    btn_frame = ttk.Frame(num_frame)
                    btn_frame.grid(row=i, column=j, padx=2, pady=2, sticky='nsew')

                    btn = ttk.Button(btn_frame, text=text, width=5,
                                     command=lambda t=text: self.append_to_expression(t))
                    if text in '+-*/^':
                        btn.configure(style='Operator.TButton')
                    else:
                        btn.configure(style='Number.TButton')
                    btn.pack(fill=tk.BOTH, expand=True)

        # 为数字按钮行配置网格权重
        for i in range(4):
            num_frame.grid_columnconfigure(i, weight=1)

        # 变量和括号按钮行
        var_frame = ttk.Frame(buttons_frame)
        var_frame.pack(fill=tk.X)

        var_buttons = ['x', 'y', 'z', 'a', 'b', 'c', '(', ')', '=', '√', 'log', '|']

        for col, text in enumerate(var_buttons):
            btn_frame = ttk.Frame(var_frame)
            btn_frame.grid(row=0, column=col, padx=2, pady=2, sticky='nsew')

            btn = ttk.Button(btn_frame, text=text, width=5,
                             command=lambda t=text: self.append_to_expression(t))
            if text.isalpha():
                btn.configure(style='Variable.TButton')
            elif text == '=':
                btn.configure(style='Solve.TButton')
            elif text == '√':
                btn.configure(style='Debug.TButton')
            else:
                btn.configure(style='Operator.TButton')
            btn.pack(fill=tk.BOTH, expand=True)

            var_frame.grid_columnconfigure(col, weight=1)

        # 历史记录框架
        history_frame = ttk.LabelFrame(left_panel, text="计算历史", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_text = scrolledtext.ScrolledText(history_frame, height=8,
                                                      font=('Courier New', 10))
        self.history_text.pack(fill=tk.BOTH, expand=True)

        # ========== 右侧面板：Debug信息 ==========

        # Debug信息框架
        debug_frame_main = ttk.LabelFrame(right_panel, text="Debug信息 - 计算过程跟踪", padding=10)
        debug_frame_main.pack(fill=tk.BOTH, expand=True)

        # Debug控制栏 - 仅状态和计数
        debug_control_frame = ttk.Frame(debug_frame_main)
        debug_control_frame.pack(fill=tk.X, pady=(0, 8))
        for c in range(2):
            debug_control_frame.grid_columnconfigure(c, weight=1)

        self.debug_status_var = tk.StringVar()
        self.debug_status_var.set("就绪")
        debug_status = ttk.Label(debug_control_frame, textvariable=self.debug_status_var,
                                 font=('Arial', 11, 'italic'), foreground='blue')
        debug_status.grid(row=0, column=0, sticky='w')

        self.debug_counter_var = tk.StringVar()
        self.debug_counter_var.set("0条")
        debug_counter = ttk.Label(debug_control_frame, textvariable=self.debug_counter_var,
                                  font=('Arial', 11))
        debug_counter.grid(row=0, column=1, sticky='e')

        # Debug信息文本区域
        self.debug_text = scrolledtext.ScrolledText(debug_frame_main,
                                                    font=('Consolas', 10),
                                                    wrap=tk.WORD,
                                                    bg='#f8f8f8',
                                                    relief=tk.SUNKEN,
                                                    borderwidth=1)
        self.debug_text.pack(fill=tk.BOTH, expand=True)

        # 状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)  # 修改这里：tk.Bottom -> tk.BOTTOM

        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 输入表达式或方程（如 x+2=5），Debug模式已启用，当前级别：正常")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        status_bar.pack(fill=tk.X)

    def show_settings(self):
        """打开设置弹窗"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.geometry("380x260")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # --- Debug 级别 ---
        ttk.Label(frame, text="Debug 级别:", font=('Arial', 11)).grid(row=0, column=0, sticky='w', pady=(0, 5))
        level_combo = ttk.Combobox(frame, values=["无", "简易", "正常", "详细"],
                                   state="readonly", width=10, font=('Arial', 11))
        level_names = ["无", "简易", "正常", "详细"]
        level_combo.current(self.debug_level.get())
        level_combo.grid(row=0, column=1, sticky='ew', pady=(0, 5))

        # --- Debug 速度 ---
        ttk.Label(frame, text="Debug 速度:", font=('Arial', 11)).grid(row=1, column=0, sticky='w', pady=(0, 5))
        speed_combo = ttk.Combobox(frame, values=["即时", "快速", "正常", "慢速", "逐条"],
                                   state="readonly", width=10, font=('Arial', 11))
        speed_names = ["即时", "快速", "正常", "慢速", "逐条"]
        saved_sp = self.config_manager.get("debug_speed", "正常")
        speed_combo.current(speed_names.index(saved_sp) if saved_sp in speed_names else 2)
        speed_combo.grid(row=1, column=1, sticky='ew', pady=(0, 5))

        # --- 历史过滤 ---
        ttk.Label(frame, text="计算历史:", font=('Arial', 11)).grid(row=2, column=0, sticky='w', pady=(0, 15))
        ttk.Checkbutton(frame, text="只显示出错的计算",
                        variable=self.history_filter_var,
                        command=self._refilter_history).grid(row=2, column=1, sticky='w')

        # --- 按钮 ---
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        def on_save():
            # 保存 Debug 级别
            selected_lv = level_combo.get()
            level = level_names.index(selected_lv)
            if level == 0:
                self.debug_enabled.set(False)
                self.debug_callback.text_widget = None
            else:
                self.debug_enabled.set(True)
                self.debug_callback.text_widget = self.debug_text
            self.debug_level.set(level)
            self.debug_callback.set_debug_level(level)
            self.debug_level_var.set(f"级别:{selected_lv}")
            self.config_manager.set("debug_level", level)
            self.config_manager.set("debug_enabled", level > 0)

            # 保存 Debug 速度
            selected_sp = speed_combo.get()
            self.debug_callback.set_display_speed(selected_sp)
            self.config_manager.set("debug_speed", selected_sp)

            level_text = "已禁用" if level == 0 else selected_lv
            sp_text = selected_sp
            self.status_var.set(f"Debug:{level_text} | 速度:{sp_text}")
            dialog.destroy()

        ttk.Button(btn_frame, text="保存", command=on_save).grid(row=0, column=0, sticky='ew', padx=(0, 5))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).grid(row=0, column=1, sticky='ew')

        dialog.wait_window()

    def set_debug_level(self, level):
        """设置debug级别"""
        self.debug_level.set(level)
        if self.debug_callback:
            self.debug_callback.set_debug_level(level)
        level_text = self._get_debug_level_text()
        self.debug_level_var.set(f"级别:{level_text}")
        if self.debug_enabled.get():
            self.status_var.set(f"Debug已启用，级别：{level_text}")
        else:
            self.status_var.set(f"Debug已禁用（级别：{level_text}）")
        self.config_manager.set("debug_speed", selected)

    def _get_debug_level_text(self):
        """获取debug级别的文本描述"""
        level = self.debug_level.get()
        if level == 0:
            return "无"
        elif level == 1:
            return "简易"
        elif level == 2:
            return "正常"
        elif level == 3:
            return "详细"
        else:
            return f"未知({level})"

    def bind_events(self):
        """绑定键盘事件"""
        self.root.bind('<Return>', lambda event: self.calculate())
        self.root.bind('<Escape>', lambda event: self.clear_expression())
        self.root.bind('<Control-e>', lambda event: self.solve_equation())
        self.root.bind('<Control-d>', lambda event: self.toggle_debug_mode())

        # 快捷键
        self.root.bind('<Control-l>', lambda event: self.clear_history())
        self.root.bind('<Control-t>', lambda event: self.run_tests())
        self.root.bind('<Control-c>', lambda event: self.clear_debug())
        self.root.bind('<Control-v>', lambda event: self.view_logs())  # 查看日志快捷键

        # Debug级别快捷键
        self.root.bind('<F1>', lambda event: self.set_debug_level(1))  # F1: 简易debug
        self.root.bind('<F2>', lambda event: self.set_debug_level(2))  # F2: 正常debug
        self.root.bind('<F3>', lambda event: self.set_debug_level(3))  # F3: 详细debug

    def toggle_debug_mode(self):
        """切换debug模式"""
        if self.debug_enabled.get():
            # 当前启用，切换到禁用
            self.debug_enabled.set(False)
            self.debug_status_var.set("Debug模式: 禁用")
            self.debug_level_var.set("级别:无")
            self.status_var.set("Debug模式已禁用")
            self.debug_callback.text_widget = None
        else:
            # 当前禁用，切换到启用（默认正常级别）
            self.debug_enabled.set(True)
            self.set_debug_level(2)  # 切换到正常级别
            self.debug_status_var.set("Debug模式: 启用")
            self.debug_callback.text_widget = self.debug_text
            self.status_var.set("Debug模式已启用，当前级别：正常")

    def clear_debug(self):
        """清空debug信息"""
        self.debug_text.delete(1.0, tk.END)
        self.debug_callback.clear()
        self.debug_counter_var.set("0 条信息")
        self.debug_status_var.set("已清空Debug信息")
        self.status_var.set("Debug信息已清空")

    def clear_history(self):
        """清空历史记录"""
        self.history_text.delete(1.0, tk.END)
        self.history = []
        self._history_entries = []
        self.status_var.set("已清空历史记录")

    def view_logs(self):
        """查看日志"""
        LogViewerWindow(self.root, self.log_manager)

    def append_to_expression(self, text):
        current = self.expression_var.get()
        cursor_pos = self.expression_entry.index(tk.INSERT)

        # 特殊处理带括号的函数
        if text == 'abs':
            text = 'abs()'
            new_text = current[:cursor_pos] + text + current[cursor_pos:]
            self.expression_var.set(new_text)
            new_pos = cursor_pos + 4
            self.expression_entry.icursor(new_pos)
        elif text == '√':
            # 插入 √()，光标放在括号内
            new_text = current[:cursor_pos] + '√()' + current[cursor_pos:]
            self.expression_var.set(new_text)
            self.expression_entry.icursor(cursor_pos + 2)
        elif text == 'log':
            # 插入 log(,)，光标放在逗号位置
            new_text = current[:cursor_pos] + 'log(,)' + current[cursor_pos:]
            self.expression_var.set(new_text)
            self.expression_entry.icursor(cursor_pos + 4)
        elif text == '|':
            # 插入成对的竖线，光标放在中间
            new_text = current[:cursor_pos] + '||' + current[cursor_pos:]
            self.expression_var.set(new_text)
            self.expression_entry.icursor(cursor_pos + 1)
        else:
            new_text = current[:cursor_pos] + text + current[cursor_pos:]
            self.expression_var.set(new_text)
            new_pos = cursor_pos + len(text)
            self.expression_entry.icursor(new_pos)

        self.expression_entry.focus()

    def clear_expression(self):
        """清空表达式输入框"""
        self.expression_var.set("")
        self.result_text.delete(1.0, tk.END)
        self.expression_entry.focus()
        self.status_var.set("已清空输入")

    def factor_expression(self):
        """因式分解：先化简表达式，再对结果进行因式分解"""
        expression = self.expression_var.get().strip()

        if not expression:
            messagebox.showwarning("输入为空", "请输入一个表达式")
            return

        if self._contains_chinese(expression):
            messagebox.showerror("输入错误", "表达式不能包含中文字符，请使用英文、数字和运算符。")
            return

        if ';' in expression:
            messagebox.showinfo("提示",
                              "因式分解不支持方程组，请使用解方程功能。\n"
                              "已自动转为解方程。")
            self.solve_equation()
            return

        if '=' in expression:
            messagebox.showinfo("提示",
                              "因式分解不支持方程，请只输入表达式。\n"
                              "已自动转为解方程。")
            self.solve_equation()
            return

        try:
            self.clear_debug()
            self.debug_status_var.set("正在因式分解...")
            level_text = self._get_debug_level_text()
            self.status_var.set(f"因式分解: {expression} (Debug级别: {level_text})")

            debug_cb = self.debug_callback if self.debug_enabled.get() else None
            if debug_cb:
                debug_cb(f"开始因式分解: {expression}", level=1)
                debug_cb(f"Debug级别: {level_text}", level=1)

            result = self.calculator.factor_expression(expression, debug_cb)

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result)

            if debug_cb:
                debug_lines = len(debug_cb.lines)
                self.debug_counter_var.set(f"{debug_lines} 条信息")

            self.add_to_history(f"[因式分解] {expression}")
            self.add_to_history(f"[结果]   {result}")
            self.add_to_history("-" * 60)

            self.log_manager.log_calculation(
                calculation_type="因式分解",
                expression=expression,
                result=result,
                debug_info=debug_cb,
                status="success"
            )

            self.status_var.set(f"因式分解完成: {result[:50]}...")
            self.debug_status_var.set("完成")

        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
        except Exception as e:
            import traceback
            err_msg = f"因式分解失败: {str(e)}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, err_msg)
            self.status_var.set(f"因式分解出错: {str(e)}")
            self.debug_status_var.set("出错")
            if self.debug_callback:
                self.debug_callback(f"因式分解出错: {str(e)}", level=1)
                self.debug_callback(traceback.format_exc(), level=1)

    def _contains_chinese(self, text):
        """检查字符串是否包含中文字符"""
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff':
                return True
        return False

    def calculate(self):
        """计算或化简表达式（含方程组处理）"""
        if self.calculation_running:
            messagebox.showinfo("计算中", "当前正在计算中，请稍候...")
            return

        expression = self.expression_var.get().strip()

        if not expression:
            messagebox.showwarning("输入为空", "请输入一个表达式")
            return

        if self._contains_chinese(expression):
            messagebox.showerror("输入错误", "表达式不能包含中文字符，请使用英文、数字和运算符。")
            return

        # ===== 新增：处理方程组（包含分号） =====
        if ';' in expression:
            # 方程组统一调用 _solve_system（可能弹出对话框）
            try:
                self.clear_debug()
                self.debug_status_var.set("正在解方程组...")
                level_text = self._get_debug_level_text()
                self.status_var.set(f"解方程组: {expression} (Debug级别: {level_text})")

                self.calc_btn.config(state=tk.DISABLED, text="计算中...")
                self.solve_btn.config(state=tk.DISABLED)

                debug_cb = self.debug_callback if self.debug_enabled.get() else None
                if debug_cb:
                    debug_cb(f"开始解方程组: {expression}", level=1)
                    debug_cb(f"Debug级别: {level_text}", level=1)

                result = self._solve_system(expression, debug_cb)

                if result == "已取消":
                    self.debug_status_var.set("求解已取消")
                    self.status_var.set("方程组求解已取消")
                    return

                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, result)

                if debug_cb:
                    self.debug_counter_var.set(f"{len(debug_cb.lines)} 条信息")

                self.add_to_history(f"[方程组] {expression}")
                self.add_to_history(f"[解]   {result}")
                self.add_to_history("-" * 60)

                self.log_manager.log_calculation(
                    calculation_type="方程组求解",
                    expression=expression,
                    result=result,
                    debug_info=debug_cb,
                    status="success"
                )

                self.debug_status_var.set("方程组求解完成")
                self.status_var.set(f"方程组求解完成: {expression}")

            except Exception as e:
                self._handle_calculation_error(expression, str(e))
            finally:
                self.calc_btn.config(state=tk.NORMAL, text="化简计算")
                self.solve_btn.config(state=tk.NORMAL)
            return  # 直接返回，不进入化简分支

        # ===== 原有表达式化简处理（不含等号） =====
        if '=' not in expression:
            # 启动后台计算线程（与原来相同）
            try:
                self.clear_debug()
                self.debug_status_var.set("正在计算...")
                level_text = self._get_debug_level_text()
                self.status_var.set(f"计算: {expression} (Debug级别: {level_text})")

                self.calc_btn.config(state=tk.DISABLED, text="计算中...")
                self.solve_btn.config(state=tk.DISABLED)

                debug_cb = self.debug_callback if self.debug_enabled.get() else None
                if debug_cb:
                    debug_cb(f"开始计算表达式: {expression}", level=1)
                    debug_cb(f"Debug级别: {level_text}", level=1)

                self.calculation_running = True
                self.calculation_thread = threading.Thread(
                    target=self._calculate_thread,
                    args=(expression, debug_cb),
                    daemon=True
                )
                self.calculation_thread.start()
            except Exception as e:
                self._handle_calculation_error(expression, str(e))
        else:
            # 单个方程，调用解方程流程（可能启动后台线程）
            self.solve_equation()  # 直接调用解方程方法

    def _calculate_thread(self, expression, debug_cb):
        """后台计算线程"""
        try:
            # 计算表达式
            result = self.calculator.simplify_expression(expression, debug_cb)

            # 在主线程中更新结果
            self.root.after(0, self._calculation_complete, expression, result, debug_cb)

        except Exception as e:
            # 在主线程中处理错误
            self.root.after(0, self._calculation_error, expression, str(e), debug_cb)

    def _calculation_complete(self, expression, result, debug_cb):
        """计算完成后的处理"""
        try:
            # 记录计算完成（使用级别1 - 简易debug）
            if debug_cb:
                debug_cb(f"计算完成，结果: {result}", level=1)

            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result)

            # 更新debug信息计数器
            if debug_cb:
                debug_lines = len(debug_cb.lines)
                self.debug_counter_var.set(f"{debug_lines} 条信息")

            # 添加到历史记录
            self.add_to_history(f"[表达式] {expression}")
            self.add_to_history(f"[结果]   {result}")
            self.add_to_history("-" * 60)

            # 记录到日志
            self.log_manager.log_calculation(
                calculation_type="表达式化简",
                expression=expression,
                result=result,
                debug_info=debug_cb,
                status="success"
            )

            # 更新状态
            self.debug_status_var.set("计算完成")
            self.status_var.set(f"计算完成: {expression}")

        except Exception as e:
            self._handle_calculation_error(expression, str(e))
        finally:
            # 重新启用计算按钮
            self.calc_btn.config(state=tk.NORMAL, text="化简计算")
            self.solve_btn.config(state=tk.NORMAL)
            self.calculation_running = False

    def _calculation_error(self, expression, error_msg, debug_cb):
        """计算错误处理"""
        try:
            # 记录错误到debug（使用级别1 - 简易debug）
            if debug_cb:
                debug_cb(f"计算出错: {error_msg}", level=1)

            # 显示错误结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, f"错误: {error_msg}")

            # 添加到历史记录（错误）
            self.add_to_history(f"[表达式] {expression}")
            self.add_to_history(f"[错误]   {error_msg}")
            self.add_to_history("-" * 60)

            # 记录错误到日志
            self.log_manager.log_calculation(
                calculation_type="表达式化简",
                expression=expression,
                result=error_msg,
                debug_info=debug_cb,
                status="error",
                error_msg=error_msg
            )

            self.debug_status_var.set("计算出错")
            self.status_var.set(f"计算出错: {error_msg}")

            # 显示错误消息框
            messagebox.showerror("计算错误", error_msg)

        finally:
            # 重新启用计算按钮
            self.calc_btn.config(state=tk.NORMAL, text="化简计算")
            self.solve_btn.config(state=tk.NORMAL)
            self.calculation_running = False

    def _handle_calculation_error(self, expression, error_msg):
        """处理计算错误"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, f"错误: {error_msg}")

        # 添加到历史记录（错误）
        self.add_to_history(f"[表达式] {expression}")
        self.add_to_history(f"[错误]   {error_msg}")
        self.add_to_history("-" * 60)

        # 记录错误到日志
        self.log_manager.log_calculation(
            calculation_type="表达式化简",
            expression=expression,
            result=error_msg,
            debug_info=self.debug_callback,
            status="error",
            error_msg=error_msg
        )

        self.debug_status_var.set("计算出错")
        self.status_var.set(f"计算出错: {error_msg}")

        # 显示错误消息框
        messagebox.showerror("计算错误", error_msg)

        # 重新启用计算按钮
        self.calc_btn.config(state=tk.NORMAL, text="化简计算")
        self.solve_btn.config(state=tk.NORMAL)
        self.calculation_running = False

    def solve_equation(self):
        """解方程（含方程组处理）"""
        if self.calculation_running:
            messagebox.showinfo("计算中", "当前正在计算中，请稍候...")
            return

        expression = self.expression_var.get().strip()

        if not expression:
            messagebox.showwarning("输入为空", "请输入一个方程（包含等号）")
            return

        if '=' not in expression:
            messagebox.showinfo("提示", "方程应包含等号。已自动进行化简计算。")
            self.calculate()
            return

        if self._contains_chinese(expression):
            messagebox.showerror("输入错误", "方程不能包含中文字符，请使用英文、数字和运算符。")
            return

        # ===== 处理方程组（包含分号） =====
        if ';' in expression:
            try:
                self.clear_debug()
                self.debug_status_var.set("正在解方程组...")
                level_text = self._get_debug_level_text()
                self.status_var.set(f"解方程组: {expression} (Debug级别: {level_text})")

                self.calc_btn.config(state=tk.DISABLED)
                self.solve_btn.config(state=tk.DISABLED, text="求解中...")

                debug_cb = self.debug_callback if self.debug_enabled.get() else None
                if debug_cb:
                    debug_cb(f"开始解方程组: {expression}", level=1)
                    debug_cb(f"Debug级别: {level_text}", level=1)

                result = self._solve_system(expression, debug_cb)

                if result == "已取消":
                    self.debug_status_var.set("求解已取消")
                    self.status_var.set("方程组求解已取消")
                    return

                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, result)

                if debug_cb:
                    self.debug_counter_var.set(f"{len(debug_cb.lines)} 条信息")

                self.add_to_history(f"[方程组] {expression}")
                self.add_to_history(f"[解]   {result}")
                self.add_to_history("-" * 60)

                self.log_manager.log_calculation(
                    calculation_type="方程组求解",
                    expression=expression,
                    result=result,
                    debug_info=debug_cb,
                    status="success"
                )

                self.debug_status_var.set("方程组求解完成")
                self.status_var.set(f"方程组求解完成: {expression}")

            except Exception as e:
                self._handle_solve_error(expression, str(e))
            finally:
                self.calc_btn.config(state=tk.NORMAL)
                self.solve_btn.config(state=tk.NORMAL, text="解方程")
            return

        # ===== 单个方程处理（后台线程） =====
        try:
            self.clear_debug()
            self.debug_status_var.set("正在解方程...")
            level_text = self._get_debug_level_text()
            self.status_var.set(f"解方程: {expression} (Debug级别: {level_text})")

            self.calc_btn.config(state=tk.DISABLED)
            self.solve_btn.config(state=tk.DISABLED, text="求解中...")

            debug_cb = self.debug_callback if self.debug_enabled.get() else None
            if debug_cb:
                debug_cb(f"开始解方程: {expression}", level=1)
                debug_cb(f"Debug级别: {level_text}", level=1)

            self.calculation_running = True
            self.calculation_thread = threading.Thread(
                target=self._solve_equation_thread,
                args=(expression, debug_cb),
                daemon=True
            )
            self.calculation_thread.start()

        except Exception as e:
            self._handle_solve_error(expression, str(e))

    def _solve_equation_thread(self, expression, debug_cb):
        """后台解方程线程"""
        try:
            # 解方程
            result = self.calculator.simplify_expression(expression, debug_cb)

            # 在主线程中更新结果
            self.root.after(0, self._solve_complete, expression, result, debug_cb)

        except Exception as e:
            # 在主线程中处理错误
            self.root.after(0, self._solve_error, expression, str(e), debug_cb)

    def _solve_complete(self, expression, result, debug_cb):
        """解方程完成后的处理"""
        try:
            # 记录方程求解完成（使用级别1 - 简易debug）
            if debug_cb:
                debug_cb(f"方程求解完成，结果: {result}", level=1)

            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result)

            # 更新debug信息计数器
            if debug_cb:
                debug_lines = len(debug_cb.lines)
                self.debug_counter_var.set(f"{debug_lines} 条信息")

            # 添加到历史记录
            self.add_to_history(f"[方程] {expression}")
            self.add_to_history(f"[解]   {result}")
            self.add_to_history("-" * 60)

            # 记录到日志
            self.log_manager.log_calculation(
                calculation_type="方程求解",
                expression=expression,
                result=result,
                debug_info=debug_cb,
                status="success"
            )

            # 更新状态
            self.debug_status_var.set("解方程完成")
            self.status_var.set(f"方程求解完成: {expression}")

        except Exception as e:
            self._handle_solve_error(expression, str(e))
        finally:
            # 重新启用计算按钮
            self.calc_btn.config(state=tk.NORMAL)
            self.solve_btn.config(state=tk.NORMAL, text="解方程")
            self.calculation_running = False

    def _solve_error(self, expression, error_msg, debug_cb):
        """解方程错误处理"""
        try:
            # 记录错误到debug（使用级别1 - 简易debug）
            if debug_cb:
                debug_cb(f"解方程出错: {error_msg}", level=1)

            # 显示错误结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, f"解方程错误: {error_msg}")

            # 添加到历史记录（错误）
            self.add_to_history(f"[方程] {expression}")
            self.add_to_history(f"[错误] {error_msg}")
            self.add_to_history("-" * 60)

            # 记录错误到日志
            self.log_manager.log_calculation(
                calculation_type="方程求解",
                expression=expression,
                result=error_msg,
                debug_info=debug_cb,
                status="error",
                error_msg=error_msg
            )

            self.debug_status_var.set("解方程出错")
            self.status_var.set(f"解方程出错: {error_msg}")

            # 显示错误消息框
            messagebox.showerror("解方程错误", error_msg)

        finally:
            # 重新启用计算按钮
            self.calc_btn.config(state=tk.NORMAL)
            self.solve_btn.config(state=tk.NORMAL, text="解方程")
            self.calculation_running = False

    def _handle_solve_error(self, expression, error_msg):
        """处理解方程错误"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, f"解方程错误: {error_msg}")

        # 添加到历史记录（错误）
        self.add_to_history(f"[方程] {expression}")
        self.add_to_history(f"[错误] {error_msg}")
        self.add_to_history("-" * 60)

        # 记录错误到日志
        self.log_manager.log_calculation(
            calculation_type="方程求解",
            expression=expression,
            result=error_msg,
            debug_info=self.debug_callback,
            status="error",
            error_msg=error_msg
        )

        self.debug_status_var.set("解方程出错")
        self.status_var.set(f"解方程出错: {error_msg}")

        # 显示错误消息框
        messagebox.showerror("解方程错误", error_msg)

        # 重新启用计算按钮
        self.calc_btn.config(state=tk.NORMAL)
        self.solve_btn.config(state=tk.NORMAL, text="解方程")
        self.calculation_running = False

    def _solve_system(self, expr, debug_callback=None):
        """处理联立方程组，弹出变量选择对话框（若欠定），然后调用核心求解器"""
        try:
            eq_strings = [e.strip() for e in expr.split(';') if e.strip()]
            # 提取所有变量（简单方法：从每个方程中收集字母）
            import re
            all_vars = set()
            for eq_str in eq_strings:
                vars_in_eq = re.findall(r'[a-zA-Z]', eq_str)
                all_vars.update(vars_in_eq)
            all_vars = sorted(all_vars)
            n = len(eq_strings)
            m = len(all_vars)

            if n < m:
                # 欠定，需要用户选择变量
                selected = self._select_variables_for_system(all_vars, n)
                if selected is None:
                    return "已取消"
                solve_vars = selected
            else:
                solve_vars = all_vars

            # 调用核心求解
            result = self.calculator.solve_system(expr, solve_vars, debug_callback)
            return result
        except Exception as e:
            return f"方程组求解错误: {str(e)}"

    def _select_variables_for_system(self, all_vars, need_count):
        """弹出对话框让用户选择 need_count 个变量"""
        import tkinter as tk
        from tkinter import messagebox, ttk

        dialog = tk.Toplevel(self.root)
        dialog.title("选择求解变量")
        dialog.geometry("450x200")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        label = ttk.Label(dialog,
                          text=f"方程组有 {len(all_vars)} 个变量，方程有 {need_count} 个。\n请选择 {need_count} 个变量进行求解（用逗号分隔）：",
                          justify=tk.LEFT)
        label.pack(pady=15, padx=20)

        entry_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=entry_var, width=40)
        entry.pack(pady=5, padx=20)
        entry.focus_set()

        result = [None]

        def on_ok():
            input_str = entry_var.get().strip()
            selected = [v.strip() for v in input_str.split(',') if v.strip()]
            if len(selected) != need_count:
                messagebox.showerror("错误", f"请选择 {need_count} 个变量，当前选择了 {len(selected)} 个")
                return
            if not all(v in all_vars for v in selected):
                invalid = [v for v in selected if v not in all_vars]
                messagebox.showerror("错误", f"变量 {', '.join(invalid)} 不存在于方程中")
                return
            result[0] = selected
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="确定", command=on_ok, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=on_cancel, width=10).pack(side=tk.LEFT, padx=10)

        # 预填充所有变量（方便用户修改）
        entry_var.set(', '.join(all_vars))

        dialog.wait_window()
        return result[0]

    def add_to_history(self, text, is_error=False):
        """添加文本到历史记录。is_error=True 表示该条目是出错/失败的记录"""
        self.history.append(text)
        self._history_entries.append((text, is_error))
        if self.history_filter_var.get() and not is_error:
            return
        self.history_text.insert(tk.END, text + "\n")
        self.history_text.see(tk.END)

    def _refilter_history(self):
        """根据过滤勾选框刷新历史显示"""
        self.history_text.delete(1.0, tk.END)
        for text, is_error in self._history_entries:
            if self.history_filter_var.get() and not is_error:
                continue
            self.history_text.insert(tk.END, text + "\n")
        self.history_text.see(tk.END)

    def run_tests(self):
        """运行测试用例 - 弹出选择对话框，运行所选类别的测试"""
        if self.test_thread and self.test_thread.is_alive():
            if messagebox.askyesno("测试正在运行", "测试正在运行中，是否重新开始？"):
                self.test_cancelled = True
                self.test_thread.join(timeout=1.0)
            else:
                return

        # 弹出选择对话框
        dlg = TestSelectionDialog(self.root, self.expression_categories,
                                  self.equation_categories, self.other_categories)
        result = dlg.show()
        if result is None:
            return
        expr_selected, eq_selected, other_selected = result
        if expr_selected is None and eq_selected is None and other_selected is None:
            return  # 用户取消

        # 根据选择构建测试列表
        all_tests = []

        # 添加表达式测试
        for sub in expr_selected:
            for item in self.expression_categories[sub]:
                if len(item) == 2:
                    test_input, expected = item
                    all_tests.append(("表达式", test_input, expected))
                else:
                    test_input, expected, solve_vars = item
                    all_tests.append(("表达式", test_input, expected, solve_vars))

        # 添加方程测试
        for sub in eq_selected:
            for item in self.equation_categories[sub]:
                if len(item) == 2:
                    test_input, expected = item
                    all_tests.append(("方程", test_input, expected))
                else:
                    test_input, expected, solve_vars = item
                    all_tests.append(("方程", test_input, expected, solve_vars))

        # 添加其他测试（因式分解等）
        for sub in other_selected:
            for item in self.other_categories[sub]:
                if len(item) == 2:
                    test_input, expected = item
                    all_tests.append(("其他", test_input, expected, None))
                else:
                    test_input, expected, third = item
                    # third 可以是 list（求解变量）或 str（模式：simplify/factor）
                    all_tests.append(("其他", test_input, expected, third))

        if not all_tests:
            messagebox.showinfo("无测试", "所选类别中没有测试用例")
            return

        # 清空debug信息
        self.clear_debug()

        # 重置取消标志
        self.test_cancelled = False

        # 创建进度窗口
        self.test_progress_window = TestProgressWindow(self.root)

        # 启动测试线程
        self.test_thread = threading.Thread(target=self._run_tests_thread,
                                            args=(all_tests,),
                                            daemon=True)
        self.test_thread.start()

    def _are_solutions_equivalent(self, expected, actual, test_type):
        """判断两个解字符串是否数学等价

        策略：
        1. 用计算器自身的解析+化简归一化表达式值，消除格式差异（如 √(1/2) vs (√2)/2）
        2. 对复杂表达式用 sympy 精确比较
        """
        import re

        def _normalize_value(val_str):
            """用计算器规范化单个表达式的字符串形式"""
            try:
                expr = self.calculator.parse_expression(val_str)
                if hasattr(expr, 'simplify'):
                    simplified = expr.simplify()
                    s = str(simplified)
                    # 清理显示格式
                    s = s.replace('+-', '-').replace('--', '+')
                    return s
            except Exception:
                pass
            return val_str

        def _values_match(e_val, a_val):
            """比较两个变量值是否数学等价"""
            # 快速路径：完全相同
            if e_val == a_val:
                return True
            # 归一化后比较
            e_norm = _normalize_value(e_val)
            a_norm = _normalize_value(a_val)
            if e_norm == a_norm:
                return True
            # sympy 精确比较
            try:
                import sympy as sp
                e_s = e_norm.replace(' ', '')
                a_s = a_norm.replace(' ', '')
                # 转换 √(...) → sqrt(...)
                while '√(' in e_s:
                    e_s = re.sub(r'√\(([^()]+)\)', r'sqrt(\1)', e_s)
                while '√(' in a_s:
                    a_s = re.sub(r'√\(([^()]+)\)', r'sqrt(\1)', a_s)
                e_s = e_s.replace('^', '**')
                a_s = a_s.replace('^', '**')
                e_s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', e_s)
                a_s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', a_s)
                e_expr = sp.sympify(e_s)
                a_expr = sp.sympify(a_s)
                return sp.simplify(e_expr - a_expr) == 0
            except Exception:
                return False

        def _parse_pairs(line):
            """解析 'var = val, var = val' 格式"""
            pairs = {}
            for pair in re.split(r',\s*', line):
                if '=' in pair:
                    var, val = pair.split('=', 1)
                    pairs[var.strip()] = val.strip()
            return pairs

        # 归一化分隔符
        expected = expected.replace(' 或 ', '\n').replace('或 ', '\n').replace(' 或', '\n')
        actual = actual.replace(' 或 ', '\n').replace('或 ', '\n').replace(' 或', '\n')

        # 无解/恒等类型的模糊匹配
        _no_sol = ('无解', '矛盾方程', '无法求解', '无法显示', '目前不支持', '无穷多解', '恒等式')
        if any(expected.startswith(p) for p in _no_sol) and any(actual.startswith(p) for p in _no_sol):
            return True

        # 按"或"拆分解组
        exp_groups = [g.strip() for g in expected.split('\n') if g.strip()]
        act_groups = [g.strip() for g in actual.split('\n') if g.strip()]

        # 单解组：直接比较变量值
        if len(exp_groups) == 1 and len(act_groups) == 1:
            exp_pairs = _parse_pairs(exp_groups[0])
            act_pairs = _parse_pairs(act_groups[0])
            if not exp_pairs or not act_pairs:
                return expected.strip() == actual.strip()
            for var in exp_pairs:
                if var not in act_pairs:
                    return False
                if not _values_match(exp_pairs[var], act_pairs[var]):
                    return False
            return True

        # 多解组：数量必须一致
        if len(exp_groups) != len(act_groups):
            return False

        # 对每个期望解组，找到匹配的实际解组
        matched_act = set()
        for exp_group in exp_groups:
            exp_pairs = _parse_pairs(exp_group)
            found = False
            for j, act_group in enumerate(act_groups):
                if j in matched_act:
                    continue
                act_pairs = _parse_pairs(act_group)
                if not exp_pairs or not act_pairs:
                    if exp_group == act_group:
                        matched_act.add(j)
                        found = True
                        break
                    continue
                # 比较共同的变量
                common = set(exp_pairs.keys()) & set(act_pairs.keys())
                if not common:
                    continue
                all_match = True
                for var in common:
                    if not _values_match(exp_pairs[var], act_pairs[var]):
                        all_match = False
                        break
                if all_match:
                    matched_act.add(j)
                    found = True
                    break
            if not found:
                return False
        return True

    def _run_tests_thread(self, all_tests):
        """在后台线程中运行指定的测试用例列表"""
        try:
            debug_cb = self.debug_callback if self.debug_enabled.get() else None
            total_tests = len(all_tests)
            passed = 0
            failed = 0

            # 记录测试开始
            if debug_cb:
                debug_cb(f"开始运行测试，总计 {total_tests} 个测试用例", level=1)

            for i, test_data in enumerate(all_tests):
                if self.test_cancelled:
                    break

                # 兼容两种格式： (类型, 输入, 期望) 或 (类型, 输入, 期望, 模式/求解变量)
                if len(test_data) == 3:
                    test_type, test_input, expected = test_data
                    solve_vars = None
                    mode = None
                else:
                    test_type, test_input, expected, mode_or_vars = test_data
                    if isinstance(mode_or_vars, list):
                        solve_vars = mode_or_vars
                        mode = None
                    elif isinstance(mode_or_vars, str):
                        solve_vars = None
                        mode = mode_or_vars
                    else:
                        solve_vars = None
                        mode = None

                progress = (i + 1) / total_tests * 100
                self.root.after(0, self._update_test_progress, progress, i + 1, total_tests, test_input)

                try:
                    if debug_cb:
                        debug_cb(f"正在测试 ({i + 1}/{total_tests}): {test_input}", level=1)

                    # 判断测试类型，调用对应的计算方法
                    if mode == "factor":
                        result = self.calculator.factor_expression(test_input, debug_cb)
                    elif mode == "simplify":
                        result = self.calculator.simplify_expression(test_input, debug_cb)
                    elif isinstance(solve_vars, list):
                        # solve_vars 列表 → 调用 solve_system
                        result = self.calculator.solve_system(test_input, solve_vars, debug_cb)
                    elif ';' in test_input and solve_vars is not None:
                        result = self.calculator.solve_system(test_input, solve_vars, debug_cb)
                    elif test_type == "其他":
                        result = self.calculator.factor_expression(test_input, debug_cb)
                    else:
                        result = self.calculator.simplify_expression(test_input, debug_cb)

                    # 去除外层括号（如果无运算符）
                    if result.startswith('(') and result.endswith(')'):
                        inner = result[1:-1]
                        if not any(op in inner for op in '+-'):
                            result = inner

                    is_correct = self._are_solutions_equivalent(expected, result, test_type)

                    if debug_cb:
                        if is_correct:
                            debug_cb(f"测试通过: {test_input} → {result}", level=1)
                        else:
                            debug_cb(f"测试失败: {test_input}，期望: {expected}，实际: {result}", level=1)

                    self.log_manager.log_calculation(
                        calculation_type=f"测试-{test_type}",
                        expression=test_input,
                        result=result,
                        debug_info=debug_cb if is_correct else None,
                        status="success" if is_correct else "error"
                    )

                    if is_correct:
                        self.root.after(0, self._add_test_result, test_type, test_input, result, True, expected)
                        passed += 1
                    else:
                        self.root.after(0, self._add_test_result, test_type, test_input, result, False, expected)
                        failed += 1

                except Exception as e:
                    if debug_cb:
                        debug_cb(f"测试出错: {test_input} - {str(e)}", level=1)

                    self.root.after(0, self._add_test_error, test_type, test_input, str(e))

                    self.log_manager.log_calculation(
                        calculation_type=f"测试-{test_type}",
                        expression=test_input,
                        result=str(e),
                        debug_info=debug_cb,
                        status="error",
                        error_msg=str(e)
                    )
                    failed += 1

                time.sleep(0.05)

            # 记录测试完成
            if debug_cb:
                if self.test_cancelled:
                    debug_cb(f"测试已取消，已运行 {i + 1} 个测试用例", level=1)
                else:
                    success_rate = passed / total_tests * 100 if total_tests > 0 else 0
                    debug_cb(f"测试完成，通过: {passed}, 失败: {failed}, 成功率: {success_rate:.1f}%", level=1)

            if not self.test_cancelled:
                self.root.after(0, self._complete_tests, passed, failed, total_tests)
            else:
                self.root.after(0, self._tests_cancelled, passed, failed, i + 1)

        except Exception as e:
            if self.debug_enabled.get():
                self.debug_callback(f"测试过程发生错误: {str(e)}", level=1)
            self.root.after(0, self._tests_error, str(e))

    def _clear_and_add_test_header(self, total_tests):
        self.history_text.delete(1.0, tk.END)
        self.history = []
        self._history_entries = []
        self.add_to_history("=" * 60)
        self.add_to_history(f"开始运行测试用例 - 总计 {total_tests} 个")
        self.add_to_history("=" * 60)

    def _update_test_progress(self, progress, current, total, current_test):
        if self.test_progress_window:
            self.test_progress_window.update_progress(progress, current, total, current_test)

    def _add_test_result(self, test_type, test_input, result, is_correct, expected=None):
        if is_correct:
            self.add_to_history(f"✓ {test_type}: {test_input}")
            self.add_to_history(f"  结果: {result}")
        else:
            self.add_to_history(f"✗ {test_type}: {test_input}", is_error=True)
            self.add_to_history(f"  期望: {expected}", is_error=True)
            self.add_to_history(f"  实际: {result}", is_error=True)

    def _add_test_error(self, test_type, test_input, error_msg):
        self.add_to_history(f"✗ {test_type}: {test_input} - 错误: {error_msg}", is_error=True)

    def _complete_tests(self, passed, failed, total_tests):
        self.add_to_history("=" * 60)
        self.add_to_history(f"测试完成: 通过 {passed}, 失败 {failed}, 总计 {total_tests}")
        self.add_to_history("=" * 60)

        debug_lines = len(self.debug_callback.lines)
        self.debug_counter_var.set(f"{debug_lines} 条信息")

        self.debug_status_var.set("测试完成")
        self.status_var.set(f"测试完成: 通过 {passed}/{total_tests}")

        self.result_text.delete(1.0, tk.END)
        summary = f"测试完成:\n\n"
        summary += f"通过: {passed}\n"
        summary += f"失败: {failed}\n"
        summary += f"总计: {total_tests}\n\n"
        success_rate = passed / total_tests * 100 if total_tests > 0 else 0
        summary += f"成功率: {success_rate:.1f}%"
        self.result_text.insert(1.0, summary)

        if self.test_progress_window:
            self.test_progress_window.complete(passed, failed, total_tests)

    def _tests_cancelled(self, passed, failed, tests_run):
        self.add_to_history("=" * 60)
        self.add_to_history(f"测试已取消")
        self.add_to_history(f"已运行: {tests_run} 个测试")
        self.add_to_history(f"通过: {passed}, 失败: {failed}")
        self.add_to_history("=" * 60)

        self.debug_status_var.set("测试已取消")
        self.status_var.set(f"测试已取消 - 已运行 {tests_run} 个测试")

        if self.test_progress_window:
            self.test_progress_window.close()
            self.test_progress_window = None

    def _tests_error(self, error_msg):
        self.add_to_history("=" * 60)
        self.add_to_history(f"测试发生错误: {error_msg}")
        self.add_to_history("=" * 60)

        self.debug_status_var.set("测试出错")
        self.status_var.set(f"测试出错: {error_msg}")

        if self.test_progress_window:
            self.test_progress_window.close()
            self.test_progress_window = None

        messagebox.showerror("测试错误", f"测试过程中发生错误:\n{error_msg}")



def main():
    """主函数"""
    root = tk.Tk()
    app = AlgebraCalculatorGUI(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n程序被用户中断，正在退出...")
        # 可选：√(x+1)=2，如保存日志、关闭线程等
        root.quit()


if __name__ == "__main__":
    main()