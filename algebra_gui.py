import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import re
import threading
import time
import os
import json
from datetime import datetime
from algebra_solver import AlgebraicCalculator


class ConfigManager:
    """配置文件管理器，负责保存和加载用户设置"""

    DEFAULT_CONFIG = {
        "debug_level": 2,          # 0:无 1:简易 2:正常 3:详细
        "debug_speed": "正常",      # 即时/快速/正常/慢速/逐条
        "debug_enabled": True,
    }

    def __init__(self, config_file="algebra_calculator_config.json"):
        self.config_file = config_file
        self.config = dict(self.DEFAULT_CONFIG)
        self.load()

    def load(self):
        """从文件加载配置，文件不存在或格式错误时使用默认值"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 只更新已知的键，保留默认值
                for key in self.DEFAULT_CONFIG:
                    if key in data:
                        self.config[key] = data[key]
                return True
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
            self.config = dict(self.DEFAULT_CONFIG)
        return False

    def save(self):
        """保存当前配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key, value):
        """设置配置项并立即保存"""
        if key in self.DEFAULT_CONFIG:
            self.config[key] = value
            self.save()


class LogManager:
    """日志管理器，负责记录计算日志"""

    def __init__(self, log_file="algebra_calculator.log"):
        self.log_file = log_file
        self.enabled = True
        self.max_log_size = 1024 * 1024 * 1024  # 1GB最大日志文件大小
        self.max_log_files = 5  # 最多保留5个日志文件

        # 确保日志目录存在
        log_dir = os.path.dirname(os.path.abspath(self.log_file))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 初始化日志文件
        self._init_log_file()

    def _init_log_file(self):
        """初始化日志文件"""
        try:
            # 检查文件大小，如果超过限制则轮转
            if os.path.exists(self.log_file):
                if os.path.getsize(self.log_file) > self.max_log_size:
                    self._rotate_logs()

            # 写入日志头
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"代数计算器日志 - 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
        except Exception as e:
            print(f"初始化日志文件失败: {e}")

    def _rotate_logs(self):
        """日志轮转"""
        try:
            for i in range(self.max_log_files - 1, 0, -1):
                old_file = f"{self.log_file}.{i}"
                new_file = f"{self.log_file}.{i + 1}"
                if os.path.exists(old_file):
                    if os.path.exists(new_file):
                        os.remove(new_file)
                    os.rename(old_file, new_file)

            if os.path.exists(self.log_file):
                os.rename(self.log_file, f"{self.log_file}.1")
        except Exception as e:
            print(f"日志轮转失败: {e}")

    def log_calculation(self, calculation_type, expression, result,
                        debug_info=None, status="success", error_msg=None):
        """记录计算日志"""
        if not self.enabled:
            return

        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 获取debug信息的行数
            debug_lines = 0
            if debug_info and hasattr(debug_info, 'lines'):
                debug_lines = len(debug_info.lines)

            log_entry = {
                "timestamp": timestamp,
                "type": calculation_type,
                "expression": expression,
                "result": result,
                "status": status,
                "debug_lines": debug_lines,
                "error": error_msg
            }

            # 写入文本日志
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {calculation_type}\n")
                f.write(f"表达式: {expression}\n")
                f.write(f"结果: {result}\n")

                if status == "error" and error_msg:
                    f.write(f"错误: {error_msg}\n")

                if debug_info and hasattr(debug_info, 'lines') and debug_info.lines:
                    f.write(f"Debug信息 ({len(debug_info.lines)}行):\n")
                    for line in debug_info.lines:
                        f.write(f"  {line}\n")

                f.write("-" * 80 + "\n\n")

            # 写入JSON日志（用于分析）
            json_file = self.log_file.replace('.log', '_history.json')
            self._append_json_log(json_file, log_entry)

            return True
        except Exception as e:
            print(f"记录日志失败: {e}")
            return False

    def _append_json_log(self, json_file, log_entry):
        """追加JSON格式的日志"""
        try:
            logs = []
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            logs = json.loads(content)
                except:
                    logs = []

            logs.append(log_entry)

            # 保持最近1000条记录
            if len(logs) > 1000:
                logs = logs[-1000:]

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入JSON日志失败: {e}")

    def get_recent_logs(self, count=50):
        """获取最近的日志记录"""
        try:
            json_file = self.log_file.replace('.log', '_history.json')
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    return logs[-count:] if len(logs) > count else logs
            return []
        except Exception as e:
            print(f"读取日志失败: {e}")
            return []

    def clear_logs(self):
        """清空日志"""
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)

            json_file = self.log_file.replace('.log', '_history.json')
            if os.path.exists(json_file):
                os.remove(json_file)

            # 重新初始化
            self._init_log_file()
            return True
        except Exception as e:
            print(f"清空日志失败: {e}")
            return False

    def export_logs(self, file_path=None):
        """导出日志到文件"""
        try:
            if not file_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = f"algebra_logs_{timestamp}.txt"

            with open(self.log_file, 'r', encoding='utf-8') as src, \
                    open(file_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())

            return file_path
        except Exception as e:
            print(f"导出日志失败: {e}")
            return None

    def get_log_stats(self):
        """获取日志统计信息"""
        try:
            if os.path.exists(self.log_file):
                size = os.path.getsize(self.log_file)
                size_kb = size / 1024
                size_mb = size_kb / 1024

                if size_mb >= 1:
                    size_str = f"{size_mb:.2f} MB"
                else:
                    size_str = f"{size_kb:.2f} KB"

                logs = self.get_recent_logs(1000)
                success_count = sum(1 for log in logs if log.get('status') == 'success')
                error_count = sum(1 for log in logs if log.get('status') == 'error')

                return {
                    "file_size": size_str,
                    "total_entries": len(logs),
                    "success_count": success_count,
                    "error_count": error_count,
                    "last_entry": logs[-1]['timestamp'] if logs else "无记录"
                }
            return {
                "file_size": "0 KB",
                "total_entries": 0,
                "success_count": 0,
                "error_count": 0,
                "last_entry": "无记录"
            }
        except Exception as e:
            print(f"获取日志统计失败: {e}")
            return {}


