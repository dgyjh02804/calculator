import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from algebra_core import AlgebraicCalculator


class DebugCallback:
    """调试回调类，用于收集调试信息"""

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.lines = []

    def __call__(self, message):
        """调用时添加调试信息"""
        self.lines.append(message)
        # 在文本控件中显示
        if self.text_widget:
            self.text_widget.insert(tk.END, message + "\n")
            self.text_widget.see(tk.END)

    def clear(self):
        """清空调试信息"""
        self.lines = []
        if self.text_widget:
            self.text_widget.delete(1.0, tk.END)


class AlgebraCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("代数表达式计算器 - 含Debug模式")
        self.root.geometry("1200x900")

        # 创建计算器实例
        self.calculator = AlgebraicCalculator()

        # 存储历史记录
        self.history = []

        # Debug模式状态
        self.debug_mode = tk.BooleanVar(value=True)  # 默认开启debug模式

        # Debug回调
        self.debug_callback = None

        # 设置样式
        self.setup_styles()

        # 创建GUI组件
        self.create_widgets()

        # 绑定键盘事件
        self.bind_events()

        # 初始化debug回调
        self.debug_callback = DebugCallback(self.debug_text)

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
        style.configure('DebugOn.TButton', font=('Arial', 12, 'bold'), padding=5,
                        background='#4CAF50', foreground='white')
        style.configure('DebugOff.TButton', font=('Arial', 12), padding=5,
                        background='#9E9E9E', foreground='white')

    def create_widgets(self):
        """创建GUI组件"""
        # 创建主框架容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建左右两个主要面板
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))

        # ========== 左侧面板：计算器和历史记录 ==========

        # 标题
        title_label = ttk.Label(left_panel, text="代数表达式计算器",
                                font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 15))

        # 控制面板
        control_frame = ttk.Frame(left_panel)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Debug模式开关
        debug_frame = ttk.Frame(control_frame)
        debug_frame.pack(side=tk.LEFT, padx=(0, 20))

        debug_label = ttk.Label(debug_frame, text="Debug模式:", font=('Arial', 11))
        debug_label.pack(side=tk.LEFT)

        self.debug_on_btn = ttk.Button(debug_frame, text="ON",
                                       command=lambda: self.set_debug_mode(True),
                                       style='DebugOn.TButton')
        self.debug_on_btn.pack(side=tk.LEFT, padx=(5, 2))

        self.debug_off_btn = ttk.Button(debug_frame, text="OFF",
                                        command=lambda: self.set_debug_mode(False),
                                        style='DebugOff.TButton')
        self.debug_off_btn.pack(side=tk.LEFT, padx=(2, 5))

        # 控制按钮
        clear_debug_btn = ttk.Button(control_frame, text="清空Debug",
                                     command=self.clear_debug, style='Debug.TButton')
        clear_debug_btn.pack(side=tk.LEFT, padx=5)

        clear_history_btn = ttk.Button(control_frame, text="清空历史",
                                       command=self.clear_history)
        clear_history_btn.pack(side=tk.LEFT, padx=5)

        run_tests_btn = ttk.Button(control_frame, text="运行测试",
                                   command=self.run_tests)
        run_tests_btn.pack(side=tk.LEFT, padx=5)

        # 表达式输入框架
        expr_frame = ttk.LabelFrame(left_panel, text="输入表达式", padding=10)
        expr_frame.pack(fill=tk.X, pady=(0, 10))

        # 表达式输入框
        self.expression_var = tk.StringVar()
        self.expression_entry = ttk.Entry(expr_frame, textvariable=self.expression_var,
                                          font=('Arial', 12))
        self.expression_entry.pack(fill=tk.X, pady=(0, 10))

        # 操作按钮框架
        op_buttons_frame = ttk.Frame(expr_frame)
        op_buttons_frame.pack(fill=tk.X)

        calc_btn = ttk.Button(op_buttons_frame, text="化简计算",
                              command=self.calculate, style='Equal.TButton', width=15)
        calc_btn.pack(side=tk.LEFT, padx=(0, 10))

        solve_btn = ttk.Button(op_buttons_frame, text="解方程",
                               command=self.solve_equation, style='Solve.TButton', width=15)
        solve_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(op_buttons_frame, text="清空输入",
                               command=self.clear_expression, style='Clear.TButton')
        clear_btn.pack(side=tk.LEFT)

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

        # 变量和括号按钮行 - 修改这里，添加绝对值按钮
        var_frame = ttk.Frame(buttons_frame)
        var_frame.pack(fill=tk.X)

        # 修改 var_buttons 列表，添加 '√' 按钮
        var_buttons = ['x', 'y', 'z', 'a', 'b', 'c', '(', ')', '=', '√', '^']

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

            # 配置列权重
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

        # Debug控制栏
        debug_control_frame = ttk.Frame(debug_frame_main)
        debug_control_frame.pack(fill=tk.X, pady=(0, 10))

        debug_status_label = ttk.Label(debug_control_frame, text="状态:", font=('Arial', 11))
        debug_status_label.pack(side=tk.LEFT)

        self.debug_status_var = tk.StringVar()
        self.debug_status_var.set("就绪")
        debug_status = ttk.Label(debug_control_frame, textvariable=self.debug_status_var,
                                 font=('Arial', 11, 'italic'), foreground='blue')
        debug_status.pack(side=tk.LEFT, padx=(5, 15))

        # Debug信息计数器
        self.debug_counter_var = tk.StringVar()
        self.debug_counter_var.set("0 条信息")
        debug_counter = ttk.Label(debug_control_frame, textvariable=self.debug_counter_var,
                                  font=('Arial', 11))
        debug_counter.pack(side=tk.RIGHT)

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
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 输入表达式或方程（如 x+2=5），Debug模式已启用")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        status_bar.pack(fill=tk.X)

        # 更新Debug按钮状态
        self.update_debug_buttons()

    def update_debug_buttons(self):
        """更新Debug按钮状态"""
        if self.debug_mode.get():
            self.debug_on_btn.configure(style='DebugOn.TButton')
            self.debug_off_btn.configure(style='DebugOff.TButton')
        else:
            self.debug_on_btn.configure(style='DebugOff.TButton')
            self.debug_off_btn.configure(style='DebugOn.TButton')

    def set_debug_mode(self, enabled):
        """设置debug模式"""
        self.debug_mode.set(enabled)
        self.update_debug_buttons()

        if enabled:
            self.debug_callback.text_widget = self.debug_text
            self.debug_status_var.set("Debug模式: 启用")
            self.status_var.set("Debug模式已启用 - 计算过程将实时显示在右侧")
        else:
            self.debug_callback.text_widget = None
            self.debug_status_var.set("Debug模式: 禁用")
            self.status_var.set("Debug模式已禁用")

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

    def toggle_debug_mode(self):
        """切换debug模式"""
        self.set_debug_mode(not self.debug_mode.get())

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
        self.status_var.set("已清空历史记录")

    def append_to_expression(self, text):
        """将文本附加到表达式输入框"""
        current = self.expression_var.get()
        cursor_pos = self.expression_entry.index(tk.INSERT)

        # 特殊处理绝对值函数
        if text == 'abs':
            text = 'abs()'
            # 移动光标到括号内
            new_text = current[:cursor_pos] + text + current[cursor_pos:]
            self.expression_var.set(new_text)
            # 移动光标到括号内
            new_pos = cursor_pos + 4  # 'abs(' 的长度
            self.expression_entry.icursor(new_pos)
        else:
            # 插入文本
            new_text = current[:cursor_pos] + text + current[cursor_pos:]
            self.expression_var.set(new_text)

            # 移动光标到插入位置后
            new_pos = cursor_pos + len(text)
            self.expression_entry.icursor(new_pos)

        # 聚焦到输入框
        self.expression_entry.focus()

    def clear_expression(self):
        """清空表达式输入框"""
        self.expression_var.set("")
        self.result_text.delete(1.0, tk.END)
        self.expression_entry.focus()
        self.status_var.set("已清空输入")

    def calculate(self):
        """计算或化简表达式"""
        expression = self.expression_var.get().strip()

        if not expression:
            messagebox.showwarning("输入为空", "请输入一个表达式")
            return

        try:
            # 清空debug信息
            self.clear_debug()

            # 更新状态
            self.debug_status_var.set("正在计算...")
            self.status_var.set(f"计算: {expression}")

            # 设置debug回调
            debug_cb = self.debug_callback if self.debug_mode.get() else None

            # 计算表达式
            result = self.calculator.simplify_expression(expression, debug_cb)

            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result)

            # 更新debug信息计数器
            debug_lines = len(self.debug_callback.lines)
            self.debug_counter_var.set(f"{debug_lines} 条信息")

            # 添加到历史记录
            self.add_to_history(f"[表达式] {expression}")
            self.add_to_history(f"[结果]   {result}")
            self.add_to_history("-" * 60)

            # 更新状态
            self.debug_status_var.set("计算完成")
            self.status_var.set(f"计算完成: {expression}")

        except Exception as e:
            error_msg = f"错误: {str(e)}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, error_msg)

            # 添加到历史记录（错误）
            self.add_to_history(f"[表达式] {expression}")
            self.add_to_history(f"[错误]   {str(e)}")
            self.add_to_history("-" * 60)

            self.debug_status_var.set("计算出错")
            self.status_var.set(f"计算出错: {str(e)}")

            # 显示错误消息框
            messagebox.showerror("计算错误", str(e))

    def solve_equation(self):
        """解方程"""
        expression = self.expression_var.get().strip()

        if not expression:
            messagebox.showwarning("输入为空", "请输入一个方程（包含等号）")
            return

        if '=' not in expression:
            messagebox.showinfo("提示", "方程应包含等号。已自动进行化简计算。")
            self.calculate()
            return

        try:
            # 清空debug信息
            self.clear_debug()

            # 更新状态
            self.debug_status_var.set("正在解方程...")
            self.status_var.set(f"解方程: {expression}")

            # 设置debug回调
            debug_cb = self.debug_callback if self.debug_mode.get() else None

            # 解方程
            result = self.calculator.simplify_expression(expression, debug_cb)

            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result)

            # 更新debug信息计数器
            debug_lines = len(self.debug_callback.lines)
            self.debug_counter_var.set(f"{debug_lines} 条信息")

            # 添加到历史记录
            self.add_to_history(f"[方程] {expression}")
            self.add_to_history(f"[解]   {result}")
            self.add_to_history("-" * 60)

            # 更新状态
            self.debug_status_var.set("解方程完成")
            self.status_var.set(f"方程求解完成: {expression}")

        except Exception as e:
            error_msg = f"解方程错误: {str(e)}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, error_msg)

            # 添加到历史记录（错误）
            self.add_to_history(f"[方程] {expression}")
            self.add_to_history(f"[错误] {str(e)}")
            self.add_to_history("-" * 60)

            self.debug_status_var.set("解方程出错")
            self.status_var.set(f"解方程出错: {str(e)}")

            # 显示错误消息框
            messagebox.showerror("解方程错误", str(e))

    def add_to_history(self, text):
        """添加文本到历史记录"""
        self.history.append(text)
        self.history_text.insert(tk.END, text + "\n")

        # 滚动到底部
        self.history_text.see(tk.END)

    def run_tests(self):
        """运行测试用例"""
        # 清空debug信息
        self.clear_debug()

        # 更新状态
        self.debug_status_var.set("正在运行测试...")
        self.status_var.set("正在运行测试用例")

        # 设置debug回调
        debug_cb = self.debug_callback if self.debug_mode.get() else None

        # 测试用例
        test_cases = [
            ("(2x)/2", "x"),
            ("2x+3x", "5x"),
            ("a+b-(a-b)", "2b"),
            ("x*x", "x^2"),
            ("2*(a+b)", "2a+2b"),
            ("(a+b)(c+d)", "ac+ad+bc+bd"),
            ("(x+y)(x-y)", "x^2-y^2"),
            ("(a+b)^2", "2ab+a^2+b^2"),
            ("x/2 + x/2", "x"),
            ("3*(x+y) - 2*(x+y)", "x+y"),
            ("1/2/3/4/5/6/7/8","35/128"),
            ("(8x^3)^(1/2)","2x√(2x)"),
            ("√(4)","2"),
            ("1/√(x+1)","(√(x+1))/(x+1)")
        ]

        # 方程测试用例
        equation_tests = [
            ("x+2=5", "x = 3"),
            ("2x=8", "x = 4"),
            ("3x-6=0", "x = 2"),
            ("x+y=10", "多变量方程的解:\n  x = 10-y\n  y = 10-x"),
            ("2x+3=7", "x = 2"),
            ("x/2 = 3", "x = 6"),
            ("3x = 12", "x = 4"),
            ("x-5=0", "x = 5"),
        ]

        self.add_to_history("=" * 60)
        self.add_to_history("开始运行测试用例")
        self.add_to_history("=" * 60)

        passed = 0
        failed = 0

        # 测试表达式化简
        self.add_to_history("--- 表达式化简测试 ---")
        for expr, expected in test_cases:
            try:
                if debug_cb:
                    debug_cb(f"\n{'=' * 50}")
                    debug_cb(f"测试: {expr}")
                    debug_cb(f"{'=' * 50}")

                result = self.calculator.simplify_expression(expr, debug_cb)

                # 简化和格式化结果
                if result.startswith('(') and result.endswith(')'):
                    inner = result[1:-1]
                    if not any(op in inner for op in '+-'):
                        result = inner

                if result == expected:
                    self.add_to_history(f"✓ {expr} = {result}")
                    passed += 1
                else:
                    self.add_to_history(f"✗ {expr}")
                    self.add_to_history(f"  期望: {expected}")
                    self.add_to_history(f"  实际: {result}")
                    failed += 1

            except Exception as e:
                self.add_to_history(f"✗ {expr} - 错误: {str(e)}")
                failed += 1

        # 测试方程求解
        self.add_to_history("--- 方程求解测试 ---")
        for equation, expected in equation_tests:
            try:
                if debug_cb:
                    debug_cb(f"\n{'=' * 50}")
                    debug_cb(f"测试方程: {equation}")
                    debug_cb(f"{'=' * 50}")

                result = self.calculator.simplify_expression(equation, debug_cb)

                # 对于方程求解，我们检查结果是否包含期望的解
                # 对于多变量方程，可能格式略有不同，我们检查关键部分
                is_correct = False

                if "多变量方程" in expected:
                    # 对于多变量方程，检查是否包含了正确的解
                    if "10-y" in result and "10-x" in result:
                        is_correct = True
                else:
                    # 对于单变量方程，检查精确匹配
                    is_correct = (result == expected)

                if is_correct:
                    self.add_to_history(f"✓ {equation}")
                    self.add_to_history(f"  结果: {result}")
                    passed += 1
                else:
                    self.add_to_history(f"✗ {equation}")
                    self.add_to_history(f"  期望: {expected}")
                    self.add_to_history(f"  实际: {result}")
                    failed += 1

            except Exception as e:
                self.add_to_history(f"✗ {equation} - 错误: {str(e)}")
                failed += 1

        # 显示统计结果
        self.add_to_history("=" * 60)
        total_tests = len(test_cases) + len(equation_tests)
        self.add_to_history(f"测试完成: 通过 {passed}, 失败 {failed}, 总计 {total_tests}")
        self.add_to_history("=" * 60)

        # 更新debug信息计数器
        debug_lines = len(self.debug_callback.lines)
        self.debug_counter_var.set(f"{debug_lines} 条信息")

        # 更新状态
        self.debug_status_var.set("测试完成")
        self.status_var.set(f"测试完成: 通过 {passed}/{total_tests}")

        # 在结果框中显示测试摘要
        self.result_text.delete(1.0, tk.END)
        summary = f"测试完成:\n\n"
        summary += f"表达式测试: {len(test_cases)}个\n"
        summary += f"方程测试: {len(equation_tests)}个\n\n"
        summary += f"通过: {passed}\n"
        summary += f"失败: {failed}\n"
        summary += f"总计: {total_tests}\n\n"
        summary += f"成功率: {passed / total_tests * 100:.1f}%"
        self.result_text.insert(1.0, summary)


def main():
    """主函数"""
    root = tk.Tk()
    app = AlgebraCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()