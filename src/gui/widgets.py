"""代数计算器 GUI — 控件：日志查看器、测试进度窗口、测试选择对话框"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import json
import threading
from datetime import datetime


class LogViewerWindow:
    """日志查看器窗口"""

    def __init__(self, parent, log_manager):
        self.parent = parent
        self.log_manager = log_manager
        self.window = tk.Toplevel(parent)
        self.window.title("计算日志查看器")
        self.window.geometry("800x600")

        # 创建主框架
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题和统计信息
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(header_frame, text="计算日志查看器",
                                font=('Arial', 14, 'bold'))
        title_label.pack(side=tk.LEFT)

        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        refresh_btn = ttk.Button(control_frame, text="刷新日志",
                                 command=self.refresh_logs)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        export_btn = ttk.Button(control_frame, text="导出日志",
                                command=self.export_logs)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(control_frame, text="清空日志",
                               command=self.clear_logs)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        close_btn = ttk.Button(control_frame, text="关闭",
                               command=self.window.destroy)
        close_btn.pack(side=tk.RIGHT)

        # 统计信息框架
        stats_frame = ttk.LabelFrame(main_frame, text="日志统计", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.stats_labels = {}
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)

        stats_info = [
            ("日志文件大小:", "file_size"),
            ("总记录数:", "total_entries"),
            ("成功计算:", "success_count"),
            ("失败计算:", "error_count"),
            ("最后记录:", "last_entry")
        ]

        for i, (label_text, key) in enumerate(stats_info):
            row = i // 2
            col = (i % 2) * 2

            label = ttk.Label(stats_grid, text=label_text, font=('Arial', 10))
            label.grid(row=row, column=col, padx=(10, 5), pady=5, sticky=tk.W)

            value_label = ttk.Label(stats_grid, text="", font=('Arial', 10, 'bold'))
            value_label.grid(row=row, column=col + 1, padx=(0, 20), pady=5, sticky=tk.W)

            self.stats_labels[key] = value_label

        # 日志列表
        list_frame = ttk.LabelFrame(main_frame, text="计算记录", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Treeview显示日志
        columns = ("时间", "类型", "表达式", "结果", "状态")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        # 设置列宽
        column_widths = [150, 80, 200, 200, 80]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 详情面板
        detail_frame = ttk.LabelFrame(main_frame, text="详细信息", padding=10)
        detail_frame.pack(fill=tk.X, pady=(10, 0))

        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=8,
                                                     font=('Consolas', 9))
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_log_selected)

        # 初始加载日志
        self.refresh_logs()

    def refresh_logs(self):
        """刷新日志列表"""
        # 清除现有项
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 获取日志
        logs = self.log_manager.get_recent_logs(100)

        # 添加到treeview
        for log in logs:
            timestamp = log.get('timestamp', '')
            calc_type = log.get('type', '')
            expression = log.get('expression', '')
            result = log.get('result', '')
            status = log.get('status', '')

            # 截断长字符串
            if len(expression) > 30:
                expression_display = expression[:27] + "..."
            else:
                expression_display = expression

            if len(result) > 30:
                result_display = result[:27] + "..."
            else:
                result_display = result

            # 添加行
            self.tree.insert('', tk.END, values=(
                timestamp, calc_type, expression_display,
                result_display, status
            ), tags=(status,))

        # 设置状态颜色
        self.tree.tag_configure('success', foreground='green')
        self.tree.tag_configure('error', foreground='red')

        # 更新统计信息
        self.update_stats()

    def update_stats(self):
        """更新统计信息"""
        stats = self.log_manager.get_log_stats()
        for key, label in self.stats_labels.items():
            if key in stats:
                label.config(text=str(stats[key]))

    def on_log_selected(self, event):
        """当选择日志项时显示详细信息"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, 'values')

        # 获取完整日志
        logs = self.log_manager.get_recent_logs(100)
        index = self.tree.index(item)

        if index < len(logs):
            log = logs[index]
            detail = f"时间: {log.get('timestamp', '')}\n"
            detail += f"类型: {log.get('type', '')}\n"
            detail += f"表达式: {log.get('expression', '')}\n"
            detail += f"结果: {log.get('result', '')}\n"
            detail += f"状态: {log.get('status', '')}\n"

            if log.get('status') == 'error' and log.get('error'):
                detail += f"错误信息: {log.get('error', '')}\n"

            detail += f"Debug行数: {log.get('debug_lines', 0)}\n"

            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(1.0, detail)

    def export_logs(self):
        """导出日志"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"algebra_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if file_path:
            exported = self.log_manager.export_logs(file_path)
            if exported:
                messagebox.showinfo("导出成功", f"日志已导出到:\n{exported}")
            else:
                messagebox.showerror("导出失败", "日志导出失败")

    def clear_logs(self):
        """清空日志"""
        if messagebox.askyesno("确认清空", "确定要清空所有日志记录吗？"):
            if self.log_manager.clear_logs():
                messagebox.showinfo("清空成功", "日志已清空")
                self.refresh_logs()
            else:
                messagebox.showerror("清空失败", "清空日志失败")


class TestProgressWindow:
    """测试进度窗口"""

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("测试进度")
        self.window.geometry("500x220")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self.window.protocol("WM_DELETE_WINDOW", self._do_nothing)

        title_label = ttk.Label(self.window, text="正在运行测试用例",
                                font=('Arial', 14, 'bold'))
        title_label.pack(pady=(20, 15))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.window,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(pady=10, padx=20)

        self.progress_label = ttk.Label(
            self.window,
            text="准备开始...",
            font=('Arial', 11, 'bold')
        )
        self.progress_label.pack(pady=(5, 8))

        self.detail_label = ttk.Label(
            self.window,
            text="",
            font=('Arial', 10),
            wraplength=450
        )
        self.detail_label.pack(pady=(0, 15))

        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        self.cancel_button = ttk.Button(
            button_frame,
            text="取消测试",
            command=self.cancel,
            width=15
        )
        self.cancel_button.pack()

        self.cancelled = False

    def _do_nothing(self):
        pass

    def update_progress(self, value, current, total, current_test=""):
        self.progress_var.set(value)
        self.progress_label.config(text=f"进度: {current}/{total} ({value:.1f}%)")
        if current_test:
            if len(current_test) > 50:
                display_test = current_test[:47] + "..."
            else:
                display_test = current_test
            self.detail_label.config(text=f"当前: {display_test}")
        else:
            self.detail_label.config(text="")
        self.window.update_idletasks()

    def show_freeze_warning(self, test_name, elapsed_sec):
        """防卡死：显示当前卡住的测试和耗时"""
        self.progress_label.config(
            text=f"⚠ 疑似卡死 ({elapsed_sec:.0f}s)", foreground='red')
        if len(test_name) > 50:
            test_name = test_name[:47] + "..."
        self.detail_label.config(
            text=f"卡在: {test_name}", foreground='red')
        self.window.update_idletasks()

    def cancel(self):
        self.cancelled = True
        self.cancel_button.config(text="正在取消...", state=tk.DISABLED)
        self.progress_label.config(text="正在取消测试...")
        self.detail_label.config(text="请稍候...")

    def complete(self, passed, failed, total):
        self.cancel_button.config(text="完成", command=self.close, state=tk.NORMAL)
        success_rate = passed / total * 100 if total > 0 else 0
        self.progress_var.set(100)
        self.progress_label.config(
            text=f"测试完成! 通过: {passed}, 失败: {failed}, 总计: {total}",
            foreground='green' if success_rate > 80 else 'orange' if success_rate > 60 else 'red'
        )
        self.detail_label.config(
            text=f"成功率: {success_rate:.1f}%",
            foreground='green' if success_rate > 80 else 'orange' if success_rate > 60 else 'red'
        )
        # 3秒后自动关闭窗口
        self.window.after(3000, self.close)

    def close(self):
        self.window.destroy()



class TestSelectionDialog:
    """测试选择对话框，允许同时选择表达式和方程的子类别，支持多选和全选"""

    def __init__(self, parent, expression_categories, equation_categories, other_categories=None):
        self.parent = parent
        self.expression_categories = expression_categories
        self.equation_categories = equation_categories
        self.other_categories = other_categories or {}
        self.result = None  # 存储选择结果: (选中的表达式子类别列表, 选中的方程子类别列表, 选中的其他子类别列表)

        self.window = tk.Toplevel(parent)
        self.window.title("选择测试类别")
        self.window.geometry("900x480")
        self.window.transient(parent)
        self.window.grab_set()

        # 主框架
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 操作提示
        tip_label = ttk.Label(main_frame,
                              text="提示：按住 Ctrl 可多选；使用 Shift 可连续选择；可分别从两边选择多个类别。",
                              font=('Arial', 9), foreground='blue')
        tip_label.pack(fill=tk.X, pady=(0, 10))

        # 左右两个区域框架
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 左边：表达式子类别
        expr_frame = ttk.LabelFrame(paned, text="表达式化简测试", padding=10)
        paned.add(expr_frame, weight=1)

        # 表达式子类别列表（多选，EXTENDED 模式支持 Shift 连续选择）
        self.expr_listbox = tk.Listbox(expr_frame, selectmode=tk.EXTENDED, height=12, exportselection=False)
        self.expr_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 填充表达式子类别
        for cat in self.expression_categories.keys():
            self.expr_listbox.insert(tk.END, cat)

        # 表达式按钮组
        expr_btn_frame = ttk.Frame(expr_frame)
        expr_btn_frame.pack(fill=tk.X)
        ttk.Button(expr_btn_frame, text="全选表达式", command=self._select_all_expr).pack(side=tk.LEFT, padx=2)
        ttk.Button(expr_btn_frame, text="取消全选", command=self._deselect_all_expr).pack(side=tk.LEFT, padx=2)

        # 显示表达式已选数量
        self.expr_count_var = tk.StringVar(value="已选 0 项")
        expr_count_label = ttk.Label(expr_frame, textvariable=self.expr_count_var, font=('Arial', 9))
        expr_count_label.pack(anchor=tk.W, pady=(5, 0))

        # 右边：方程子类别
        eq_frame = ttk.LabelFrame(paned, text="方程求解测试", padding=10)
        paned.add(eq_frame, weight=1)

        self.eq_listbox = tk.Listbox(eq_frame, selectmode=tk.EXTENDED, height=12, exportselection=False)
        self.eq_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        for cat in self.equation_categories.keys():
            self.eq_listbox.insert(tk.END, cat)

        eq_btn_frame = ttk.Frame(eq_frame)
        eq_btn_frame.pack(fill=tk.X)
        ttk.Button(eq_btn_frame, text="全选方程", command=self._select_all_eq).pack(side=tk.LEFT, padx=2)
        ttk.Button(eq_btn_frame, text="取消全选", command=self._deselect_all_eq).pack(side=tk.LEFT, padx=2)

        self.eq_count_var = tk.StringVar(value="已选 0 项")
        eq_count_label = ttk.Label(eq_frame, textvariable=self.eq_count_var, font=('Arial', 9))
        eq_count_label.pack(anchor=tk.W, pady=(5, 0))

        # 右边：其他测试类别
        other_frame = ttk.LabelFrame(paned, text="其他测试", padding=10)
        paned.add(other_frame, weight=1)

        self.other_listbox = tk.Listbox(other_frame, selectmode=tk.EXTENDED, height=12, exportselection=False)
        self.other_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        for cat in self.other_categories.keys():
            self.other_listbox.insert(tk.END, cat)

        other_btn_frame = ttk.Frame(other_frame)
        other_btn_frame.pack(fill=tk.X)
        ttk.Button(other_btn_frame, text="全选其他", command=self._select_all_other).pack(side=tk.LEFT, padx=2)
        ttk.Button(other_btn_frame, text="取消全选", command=self._deselect_all_other).pack(side=tk.LEFT, padx=2)

        self.other_count_var = tk.StringVar(value="已选 0 项")
        other_count_label = ttk.Label(other_frame, textvariable=self.other_count_var, font=('Arial', 9))
        other_count_label.pack(anchor=tk.W, pady=(5, 0))

        # 绑定选择事件以更新计数
        self.expr_listbox.bind('<<ListboxSelect>>', self._update_counts)
        self.eq_listbox.bind('<<ListboxSelect>>', self._update_counts)
        self.other_listbox.bind('<<ListboxSelect>>', self._update_counts)

        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(bottom_frame, text="运行所选测试", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="取消", command=self._on_cancel).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="一键测试所有", command=self._select_all_and_run).pack(side=tk.LEFT, padx=5)

    def _select_all_and_run(self):
        self._select_all_expr()
        self._select_all_eq()
        self._select_all_other()
        self._on_ok()

    def _select_all_expr(self):
        self.expr_listbox.selection_set(0, tk.END)
        self._update_counts()

    def _deselect_all_expr(self):
        self.expr_listbox.selection_clear(0, tk.END)
        self._update_counts()

    def _select_all_eq(self):
        self.eq_listbox.selection_set(0, tk.END)
        self._update_counts()

    def _deselect_all_eq(self):
        self.eq_listbox.selection_clear(0, tk.END)
        self._update_counts()

    def _select_all_other(self):
        self.other_listbox.selection_set(0, tk.END)
        self._update_counts()

    def _deselect_all_other(self):
        self.other_listbox.selection_clear(0, tk.END)
        self._update_counts()

    def _update_counts(self, event=None):
        expr_selected = len(self.expr_listbox.curselection())
        eq_selected = len(self.eq_listbox.curselection())
        other_selected = len(self.other_listbox.curselection())
        self.expr_count_var.set(f"已选 {expr_selected} 项")
        self.eq_count_var.set(f"已选 {eq_selected} 项")
        self.other_count_var.set(f"已选 {other_selected} 项")

    def _on_ok(self):
        expr_selected = [self.expr_listbox.get(i) for i in self.expr_listbox.curselection()]
        eq_selected = [self.eq_listbox.get(i) for i in self.eq_listbox.curselection()]
        other_selected = [self.other_listbox.get(i) for i in self.other_listbox.curselection()]

        if not expr_selected and not eq_selected and not other_selected:
            messagebox.showwarning("未选择", "请至少选择一个测试类别")
            return

        self.result = (expr_selected, eq_selected, other_selected)
        self.window.destroy()

    def _on_cancel(self):
        self.result = (None, None)  # 取消时返回 (None, None)
        self.window.destroy()

    def show(self):
        """显示对话框并等待返回结果"""
        self.window.wait_window()
        return self.result


