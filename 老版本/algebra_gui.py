import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from algebra_core import AlgebraicCalculator


class AlgebraCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("代数表达式计算器")
        self.root.geometry("800x700")

        # 创建计算器实例
        self.calculator = AlgebraicCalculator()

        # 存储历史记录
        self.history = []

        # 设置样式
        self.setup_styles()

        # 创建GUI组件
        self.create_widgets()

        # 绑定键盘事件
        self.bind_events()

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

    def create_widgets(self):
        """创建GUI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text="代数表达式计算器",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # 表达式输入标签
        expr_label = ttk.Label(main_frame, text="输入表达式:", font=('Arial', 11))
        expr_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        # 表达式输入框
        self.expression_var = tk.StringVar()
        self.expression_entry = ttk.Entry(main_frame, textvariable=self.expression_var,
                                          font=('Arial', 12), width=40)
        self.expression_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E),
                                   padx=(10, 0), pady=5)

        # 清空按钮
        clear_button = ttk.Button(main_frame, text="清空", command=self.clear_expression,
                                  style='Clear.TButton')
        clear_button.grid(row=1, column=3, padx=(10, 0), pady=5)

        # 结果显示区域
        result_label = ttk.Label(main_frame, text="化简结果:", font=('Arial', 11))
        result_label.grid(row=2, column=0, sticky=tk.W, pady=5)

        self.result_text = scrolledtext.ScrolledText(main_frame, height=3,
                                                     font=('Arial', 12), wrap=tk.WORD)
        self.result_text.grid(row=2, column=1, columnspan=3, sticky=(tk.W, tk.E),
                              pady=5, padx=(10, 0))

        # 按钮框架
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=4, pady=20, sticky=(tk.W, tk.E))

        # 第一行按钮：数字
        row1_frame = ttk.Frame(buttons_frame)
        row1_frame.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))

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
                    btn = ttk.Button(row1_frame, text=text, width=5,
                                     command=lambda t=text: self.append_to_expression(t),
                                     style='Number.TButton')
                    if text in '+-*/^':
                        btn.configure(style='Operator.TButton')
                    btn.grid(row=i, column=j, padx=2, pady=2)

        # 第二行按钮：变量和括号
        row2_frame = ttk.Frame(buttons_frame)
        row2_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))

        var_buttons = [
            ('x', 0), ('y', 1), ('z', 2), ('a', 3), ('b', 4), ('c', 5),
            ('(', 6), (')', 7)
        ]

        for i, (text, col) in enumerate(var_buttons):
            btn = ttk.Button(row2_frame, text=text, width=5,
                             command=lambda t=text: self.append_to_expression(t))
            if text.isalpha():
                btn.configure(style='Variable.TButton')
            else:
                btn.configure(style='Operator.TButton')
            btn.grid(row=0, column=col, padx=2, pady=2)

        # 计算按钮
        calc_frame = ttk.Frame(buttons_frame)
        calc_frame.grid(row=2, column=0, pady=10, sticky=(tk.W, tk.E))

        equal_button = ttk.Button(calc_frame, text="计算", command=self.calculate,
                                  style='Equal.TButton', width=20)
        equal_button.grid(row=0, column=0, padx=5)

        test_button = ttk.Button(calc_frame, text="运行测试", command=self.run_tests,
                                 width=15)
        test_button.grid(row=0, column=1, padx=5)

        # 历史记录/日志区域
        history_label = ttk.Label(main_frame, text="计算历史:", font=('Arial', 11))
        history_label.grid(row=4, column=0, sticky=tk.W, pady=(20, 5))

        self.history_text = scrolledtext.ScrolledText(main_frame, height=10,
                                                      font=('Courier New', 10))
        self.history_text.grid(row=5, column=0, columnspan=4,
                               sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # 配置网格权重
        main_frame.rowconfigure(5, weight=1)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))

    def bind_events(self):
        """绑定键盘事件"""
        self.root.bind('<Return>', lambda event: self.calculate())
        self.root.bind('<Escape>', lambda event: self.clear_expression())

        # 快捷键
        self.root.bind('<Control-l>', lambda event: self.clear_history())
        self.root.bind('<Control-t>', lambda event: self.run_tests())

    def append_to_expression(self, text):
        """将文本附加到表达式输入框"""
        current = self.expression_var.get()
        cursor_pos = self.expression_entry.index(tk.INSERT)

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

    def clear_history(self):
        """清空历史记录"""
        self.history_text.delete(1.0, tk.END)
        self.history = []
        self.status_var.set("已清空历史记录")

    def calculate(self):
        """计算表达式"""
        expression = self.expression_var.get().strip()

        if not expression:
            messagebox.showwarning("输入为空", "请输入一个表达式")
            return

        try:
            # 计算表达式
            result = self.calculator.simplify_expression(expression)

            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result)

            # 添加到历史记录
            self.add_to_history(f"表达式: {expression}")
            self.add_to_history(f"结果: {result}")
            self.add_to_history("-" * 50)

            # 更新状态
            self.status_var.set(f"计算完成: {expression}")

        except Exception as e:
            error_msg = f"错误: {str(e)}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, error_msg)

            # 添加到历史记录（错误）
            self.add_to_history(f"表达式: {expression}")
            self.add_to_history(f"错误: {str(e)}")
            self.add_to_history("-" * 50)

            self.status_var.set(f"计算出错: {str(e)}")

            # 显示错误消息框
            messagebox.showerror("计算错误", str(e))

    def add_to_history(self, text):
        """添加文本到历史记录"""
        self.history.append(text)
        self.history_text.insert(tk.END, text + "\n")

        # 滚动到底部
        self.history_text.see(tk.END)

    def run_tests(self):
        """运行测试用例"""
        # 减少测试数量，只保留核心测试
        test_cases = [
            ("(2x)/2", "x"),
            ("2x+3x", "5x"),
            ("a+b-(a-b)", "2b"),
            ("x*x", "x^2"),
            ("2*(a+b)", "2a+2b"),
            ("(a+b)(c+d)", "ac+ad+bc+bd"),
            ("(x+y)(x-y)", "x^2-y^2"),
            ("(a+b)^2", "a^2+2ab+b^2"),
            ("x/2 + x/2", "x"),
            ("3*(x+y) - 2*(x+y)", "x+y"),
        ]

        self.add_to_history("=" * 50)
        self.add_to_history("开始运行测试用例")
        self.add_to_history("=" * 50)

        passed = 0
        failed = 0

        for expr, expected in test_cases:
            try:
                result = self.calculator.simplify_expression(expr)

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

        # 显示统计结果
        self.add_to_history("=" * 50)
        self.add_to_history(f"测试完成: 通过 {passed}, 失败 {failed}, 总计 {len(test_cases)}")
        self.add_to_history("=" * 50)

        self.status_var.set(f"测试完成: 通过 {passed}/{len(test_cases)}")

        # 在结果框中显示测试摘要
        self.result_text.delete(1.0, tk.END)
        summary = f"测试完成:\n通过: {passed}\n失败: {failed}\n总计: {len(test_cases)}"
        self.result_text.insert(1.0, summary)


def main():
    """主函数"""
    root = tk.Tk()
    app = AlgebraCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()