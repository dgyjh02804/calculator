"""代数计算器 GUI — 核心组件：配置、日志、Debug回调"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import json
import threading
from datetime import datetime


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