class DebugCallback:
    """调试回调类，用于收集调试信息"""

    def __init__(self, text_widget, debug_level=1, display_speed="正常"):
        """
        初始化debug回调

        参数:
            text_widget: 用于显示debug信息的文本控件
            debug_level: debug级别
                0: 无debug
                1: 简易debug - 只显示关键步骤
                2: 正常debug - 显示主要步骤（当前模式）
                3: 详细debug - 显示所有细节
            display_speed: 显示速度
                "即时": batch=500, delay=30ms
                "快速": batch=100, delay=60ms
                "正常": batch=50,  delay=150ms
                "慢速": batch=15,  delay=300ms
                "逐条": batch=1,   delay=600ms
        """
        self.text_widget = text_widget
        self.debug_level = debug_level
        self.lines = []
        self.message_queue = []
        self.max_queue_size = 2000
        self.is_running = False
        self.pending_count = 0  # 队列中待处理消息数

        # 显示速度配置
        self.SPEED_CONFIGS = {
            "即时": (500, 30),
            "快速": (100, 60),
            "正常": (50, 150),
            "慢速": (15, 300),
            "逐条": (1, 600),
        }
        self.set_display_speed(display_speed)

    def set_debug_level(self, level):
        """设置debug级别"""
        self.debug_level = level

    def set_display_speed(self, speed_name):
        """设置显示速度"""
        if speed_name in self.SPEED_CONFIGS:
            self.display_speed = speed_name
            self.batch_size, self.delay_ms = self.SPEED_CONFIGS[speed_name]
        else:
            self.display_speed = "正常"
            self.batch_size, self.delay_ms = 50, 150

    def get_pending_count(self):
        """获取队列中待处理的消息数"""
        return len(self.message_queue)

    def __call__(self, message, level=2):
        """
        调用时添加调试信息

        参数:
            message: 调试信息
            level: 信息级别，只有>=当前debug级别时才显示
        """
        if level <= self.debug_level:
            self.lines.append(message)

            # 如果是后台线程调用，将消息放入队列
            if threading.current_thread() != threading.main_thread():
                # 限制队列大小，超过时丢弃旧消息
                if len(self.message_queue) >= self.max_queue_size:
                    self.message_queue.pop(0)
                self.message_queue.append((message, level))
            else:
                # 主线程直接显示
                self._display_message(message, level)

    def _display_message(self, message, level):
        """显示调试信息"""
        # 根据级别添加不同前缀
        if level == 1:
            prefix = "[简单] "
        elif level == 2:
            prefix = "[正常] "
        elif level == 3:
            prefix = "[详细] "
        else:
            prefix = ""

        if self.text_widget:
            self.text_widget.insert(tk.END, prefix + message + "\n")
            self.text_widget.see(tk.END)

    def process_queue(self):
        """处理消息队列（在主线程中调用），每次处理的条数由显示速度决定"""
        processed = 0
        while self.message_queue and processed < self.batch_size:
            message, level = self.message_queue.pop(0)
            self._display_message(message, level)
            processed += 1

    def clear(self):
        """清空调试信息"""
        self.lines = []
        self.message_queue.clear()
        if self.text_widget:
            self.text_widget.delete(1.0, tk.END)

    def start(self):
        """开始记录"""
        self.is_running = True

    def stop(self):
        """停止记录"""
        self.is_running = False


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
            if len(current_test) > 40:
                display_test = current_test[:37] + "..."
            else:
                display_test = current_test
            self.detail_label.config(text=f"当前测试: {display_test}")
        else:
            self.detail_label.config(text="")
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


class AlgebraCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("代数表达式计算器 V2.0.0 --------------------全基础运算 --------------------   构建时间: 5.30  ")
        self.root.geometry("1200x900")

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

        # 创建日志管理器
        self.log_manager = LogManager("logs/algebra_calculator.log")

        # 表达式化简测试（按子类别分组）
        self.expression_categories = {
            "基本运算": [
                ("(2x)/2", "x"),
                ("2x+3x", "5x"),
                ("a+b-(a-b)", "2b"),
                ("x*x", "x^2"),
                ("x/2 + x/2", "x"),
                ("3*(x+y) - 2*(x+y)", "x+y"),
                ("1/2/3/4/5/6/7/8/9", "1/362880"),
            ],
            "展开与因式分解": [
                ("2*(a+b)", "2a+2b"),
                ("(a+b)(c+d)", "ac+ad+bc+bd"),
                ("(x+y)(x-y)", "x^2-y^2"),
                ("(a+b)^2", "2ab+a^2+b^2"),
                ("((2x)^2)", "4x^2"),
            ],
            "根号与分数": [
                ("(8x^3)^(1/2)", "2x√(2x)"),
                ("√(4)", "2"),
                ("1/√(x+1)", "(√(x+1))/(x+1)"),
                ("1/(x+1)+1", "(x+2)/(x+1)"),
                ("1/(x+1)+x/(1+x)", "1"),
                ("2/3*x", "(2/3)x"),
                ("1/2x", "(1/2)x"),
                ("(1/x)*x", "1"),
                ("(1/(x+1))*(x+1)", "1"),
                ("(3x/y)*y", "3x"),
                ("a+√(b)", "a+√(b)"),
                ("a-√(b)", "a-√(b)"),
                ("a√(b)", "a√(b)"),
                ("√(-4)", "√(-4)"),
                # 根号内多项式提取完全平方因子
                ("√(-4c^2+8d)", "2√(-c^2+2d)"),
                ("√(4x^2+8)", "2√(x^2+2)"),
                ("√(8x^2+16y^2)", "2√(2x^2+4y^2)"),
                ("√(9a^2+18b)", "3√(a^2+2b)"),
                ("√(12a+18b)", "√(12a+18b)"),
                ("√(36x+48y)", "2√(9x+12y)"),
                # 因式分解约分
                ("(x^2-1)/(x-1)", "x+1"),
                ("(x^2+2x+1)/(x+1)", "x+1"),
                ("(x^2-y^2)/(x-y)", "x+y"),
                ("(x^2-4)/(x^2-x-2)", "(x+2)/(x+1)"),
                ("(x^3-1)/(x-1)", "x+x^2+1"),
                ("(a^2-b^2)/(a+b)", "a-b"),
                # 分母共轭有理化
                ("1/(√(2)+1)", "-1+√(2)"),
                ("1/(√(2)-1)", "1+√(2)"),
                ("1/(2+√(3))", "2-√(3)"),
                ("1/(1+√(x))", "(1-√(x))/(-x+1)"),
                ("1/(√(x+1)-1)", "(-1-√(x+1))/(-x)"),
                ("1/(√(x)+1)", "(1-√(x))/(-x+1)"),
                # 多项分母共轭有理化（将多个不含根号的项视为整体）
                ("1/(x+y+√(x+y))", "(x+y-√(x+y))/(-x+2xy+x^2-y+y^2)"),
            ],
            "复杂公式": [
                ("(-b+√(b^2-4a*c))/(2a)", "(-b+√(-4ac+b^2))/2a"),
                ("(k^2+(2a-k)^2-4*(a^2-b^2))/(2k*(2a-k))", "(-2ak+2b^2+k^2)/(2ak-k^2)"),
                ("(x-(a+b)/2)^2", "(1/2)ab-ax+(1/4)a^2-bx+(1/4)b^2+x^2"),
                ("(x-((a+b)/2))^2+(y-((c+d)/2))^2",
                 "(1/2)ab-ax+(1/4)a^2-bx+(1/4)b^2+(1/2)cd-cy+(1/4)c^2-dy+(1/4)d^2+x^2+y^2"),
                ("(x-((a+b)/2))^2+(y-((c+d)/2))^2-0.25*((a-b)^2+(c-d)^2)", "ab-ax-bx+cd-cy-dy+x^2+y^2"),
            ],
            "绝对值": [
                ("|3|", "3"),
                ("|-5|", "5"),
                ("|0|", "0"),
                ("|x|", "|x|"),
                ("2*|x|", "|2x|"),
                ("x*|y|", "|xy|"),
                ("|x|+|x|", "|2x|"),  # 修改：原期望 "|x|+|x|" 改为 "|2x|"
                ("|x+1|", "|(x+1)|"),
                ("(1/2)*|x|", "|(1/2)x|"),
            ],
        }

        # 方程求解测试（按子类别分组）
        self.equation_categories = {
            "一次方程": [
                ("x+2=5", "x = 3"),
                ("2x=8", "x = 4"),
                ("3x-6=0", "x = 2"),
                ("2x+3=7", "x = 2"),
                ("x/2 = 3", "x = 6"),
                ("3x = 12", "x = 4"),
                ("x-5=0", "x = 5"),
            ],
            "二次方程": [
                ("x^2-5=0",
                 "x = √(5) 或 -√(5)"),
                ("x^2+3x-1=0",
                 "x = (-3+√(13))/(2) 或 (-3-√(13))/(2)"),
                ("x^2-5x+6=0",
                 "x = 3 或 2"),
                ("x^2-6x+9=0", "x = 3"),
                ("2x^2-5x+2=0",
                 "x = 2 或 1/2"),
                ("x^2+3x+2=0",
                 "x = -1 或 -2"),
                ("x^2+8x+16=0", "x = -4"),
                ("ax^2+c=0",
                 "多变量方程的解:\n  a = -c/x^2\n  c = -ax^2\n  x = √(-c/a) 或 -√(-c/a)"),
                ("ax^2+bx+c=0",
                 "多变量方程的解:\n  a = -b/x-c/x^2\n  b = -ax-c/x\n  c = -ax^2-bx\n  x = (-b+√(-4ac+b^2))/(2a) 或 (-b-√(-4ac+b^2))/(2a)"),
            ],
            "分式方程": [
                ("1/(x+1) = 2", "x = -1/2"),
                ("1/(x-1) = 0", "矛盾方程（无解）"),
                ("(x^2-1)/(x-1) = 0", "x = -1"),
                ("x/(x-2) = 3/(x-2)", "x = 3"),
                ("1/x + 1/(x+1) = 1",
                 "x = 1/2+(√(5))/2 或 1/2-(√(5))/2"),
            ],
            "多变量方程": [
                ("x+y=10", "多变量方程的解:\n  x = -y+10\n  y = -x+10"),
                ("(x+y)^2=0", "多变量方程的解:\n  x = -y\n  y = -x"),
                ("1/(x+1) = 2/(y-1)", "多变量方程的解:\n  x = (1/2)y-3/2\n  y = 2x+3"),
                ("(x+y)/(x-y) = 3", "多变量方程的解:\n  x = 2y\n  y = (1/2)x"),
                ("1/x + 1/y = 1", "多变量方程的解:\n  x = y/(y-1)\n  y = x/(x-1)"),
                ("1/x+1/y=1/(x+y)", "多变量方程的解:\n  x = 无实数解\n  y = 无实数解"),
                ("1/x+1/y=5/(x+y)",
                 "多变量方程的解:\n  x = (3/2+(√(5))/2)/y 或 (3/2-(√(5))/2)/y\n  y = (3/2+(√(5))/2)/x 或 (3/2-(√(5))/2)/x"),
                ("x/y + y/x = xy",
                 "多变量方程的解:\n  x = √((-y^2)/(-y^2+1)) 或 -√((-y^2)/(-y^2+1))\n  y = √((-x^2)/(-x^2+1)) 或 -√((-x^2)/(-x^2+1))"),
                ("x/y + y/x = 4x^2y",
                 "多变量方程的解:\n  x = 目前不支持求解这类方程，已化简：x^2/y-4x^3y+y\n  y = √((-x^2)/(-4x^3+1)) 或 -√((-x^2)/(-4x^3+1))"),
            ],
            "联立方程组": [
                ("x+y=5; x-y=1", "x = 3, y = 2"),
                ("x^2+y=5; x-y=1",
                 "x = 2, y = 1 或 x = -3, y = -4"),
                ("x+y=3; x-y=1; 2x=4", "x = 2, y = 1"),
                ("x+y=3; x-y=1; 2x+y=4", "无解"),
                ("x^2=4; y^2=9",
                 "x = 2, y = 3 或 x = 2, y = -3 或 x = -2, y = 3 或 x = -2, y = -3"),
                ("x^2=2; y=x+1",
                 "x = √(2), y = 1+√(2) 或 x = -√(2), y = 1-√(2)"),
                ("1/x + 1/y = 1; x+y=4", "x = 2, y = 2"),
                ("x+y=3; x+y=5", "无解"),
                ("x+y=3; 2x+2y=6; x=1", "x = 1, y = 2"),
                ("x+y+a=0;x+y=2", "a = -2, x = -y+2"),
                ("x + √(y) = 6; √(x) + y = 6",
                 "无法求解，化简后的方程为：721y-204y^2+24y^3-y^4-900"),
                ("√(x+y) = 3; x - y = 1", "x = 5, y = 4"),
                ("x+y=c; x^2+y^2=d",
                 "x = (1/2)c-(√(-c^2+2d))/2, y = (1/2)c+(√(-c^2+2d))/2 或 "
                 "x = (1/2)c+(√(-c^2+2d))/2, y = (1/2)c-(√(-c^2+2d))/2",
                 ['x', 'y']),
            ],
            "根式方程": [
                ("√(x+1) = 2", "x = 3"),
                ("√(x+5) = 1 + √(x)", "x = 4"),
                ("√(2x+3) = x", "x = 3"),
                ("√(x+7) - √(x) = 1", "x = 9"),
                ("√(x) + √(x+3) = 3", "x = 1"),
                ("√(x) = -2", "无解"),
                ("√(x-3) + √(x+2) = 0", "无解"),
                ("√(x) + 1 = 0", "无解"),
                ("√(x-1) = √(1-x)", "x = 1"),
                ("√(x^2+1) = -2", "无解"),
            ],
            "绝对值方程": [
                ("|x|=2",
                 "x = 2 或 -2"),
                ("|x-1|=3",
                 "x = 4 或 -2"),
                ("|x|+|y|=1",
                 "当 x ≥ 0 且 y ≥ 0 时，解为：x = -y+1\n"
                 "当 x ≥ 0 且 y < 0 时，解为：x = y+1\n"
                 "当 x < 0 且 y ≥ 0 时，解为：x = y-1\n"
                 "当 x < 0 且 y < 0 时，解为：x = -y-1"),
                ("|x+1|=y",
                 "当 x+1 ≥ 0 时，解为：x = y-1\n"
                 "当 x+1 < 0 时，解为：x = -y-1"),
            ],
            "3.7": [
                ("x^2+y^2=r^2; x+y=0",
                 "x = r√(1/2), y = -r√(1/2) 或 x = -r√(1/2), y = r√(1/2)",
                 ['x', 'y']),
                ("|x+y|=4; x^2+y^2=9",
                 "x = 2-(√(2))/2, y = 2+(√(2))/2 或 x = 2+(√(2))/2, y = 2-(√(2))/2 或 "
                 "x = -2-(√(2))/2, y = -2+(√(2))/2 或 x = -2+(√(2))/2, y = -2-(√(2))/2"),
                ("x^2+y^2-4x=9; x=y-1",
                 "x = (1+√(17))/2, y = (3+√(17))/2 或 x = (1-√(17))/2, y = (3-√(17))/2"),
                ("x^2+y^2+4x-4y=0; x^2+y^2+2x-12=0",
                 "x = -2+4/5√(10), y = 2+2/5√(10) 或 x = -2-4/5√(10), y = 2-2/5√(10)"),
                ("x^2/4+y^2=1; y=x",
                 "x = 2/√(5), y = 2/√(5) 或 x = -2/√(5), y = -2/√(5)"),
                ("√(x^2+1) + √(x^2+1) = 2", "x = 0"),
                ("x^2+y^2=9; x=y",
                 "x = 3/√(2), y = 3/√(2) 或 x = -3/√(2), y = -3/√(2)"),
                ("x^2+y^2=9; x=y-2",
                 "x = -1+1/2√(14), y = 1+1/2√(14) 或 x = -1-1/2√(14), y = 1-1/2√(14)"),
                ("x^2+y^2=9; x=y-1",
                 "x = (-1+√(17))/2, y = (1+√(17))/2 或 x = (-1-√(17))/2, y = (1-√(17))/2"),
            ],
        }
        self.other_categories = {  # 因式分解等功能测试
            "因式分解": [
                ("x^2-1", "(x-1)(x+1)"),
                ("x^2+2x+1", "(x+1)^2"),
                ("x^2-y^2", "(x-y)(x+y)"),
                ("x^3-y^3", "(x-y)(x^2+xy+y^2)"),
                ("2x^2+4x", "2x(x+2)"),
                ("x^2+5x+6", "(x+2)(x+3)"),
                ("xy+yz", "y(x+z)"),
                ("x^2+xy+xz+yz", "(x+y)(x+z)"),
                ("x^3+3x^2+3x+1", "(x+1)^3"),
                ("4x^2-9", "(2x-3)(2x+3)"),
                ("a^2-b^2", "(a-b)(a+b)"),
                ("x^2+3x+2", "(x+1)(x+2)"),
            ],
        }

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

        # Debug模式选择框
        debug_frame = ttk.Frame(control_frame)
        debug_frame.pack(side=tk.LEFT, padx=(0, 20))

        debug_label = ttk.Label(debug_frame, text="Debug模式:", font=('Arial', 11))
        debug_label.pack(side=tk.LEFT)

        # 创建下拉选择框，包含四个选项
        debug_levels = ["无", "简易", "正常", "详细"]
        self.debug_level_combo = ttk.Combobox(
            debug_frame,
            values=debug_levels,
            state="readonly",
            width=8,
            font=('Arial', 10)
        )
        # 从配置文件加载默认debug级别
        level_names = ["无", "简易", "正常", "详细"]
        saved_lv = self.config_manager.get("debug_level", 2)
        self.debug_level_combo.current(saved_lv if 0 <= saved_lv <= 3 else 2)
        self.debug_level_combo.pack(side=tk.LEFT, padx=(5, 0))

        # 绑定选择事件
        self.debug_level_combo.bind("<<ComboboxSelected>>", self.on_debug_level_selected)

        # 日志管理按钮
        log_frame = ttk.Frame(control_frame)
        log_frame.pack(side=tk.LEFT, padx=(0, 20))

        log_label = ttk.Label(log_frame, text="日志:", font=('Arial', 11))
        log_label.pack(side=tk.LEFT)

        view_logs_btn = ttk.Button(log_frame, text="查看日志",
                                   command=self.view_logs,
                                   style='Log.TButton', width=10)
        view_logs_btn.pack(side=tk.LEFT, padx=(5, 5))

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

        self.calc_btn = ttk.Button(op_buttons_frame, text="化简计算",
                                   command=self.calculate, style='Equal.TButton', width=15)
        self.calc_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.solve_btn = ttk.Button(op_buttons_frame, text="解方程",
                                    command=self.solve_equation, style='Solve.TButton', width=15)
        self.solve_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.factor_btn = ttk.Button(op_buttons_frame, text="因式分解",
                                     command=self.factor_expression, style='Solve.TButton', width=15)
        self.factor_btn.pack(side=tk.LEFT, padx=(0, 10))

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

        # 变量和括号按钮行
        var_frame = ttk.Frame(buttons_frame)
        var_frame.pack(fill=tk.X)

        var_buttons = ['x', 'y', 'z', 'a', 'b', 'c', '(', ')', '=', '√', '^', '|']

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

        # Debug级别显示
        self.debug_level_var = tk.StringVar()
        self.debug_level_var.set("级别: 正常")
        debug_level_display = ttk.Label(debug_control_frame, textvariable=self.debug_level_var,
                                        font=('Arial', 11, 'italic'), foreground='green')
        debug_level_display.pack(side=tk.LEFT, padx=(0, 10))

        # 显示速度选择
        speed_label = ttk.Label(debug_control_frame, text="速度:", font=('Arial', 11))
        speed_label.pack(side=tk.LEFT)
        self.debug_speed_combo = ttk.Combobox(
            debug_control_frame,
            values=["即时", "快速", "正常", "慢速", "逐条"],
            state="readonly",
            width=6,
            font=('Arial', 10)
        )
        # 从配置文件加载默认显示速度
        speed_names = ["即时", "快速", "正常", "慢速", "逐条"]
        saved_sp = self.config_manager.get("debug_speed", "正常")
        sp_idx = speed_names.index(saved_sp) if saved_sp in speed_names else 2
        self.debug_speed_combo.current(sp_idx)
        self.debug_speed_combo.pack(side=tk.LEFT, padx=(5, 15))
        self.debug_speed_combo.bind("<<ComboboxSelected>>", self.on_debug_speed_changed)

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
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)  # 修改这里：tk.Bottom -> tk.BOTTOM

        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 输入表达式或方程（如 x+2=5），Debug模式已启用，当前级别：正常")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        status_bar.pack(fill=tk.X)

    def on_debug_level_selected(self, event):
        """当选择debug级别时的回调"""
        selected = self.debug_level_combo.get()

        # 将文本选项映射到数字级别
        level_map = {
            "无": 0,
            "简易": 1,
            "正常": 2,
            "详细": 3
        }

        if selected in level_map:
            level = level_map[selected]

            # 如果选择了"无"，关闭debug模式
            if level == 0:
                self.debug_enabled.set(False)
                self.debug_status_var.set("Debug模式: 禁用")
                self.debug_level_var.set("级别: 无")
                self.status_var.set("Debug模式已禁用")
                self.debug_callback.text_widget = None
            else:
                # 选择其他级别，开启debug模式并设置级别
                self.debug_enabled.set(True)
                self.set_debug_level(level)
                self.debug_status_var.set("Debug模式: 启用")
                self.debug_callback.text_widget = self.debug_text

            # 保存配置
            self.config_manager.set("debug_level", level)
            self.config_manager.set("debug_enabled", level > 0)

    def set_debug_level(self, level):
        """设置debug级别"""
        self.debug_level.set(level)
        self.debug_callback.set_debug_level(level)

        # 更新显示
        level_text = self._get_debug_level_text()
        self.debug_level_var.set(f"级别: {level_text}")

        # 更新下拉框的选中项
        level_map = {0: "无", 1: "简易", 2: "正常", 3: "详细"}
        if level in level_map:
            self.debug_level_combo.set(level_map[level])

        if self.debug_enabled.get():
            self.status_var.set(f"Debug模式已启用，当前级别：{level_text}")
        else:
            self.status_var.set(f"Debug模式已禁用（级别：{level_text}）")

    def on_debug_speed_changed(self, event):
        """当选择debug显示速度时的回调"""
        selected = self.debug_speed_combo.get()
        self.debug_callback.set_display_speed(selected)
        self.status_var.set(f"Debug显示速度切换为：{selected}")
        # 保存配置
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
            self.debug_level_combo.set("无")
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
        self.status_var.set("已清空历史记录")

    def view_logs(self):
        """查看日志"""
        LogViewerWindow(self.root, self.log_manager)

    def append_to_expression(self, text):
        current = self.expression_var.get()
        cursor_pos = self.expression_entry.index(tk.INSERT)

        # 特殊处理绝对值函数
        if text == 'abs':
            text = 'abs()'
            new_text = current[:cursor_pos] + text + current[cursor_pos:]
            self.expression_var.set(new_text)
            new_pos = cursor_pos + 4
            self.expression_entry.icursor(new_pos)
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

    def add_to_history(self, text):
        """添加文本到历史记录"""
        self.history.append(text)
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
                    all_tests.append(("其他", test_input, expected))
                else:
                    test_input, expected, solve_vars = item
                    all_tests.append(("其他", test_input, expected, solve_vars))

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
        """判断两个解字符串是否数学等价（使用 sympy 进行数学比较）"""
        import re

        def to_sympy_expr(s):
            """将计算器格式的表达式转换为 sympy 表达式"""
            import sympy as sp
            s = s.strip().replace(' ', '')
            sqrt_char = '√'  # √
            # 递归替换 √(...) → sqrt(...)
            while sqrt_char + '(' in s:
                s = re.sub(sqrt_char + r'\(([^()]+)\)', r'sqrt(\1)', s)
            # 将 ^ 替换为 **
            s = s.replace('^', '**')
            # 处理隐式乘法
            s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
            s = re.sub(r'(\d)sqrt', r'\1*sqrt', s)
            s = re.sub(r'\)(\d)', r')*\1', s)
            return sp.sympify(s)

        def _is_sympy_slow_pattern(s):
            """检测 sympy.simplify 难以快速处理的表达式模式

            只检测"根号内含分式且分子分母均含负号"的极端情况。
            典型案例：√((-y²)/(-y²+1))
            这类表达式会让 sympy.simplify 陷入极慢的符号计算，导致界面卡死。
            不触发普通表达式如 -2-4/5√(10) 或 (1+√(17))/2。
            """
            s = s.replace(' ', '')
            sqrt_char = '√'
            # 查找每一个 √(...) 的内容
            pattern = sqrt_char + r'\(([^()]+)\)'
            for m in re.findall(pattern, s):
                content = m
                if '/' not in content:
                    continue
                # 检查分数中分子和分母是否各有负号
                parts = content.split('/')
                if len(parts) == 2:
                    num_neg = parts[0].count('-')
                    den_neg = parts[1].count('-')
                    if num_neg > 0 and den_neg > 0:
                        return True
            return False

        def compare_solution_line(exp_line, act_line):
            """比较单行解（可能包含多个变量）"""
            exp_pairs = {}
            act_pairs = {}
            for pair in re.split(r',\s*', exp_line):
                if '=' in pair:
                    var, val = pair.split('=', 1)
                    exp_pairs[var.strip()] = val.strip()
            for pair in re.split(r',\s*', act_line):
                if '=' in pair:
                    var, val = pair.split('=', 1)
                    act_pairs[var.strip()] = val.strip()

            if not exp_pairs or not act_pairs:
                return exp_line == act_line

            # 比较共同的变量
            common_vars = set(exp_pairs.keys()) & set(act_pairs.keys())
            if not common_vars:
                return False

            for var in sorted(common_vars):
                e_val = exp_pairs[var]
                a_val = act_pairs[var]

                # 快速路径：字符串完全相同则数学等价
                if e_val == a_val:
                    continue

                # 检测 sympy 难以快速处理的模式：嵌套根号 + 负号 + 分式
                # 形如 √((-y²)/(-y²+1)) 的表达式会导致 sp.simplify 极慢甚至卡死
                if _is_sympy_slow_pattern(e_val) or _is_sympy_slow_pattern(a_val):
                    # 直接回退到精确字符串比较
                    if e_val != a_val:
                        return False
                    continue

                try:
                    e_expr = to_sympy_expr(e_val)
                    a_expr = to_sympy_expr(a_val)
                    import sympy as sp
                    if sp.simplify(e_expr - a_expr) != 0:
                        return False
                except Exception:
                    # sympy 比较失败，回退到原始字符串比较
                    if e_val != a_val:
                        return False
            return True

        # 主逻辑: 按"或"分割多个解组
        exp_groups = [g.strip() for g in expected.split('或') if g.strip()]
        act_groups = [g.strip() for g in actual.split('或') if g.strip()]

        if len(exp_groups) != len(act_groups):
            return False

        # 对每个解组进行匹配
        matched_act = set()
        for exp_group in exp_groups:
            found = False
            for j, act_group in enumerate(act_groups):
                if j in matched_act:
                    continue
                if compare_solution_line(exp_group, act_group):
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

                # 兼容两种格式： (类型, 输入, 期望) 或 (类型, 输入, 期望, 求解变量列表)
                if len(test_data) == 3:
                    test_type, test_input, expected = test_data
                    solve_vars = None
                else:
                    test_type, test_input, expected, solve_vars = test_data

                progress = (i + 1) / total_tests * 100
                self.root.after(0, self._update_test_progress, progress, i + 1, total_tests, test_input)

                try:
                    if debug_cb:
                        debug_cb(f"正在测试 ({i + 1}/{total_tests}): {test_input}", level=1)

                    # 判断测试类型，调用对应的计算方法
                    if test_type == "其他":
                        result = self.calculator.factor_expression(test_input, debug_cb)
                    elif ';' in test_input and solve_vars is not None:
                        # 直接调用 solve_system 并传入变量列表
                        result = self.calculator.solve_system(test_input, solve_vars, debug_cb)
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
            self.add_to_history(f"✗ {test_type}: {test_input}")
            self.add_to_history(f"  期望: {expected}")
            self.add_to_history(f"  实际: {result}")

    def _add_test_error(self, test_type, test_input, error_msg):
        self.add_to_history(f"✗ {test_type}: {test_input} - 错误: {error_msg}")

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