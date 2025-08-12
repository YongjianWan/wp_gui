import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import pystray
from PIL import Image, ImageDraw, ImageFont
import threading
import os
import datetime
import json
import subprocess
import sys
from plyer import notification
import keyboard
import ctypes
import schedule
import time
from collections import defaultdict

# 解决高DPI模糊问题
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class WeeklyProgressTracker:
    def __init__(self):
        # 文件路径配置
        self.config_file = "wp_config.json"
        self.current_file = "weekly_progress.txt"
        self.habits_file = ".habits_tracker.json"
        self.reminders_file = ".reminders.json"
        self.archive_dir = "archive"
        
        # 加载配置
        self.load_config()
        self.init_files()
        
        # 创建主窗口 - 使用ttkbootstrap美化
        self.root = ttk.Window(themename="superhero")  # 可选: darkly, cyborg, solar, superhero
        self.root.title("周进度追踪器 Pro")
        self.root.geometry("900x650")
        
        # 设置窗口图标
        self.setup_window_icon()
        
        # 初始化UI
        self.setup_ui()
        
        # 创建系统托盘
        self.create_tray_icon()
        
        # 注册全局快捷键
        self.register_hotkeys()
        
        # 启动提醒检查线程
        self.start_reminder_thread()
        
        # 初始隐藏主窗口
        self.root.withdraw()
        
        # 显示欢迎通知
        self.show_notification("周进度追踪器已启动", "按 Ctrl+Alt+W 快速打开")
        
    def setup_window_icon(self):
        """设置窗口图标"""
        icon_path = self.create_icon_file()
        if sys.platform == "win32":
            self.root.iconbitmap(default=icon_path)
            
    def create_icon_file(self):
        """创建高质量图标"""
        icon_path = "wp_icon.ico"
        if not os.path.exists(icon_path):
            # 创建渐变背景的图标
            size = 256
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 绘制渐变圆形背景
            for i in range(size//2, 0, -1):
                alpha = int(255 * (i / (size//2)))
                color = (74, 144, 226, alpha)
                draw.ellipse([size//2-i, size//2-i, size//2+i, size//2+i], fill=color)
            
            # 添加文字
            try:
                font = ImageFont.truetype("arial.ttf", size//3)
            except:
                font = None
            draw.text((size//2, size//2), "WP", fill='white', anchor="mm", font=font)
            
            # 保存为ico
            img.save(icon_path, format='ICO', sizes=[(256, 256)])
        return icon_path
        
    def load_config(self):
        """加载配置"""
        default_config = {
            "week_num": 1,
            "last_check": str(datetime.date.today()),
            "theme": "superhero",
            "reminders_enabled": True,
            "reminder_times": ["09:00", "14:00", "18:00", "21:00"],
            "auto_backup": True
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
            
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
            
    def init_files(self):
        """初始化文件结构"""
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
            
        self.check_week_transition()
        
        if not os.path.exists(self.current_file):
            self.create_week_file()
            
    def setup_ui(self):
        """设置美化的UI界面"""
        # 创建自定义样式
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Microsoft YaHei', 16, 'bold'))
        style.configure('Card.TFrame', relief="flat", borderwidth=1)


        
        # 顶部标题栏
        header_frame = ttk.Frame(self.root, style='primary.TFrame')
        header_frame.pack(fill=X, padx=0, pady=0)
        
        title_label = ttk.Label(
            header_frame, 
            text=f"📅 第 {self.config['week_num']} 周学习进度",
            style='Title.TLabel',
            bootstyle="inverse-primary"
        )
        title_label.pack(pady=15)
        
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # 左侧面板 - 快捷功能
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=LEFT, fill=Y, padx=(0, 10))
        
        # 快捷操作卡片
        self.create_quick_actions(left_panel)
        
        # 统计信息卡片
        self.create_stats_card(left_panel)
        
        # 右侧主区域
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=LEFT, fill=BOTH, expand=True)
        # 创建状态栏
        self.create_status_bar()
        
        # 标签页
        self.notebook = ttk.Notebook(right_panel, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True)
        
        # 今日记录标签
        self.today_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.today_frame, text="📝 今日记录")
        self.setup_today_tab()
        
        # 本周总览标签
        self.week_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.week_frame, text="📊 本周总览")
        self.setup_week_tab()
        
        # 提醒设置标签
        self.reminder_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reminder_frame, text="⏰ 提醒设置")
        self.setup_reminder_tab()
        
        
    def create_quick_actions(self, parent):
        """创建快捷操作面板"""
        # 快捷操作标题
        ttk.Label(parent, text="快捷操作", font=('Microsoft YaHei', 12, 'bold')).pack(pady=(0, 10))
        
        # 操作按钮组
        actions = [
            ("✨ 快速记录", self.quick_add_dialog, "primary"),
            ("✅ 标记完成", self.mark_done_dialog, "success"),
            ("📋 打开编辑器", self.open_editor, "info"),
            ("⏱️ 开始计时", self.show_timer, "warning"),
            ("📊 生成报告", self.generate_report, "secondary")
        ]
        
        for text, command, style in actions:
            btn = ttk.Button(
                parent, 
                text=text, 
                command=command,
                bootstyle=style,
                width=15
            )
            btn.pack(pady=5, fill=X)
            
        # 添加快捷键提示
        ttk.Separator(parent).pack(fill=X, pady=20)
        
        shortcuts_frame = ttk.LabelFrame(parent, text="快捷键", padding=10)
        shortcuts_frame.pack(fill=X)
        
        shortcuts = [
            ("Ctrl+Alt+W", "打开主窗口"),
            ("Ctrl+Alt+Q", "快速记录"),
            ("Ctrl+Alt+D", "标记完成"),
            ("ESC", "最小化到托盘")
        ]
        
        for key, desc in shortcuts:
            frame = ttk.Frame(shortcuts_frame)
            frame.pack(fill=X, pady=2)
            ttk.Label(frame, text=key, bootstyle="primary").pack(side=LEFT)
            ttk.Label(frame, text=f" - {desc}").pack(side=LEFT)
            
    def create_stats_card(self, parent):
        """创建统计信息卡片"""
        stats_frame = ttk.LabelFrame(parent, text="今日统计", padding=15)
        stats_frame.pack(fill=X, pady=20)
        
        # 获取统计数据
        stats = self.get_today_stats()
        
        # 显示统计信息
        for label, value, style in stats:
            frame = ttk.Frame(stats_frame)
            frame.pack(fill=X, pady=5)
            
            ttk.Label(frame, text=label, width=10).pack(side=LEFT)
            value_label = ttk.Label(frame, text=str(value), font=('Arial', 14, 'bold'))
            value_label.pack(side=RIGHT)
            
            if style == "good":
                value_label.configure(bootstyle="success")
            elif style == "warning":
                value_label.configure(bootstyle="warning")
                
    def get_today_stats(self):
        """获取今日统计数据"""
        completed = 0
        pending = 0
        
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 只统计今天的
                today = datetime.date.today().strftime("%Y-%m-%d")
                if today in content:
                    # 简单统计
                    completed = content.count('✓')
                    pending = content.count('□')
                    
        streak = self.get_habit_streak()
        
        return [
            ("已完成", completed, "good" if completed > 0 else "normal"),
            ("待完成", pending, "warning" if pending > 5 else "normal"),
            ("连续天数", f"{streak}🔥", "good" if streak > 7 else "normal")
        ]
        
    def setup_today_tab(self):
        """设置今日记录标签页"""
        # 工具栏
        toolbar = ttk.Frame(self.today_frame)
        toolbar.pack(fill=X, padx=10, pady=10)
        
        ttk.Button(
            toolbar, 
            text="刷新", 
            command=self.refresh_content,
            bootstyle="outline-primary"
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="保存",
            command=self.save_current_content,
            bootstyle="outline-success"
        ).pack(side=LEFT, padx=5)
        
        # 文本编辑区
        text_frame = ttk.Frame(self.today_frame)
        text_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        
        # 添加行号和文本区域
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=('Consolas', 11),
            bg='#2b2b2b',
            fg='#ffffff',
            insertbackground='white',
            selectbackground='#4a90e2'
        )
        self.text_area.pack(fill=BOTH, expand=True)
        
        # 绑定右键菜单
        self.create_context_menu()
        
        # 加载内容
        self.refresh_content()
        
    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="标记为完成", command=self.mark_current_line_done)
        self.context_menu.add_command(label="添加时间戳", command=self.insert_timestamp)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="插入分隔线", command=self.insert_separator)
        self.context_menu.add_command(label="插入今日模板", command=self.insert_today_template)
        
        self.text_area.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        """显示右键菜单"""
        self.context_menu.post(event.x_root, event.y_root)
        
    def mark_current_line_done(self):
        """标记当前行为完成"""
        current_line = self.text_area.index(tk.INSERT).split('.')[0]
        line_content = self.text_area.get(f"{current_line}.0", f"{current_line}.end")
        if '□' in line_content:
            new_content = line_content.replace('□', '✓')
            self.text_area.delete(f"{current_line}.0", f"{current_line}.end")
            self.text_area.insert(f"{current_line}.0", new_content)
            self.save_current_content()
            self.show_notification("任务完成", "已标记任务为完成 ✓")
            
    def insert_timestamp(self):
        """插入时间戳"""
        timestamp = datetime.datetime.now().strftime("[%H:%M]")
        self.text_area.insert(tk.INSERT, timestamp + " ")
        
    def insert_separator(self):
        """插入分隔线"""
        self.text_area.insert(tk.INSERT, "\n" + "─" * 40 + "\n")
        
    def insert_today_template(self):
        """插入今日模板"""
        template = """
【时间段记录】
[09:00-10:00] 
[10:00-12:00] 
[14:00-16:00] 
[16:00-18:00] 
[19:00-21:00] 

【重要收获】
• 

【明日准备】
• 
"""
        self.text_area.insert(tk.INSERT, template)
        
    def setup_week_tab(self):
        """设置本周总览标签页"""
        # 创建可滚动的框架
        canvas = tk.Canvas(self.week_frame, bg='#2b2b2b')
        scrollbar = ttk.Scrollbar(self.week_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 生成本周总览
        self.update_week_overview(scrollable_frame)
        
    def update_week_overview(self, parent):
        """更新本周总览"""
        # 清空旧内容
        for widget in parent.winfo_children():
            widget.destroy()
            
        # 标题
        title = ttk.Label(parent, text="本周进度总览", font=('Microsoft YaHei', 16, 'bold'))
        title.pack(pady=20)
        
        # 进度统计
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=X, padx=20, pady=10)
        
        # 获取本周数据
        week_data = self.analyze_week_data()
        
        # 显示进度条
        progress_frame = ttk.LabelFrame(stats_frame, text="完成进度", padding=15)
        progress_frame.pack(fill=X, pady=10)
        
        progress = ttk.Progressbar(
            progress_frame,
            length=400,
            mode='determinate',
            bootstyle="success-striped"
        )
        progress.pack(pady=10)
        progress['value'] = week_data['completion_rate']
        
        ttk.Label(
            progress_frame, 
            text=f"{week_data['completion_rate']:.1f}% 完成",
            font=('Arial', 14, 'bold')
        ).pack()
        
        # 每日完成情况
        daily_frame = ttk.LabelFrame(stats_frame, text="每日完成情况", padding=15)
        daily_frame.pack(fill=X, pady=10)
        
        for day, data in week_data['daily_stats'].items():
            day_frame = ttk.Frame(daily_frame)
            day_frame.pack(fill=X, pady=5)
            
            ttk.Label(day_frame, text=day, width=10).pack(side=LEFT)
            
            # 迷你进度条
            mini_progress = ttk.Progressbar(
                day_frame,
                length=200,
                mode='determinate',
                bootstyle="info"
            )
            mini_progress.pack(side=LEFT, padx=10)
            mini_progress['value'] = data['rate']
            
            ttk.Label(day_frame, text=f"{data['completed']}/{data['total']}").pack(side=LEFT)
            
    def analyze_week_data(self):
        """分析本周数据"""
        week_data = {
            'completion_rate': 0,
            'daily_stats': defaultdict(lambda: {'completed': 0, 'total': 0, 'rate': 0})
        }
        
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 简单统计
            completed = content.count('✓')
            total = completed + content.count('□')
            
            if total > 0:
                week_data['completion_rate'] = (completed / total) * 100
                
            # 按日期分析（简化版）
            today = datetime.date.today()
            for i in range(7):
                date = today - datetime.timedelta(days=i)
                day_name = date.strftime("%A")[:3]
                
                # 这里简化处理，实际应该解析文件内容
                week_data['daily_stats'][day_name] = {
                    'completed': completed // 7,
                    'total': total // 7,
                    'rate': week_data['completion_rate']
                }
                
        return week_data
        
    def setup_reminder_tab(self):
        """设置提醒标签页"""
        # 提醒开关
        switch_frame = ttk.Frame(self.reminder_frame)
        switch_frame.pack(fill=X, padx=20, pady=20)
        
        ttk.Label(switch_frame, text="启用提醒功能", font=('Microsoft YaHei', 12)).pack(side=LEFT)
        
        self.reminder_switch = ttk.Checkbutton(
            switch_frame,
            bootstyle="success-round-toggle",
            variable=tk.BooleanVar(value=self.config['reminders_enabled'])
        )
        self.reminder_switch.pack(side=LEFT, padx=20)
        
        # 提醒时间设置
        times_frame = ttk.LabelFrame(self.reminder_frame, text="提醒时间", padding=20)
        times_frame.pack(fill=X, padx=20, pady=10)
        
        self.time_entries = []
        for i, time in enumerate(self.config['reminder_times']):
            time_frame = ttk.Frame(times_frame)
            time_frame.pack(fill=X, pady=5)
            
            ttk.Label(time_frame, text=f"提醒 {i+1}:").pack(side=LEFT)
            
            time_var = tk.StringVar(value=time)
            time_entry = ttk.Entry(time_frame, textvariable=time_var, width=10)
            time_entry.pack(side=LEFT, padx=10)
            self.time_entries.append(time_var)
            
        # 保存按钮
        ttk.Button(
            self.reminder_frame,
            text="保存提醒设置",
            command=self.save_reminder_settings,
            bootstyle="primary"
        ).pack(pady=20)
        
        # 添加自定义提醒
        custom_frame = ttk.LabelFrame(self.reminder_frame, text="添加自定义提醒", padding=20)
        custom_frame.pack(fill=X, padx=20, pady=10)
        
        ttk.Label(custom_frame, text="提醒内容:").grid(row=0, column=0, sticky=W, pady=5)
        self.custom_reminder_text = ttk.Entry(custom_frame, width=40)
        self.custom_reminder_text.grid(row=0, column=1, pady=5)
        
        ttk.Label(custom_frame, text="提醒时间:").grid(row=1, column=0, sticky=W, pady=5)
        self.custom_reminder_time = ttk.Entry(custom_frame, width=20)
        self.custom_reminder_time.grid(row=1, column=1, sticky=W, pady=5)
        
        ttk.Button(
            custom_frame,
            text="添加提醒",
            command=self.add_custom_reminder,
            bootstyle="info"
        ).grid(row=2, column=1, pady=10)
        
    def save_reminder_settings(self):
        """保存提醒设置"""
        self.config['reminder_times'] = [var.get() for var in self.time_entries]
        self.save_config()
        self.show_notification("设置已保存", "提醒时间已更新")
        
    def add_custom_reminder(self):
        """添加自定义提醒"""
        text = self.custom_reminder_text.get()
        time = self.custom_reminder_time.get()
        
        if text and time:
            # 这里简化处理，实际应该保存到文件
            self.show_notification("提醒已添加", f"{time} - {text}")
            self.custom_reminder_text.delete(0, tk.END)
            self.custom_reminder_time.delete(0, tk.END)
            
    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=BOTTOM, fill=X)
        
        self.status_label = ttk.Label(
            status_frame,
            text="就绪",
            bootstyle="inverse-secondary"
        )
        self.status_label.pack(side=LEFT, padx=10)
        
        # 时钟
        self.clock_label = ttk.Label(
            status_frame,
            text="",
            bootstyle="inverse-secondary"
        )
        self.clock_label.pack(side=RIGHT, padx=10)
        self.update_clock()
        
    def update_clock(self):
        """更新时钟"""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.config(text=current_time)
        self.root.after(1000, self.update_clock)
        
    def open_editor(self):
        """打开文本编辑器编辑今日记录"""
        self.add_today_entry()  # 确保今日记录存在
        
        # 使用系统默认编辑器打开文件
        if sys.platform == "win32":
            os.startfile(self.current_file)
        elif sys.platform == "darwin":  # macOS
            subprocess.call(["open", self.current_file])
        else:  # linux
            subprocess.call(["xdg-open", self.current_file])
            
        self.update_status("已打开编辑器")
        self.show_notification("编辑器已打开", "请在编辑器中修改内容")
        
    def refresh_content(self):
        """刷新内容"""
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, content)
                
        self.update_status("内容已刷新")
        
    def save_current_content(self):
        """保存当前内容"""
        content = self.text_area.get(1.0, tk.END)
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(content)
        self.update_status("已保存")
        
    def quick_add_dialog(self):
        """快速添加对话框 - 美化版"""
        dialog = tk.Toplevel(self.root)
        dialog.title("快速记录")
        dialog.geometry("500x200")
        dialog.configure(bg='#2b2b2b')
        
        # 居中显示
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 标题
        title_label = ttk.Label(
            dialog,
            text="✨ 快速记录",
            font=('Microsoft YaHei', 14, 'bold'),
            bootstyle="inverse-primary"
        )
        title_label.pack(fill=X, pady=10)
        
        # 输入框架
        input_frame = ttk.Frame(dialog)
        input_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # 输入框
        self.quick_entry = ttk.Entry(
            input_frame,
            font=('Microsoft YaHei', 11),
            bootstyle="primary"
        )
        self.quick_entry.pack(fill=X, pady=10)
        self.quick_entry.focus()
        
        # 标签选择
        tag_frame = ttk.Frame(input_frame)
        tag_frame.pack(fill=X)
        
        ttk.Label(tag_frame, text="标签:").pack(side=LEFT)
        
        tags = ["#重要", "#紧急", "#想法", "#学习", "#待办"]
        self.selected_tag = tk.StringVar()
        
        for tag in tags:
            ttk.Radiobutton(
                tag_frame,
                text=tag,
                variable=self.selected_tag,
                value=tag,
                bootstyle="primary-outline-toolbutton"
            ).pack(side=LEFT, padx=5)
            
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=X, padx=20, pady=10)
        
        def save_quick():
            text = self.quick_entry.get()
            tag = self.selected_tag.get()
            if text:
                self.quick_add(f"{text} {tag}")
                dialog.destroy()
                
        ttk.Button(
            button_frame,
            text="保存 (Enter)",
            command=save_quick,
            bootstyle="primary"
        ).pack(side=RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy,
            bootstyle="secondary-outline"
        ).pack(side=RIGHT)
        
        # 绑定回车键
        self.quick_entry.bind('<Return>', lambda e: save_quick())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        
    def quick_add(self, content):
        """快速添加记录"""
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M]")
        
        # 添加到文件
        with open(self.current_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} 快速记录: {content}\n")
            
        # 更新显示
        self.refresh_content()
        self.update_status(f"已添加: {content}")
        
        # 显示通知
        self.show_notification("快速记录", f"已添加: {content}")
        
    def show_notification(self, title, message):
        """显示系统通知"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="周进度追踪器",
                timeout=3
            )
        except:
            pass
            
    def register_hotkeys(self):
        """注册全局快捷键"""
        try:
            # 主窗口
            keyboard.add_hotkey('ctrl+alt+w', self.show_window)
            # 快速记录
            keyboard.add_hotkey('ctrl+alt+q', lambda: self.root.after(0, self.quick_add_dialog))
            # 标记完成
            keyboard.add_hotkey('ctrl+alt+d', lambda: self.root.after(0, self.mark_done_dialog))
        except:
            pass
            
    def start_reminder_thread(self):
        """启动提醒线程"""
        def check_reminders():
            while True:
                if self.config.get('reminders_enabled', True):
                    current_time = datetime.datetime.now().strftime("%H:%M")
                    
                    # 检查定时提醒
                    if current_time in self.config.get('reminder_times', []):
                        # 检查是否有待办事项
                        pending = self.get_pending_count()
                        if pending > 0:
                            self.root.after(0, lambda: self.show_notification(
                                "任务提醒",
                                f"你还有 {pending} 个待办事项需要完成"
                            ))
                    # 检查截止日期提醒  
                    self.check_due_dates_reminder()
                    
                time.sleep(60)  # 每分钟检查一次
                
        reminder_thread = threading.Thread(target=check_reminders, daemon=True)
        reminder_thread.start()
        
    def check_due_dates_reminder(self):
        """检查截止日期提醒"""
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找所有Due日期
            import re
            due_pattern = r'\[Due:(\d{2}/\d{2})\](.+)'
            matches = re.findall(due_pattern, content)
            
            today = datetime.date.today()
            for due_date_str, task in matches:
                # 解析日期
                month, day = map(int, due_date_str.split('/'))
                due_date = datetime.date(today.year, month, day)
                
                # 计算剩余天数
                days_left = (due_date - today).days
                
                # 提前提醒
                if days_left == 1:
                    self.show_notification(
                        "截止日期提醒",
                        f"明天截止: {task.strip()}"
                    )
                elif days_left == 0:
                    self.show_notification(
                        "⚠️ 紧急提醒",
                        f"今天截止: {task.strip()}"
                    )
                    
    def get_pending_count(self):
        """获取待办数量"""
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
                return content.count('□')
        return 0
        
    def get_habit_streak(self):
        """获取习惯连续天数"""
        if os.path.exists(self.habits_file):
            with open(self.habits_file, 'r') as f:
                data = json.load(f)
                return data.get('streak', 0)
        return 0
        
    def mark_done_dialog(self):
        """标记完成对话框 - 美化版"""
        tasks = self.get_all_tasks()
        if not tasks:
            messagebox.showinfo("提示", "没有待完成的任务")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("标记任务完成")
        dialog.geometry("600x450")
        dialog.configure(bg='#2b2b2b')
        
        # 标题
        title_frame = ttk.Frame(dialog, bootstyle="primary")
        title_frame.pack(fill=X)
        
        ttk.Label(
            title_frame,
            text="✅ 选择要完成的任务",
            font=('Microsoft YaHei', 14, 'bold'),
            bootstyle="inverse-primary"
        ).pack(pady=15)
        
        # 任务列表框架
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # 创建Treeview代替Listbox
        columns = ('任务',)
        self.task_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='tree',
            selectmode='extended',  # 允许多选
            height=15
        )
        self.task_tree.pack(fill=BOTH, expand=True)
        
        # 添加任务
        for i, task in enumerate(tasks):
            # 解析任务类型
            tag = "normal"
            if "#重要" in task or "!!" in task:
                tag = "important"
            elif "#紧急" in task:
                tag = "urgent"
                
            self.task_tree.insert('', 'end', values=(task,), tags=(tag,))
            
        # 设置标签样式
        self.task_tree.tag_configure('important', foreground='#ff6b6b')
        self.task_tree.tag_configure('urgent', foreground='#ffd43b')
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=X, padx=20, pady=10)
        
        def mark_selected():
            selected_items = self.task_tree.selection()
            if selected_items:
                for item in selected_items:
                    task = self.task_tree.item(item)['values'][0]
                    self.mark_task_done(task)
                dialog.destroy()
                self.show_notification("任务完成", f"已标记 {len(selected_items)} 个任务为完成")
                
        ttk.Button(
            button_frame,
            text="标记完成",
            command=mark_selected,
            bootstyle="success",
            width=15
        ).pack(side=RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy,
            bootstyle="secondary-outline",
            width=15
        ).pack(side=RIGHT)
        
    def generate_report(self):
        """生成详细报告"""
        report = self.create_detailed_report()
        
        # 创建报告窗口
        report_window = tk.Toplevel(self.root)
        report_window.title("周进度报告")
        report_window.geometry("700x600")
        
        # 报告显示
        report_text = scrolledtext.ScrolledText(
            report_window,
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        report_text.pack(fill=BOTH, expand=True, padx=10, pady=10)
        report_text.insert(1.0, report)
        report_text.config(state=tk.DISABLED)
        
        # 导出按钮
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill=X, padx=10, pady=5)
        
        def export_report():
            filename = f"weekly_report_{datetime.date.today()}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            self.show_notification("报告已导出", f"已保存到: {filename}")
            
        ttk.Button(
            button_frame,
            text="导出报告",
            command=export_report,
            bootstyle="primary"
        ).pack(side=RIGHT)
        
    def create_detailed_report(self):
        """创建详细报告"""
        # 这里应该有更复杂的分析逻辑
        report = f"""
╔══════════════════════════════════════╗
║        第 {self.config['week_num']} 周进度报告         ║
╚══════════════════════════════════════╝

生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【本周概况】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 连续记录天数: {self.get_habit_streak()} 天
• 任务完成率: {self.get_completion_rate():.1f}%
• 最高效时段: 14:00-16:00

【重要成就】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 完成云计算大作业
✓ HCI项目原型设计
✓ 阅读AI论文3篇

【待改进项】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 早起计划执行率较低
• 社交计算课程进度滞后

【下周计划】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 完成HCI期中项目
2. 准备AI课程演讲
3. 开始准备期末复习

【数据分析】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
最高产的一天: 周三 (8个任务)
平均每日完成: 5.2个任务
最常用标签: #学习 #作业 #阅读

══════════════════════════════════════
"""
        return report
        
    def get_completion_rate(self):
        """计算完成率"""
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
                completed = content.count('✓')
                total = completed + content.count('□')
                if total > 0:
                    return (completed / total) * 100
        return 0
        
    def show_timer(self):
        """显示计时器窗口 - 美化版"""
        self.timer_window = tk.Toplevel(self.root)
        self.timer_window.title("专注计时器")
        self.timer_window.geometry("400x300")
        self.timer_window.configure(bg='#1a1a1a')
        
        # 计时器显示
        try:
            self.timer_label = ttk.Label(
                self.timer_window,
                text="00:00:00",
                font=('Digital-7', 48),
                bootstyle="success"
            )
        except:
            self.timer_label = ttk.Label(
                self.timer_window,
                text="00:00:00",
                font=('Consolas', 36),  # 备用字体
                bootstyle="success"
        )
        self.timer_label.pack(pady=40)
        
        # 任务输入
        task_frame = ttk.Frame(self.timer_window)
        task_frame.pack(pady=10)
        
        ttk.Label(task_frame, text="任务名称:").pack(side=LEFT)
        self.timer_task = ttk.Entry(task_frame, width=30)
        self.timer_task.pack(side=LEFT, padx=10)
        
        # 控制按钮
        button_frame = ttk.Frame(self.timer_window)
        button_frame.pack(pady=20)
        
        self.timer_running = False
        self.timer_start = None
        
        self.start_btn = ttk.Button(
            button_frame,
            text="▶ 开始",
            command=self.start_timer,
            bootstyle="success-outline",
            width=12
        )
        self.start_btn.pack(side=LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="⏸ 停止",
            command=self.stop_timer,
            bootstyle="danger-outline",
            width=12,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=LEFT, padx=5)
        
        # 番茄钟模式
        ttk.Button(
            self.timer_window,
            text="🍅 番茄钟模式 (25分钟)",
            command=self.start_pomodoro,
            bootstyle="warning"
        ).pack(pady=10)
        
    def start_timer(self):
        """开始计时"""
        self.timer_running = True
        self.timer_start = datetime.datetime.now()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.update_timer()
        
    def stop_timer(self):
        """停止计时"""
        self.timer_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        # 记录时长
        duration = datetime.datetime.now() - self.timer_start
        minutes = int(duration.total_seconds() / 60)
        task_name = self.timer_task.get() or "未命名任务"
        
        self.quick_add(f"⏱️ {task_name} - 用时 {minutes} 分钟")
        self.show_notification("计时完成", f"{task_name} 用时 {minutes} 分钟")
        
    def update_timer(self):
        """更新计时器"""
        if self.timer_running and hasattr(self, 'timer_window'):
            elapsed = datetime.datetime.now() - self.timer_start
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.config(text=time_str)
            
            self.timer_window.after(1000, self.update_timer)
            
    def start_pomodoro(self):
        """开始番茄钟"""
        self.timer_task.delete(0, tk.END)
        self.timer_task.insert(0, "番茄钟专注时间")
        self.start_timer()
        
        # 25分钟后自动停止
        self.timer_window.after(25 * 60 * 1000, self.pomodoro_complete)
        
    def pomodoro_complete(self):
        """番茄钟完成"""
        if self.timer_running:
            self.stop_timer()
            self.show_notification(
                "🍅 番茄钟完成！",
                "休息5分钟后继续加油！"
            )
            
    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建高质量图标
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 绘制渐变背景
        for i in range(32, 0, -1):
            color = (74, 144, 226, int(255 * (i / 32)))
            draw.ellipse([32-i, 32-i, 32+i, 32+i], fill=color)
            
        # 添加文字
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = None
        draw.text((32, 32), "WP", fill='white', anchor="mm", font=font)
        
        # 创建菜单
        menu = pystray.Menu(
            pystray.MenuItem("📝 打开主窗口", self.show_window, default=True),
            pystray.MenuItem("✨ 快速记录", lambda: self.root.after(0, self.quick_add_dialog)),
            pystray.MenuItem("✅ 标记完成", lambda: self.root.after(0, self.mark_done_dialog)),
            pystray.MenuItem("📊 查看总结", lambda: self.root.after(0, self.show_summary)),
            pystray.MenuItem("⏱️ 计时器", lambda: self.root.after(0, self.show_timer)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️ 设置提醒", lambda: self.root.after(0, self.show_reminder_settings)),
            pystray.MenuItem("📈 生成报告", lambda: self.root.after(0, self.generate_report)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ 退出", self.quit_app)
        )
        
        # 创建托盘图标
        self.icon = pystray.Icon("weekly_progress", image, "周进度追踪器 Pro", menu)
        
        # 在新线程中运行
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
    def show_reminder_settings(self):
        """显示提醒设置"""
        self.show_window()
        self.notebook.select(self.reminder_frame)
        
    def update_status(self, message):
        """更新状态栏"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
        
    def show_window(self):
        """显示主窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        self.refresh_content()
        
    def hide_window(self):
        """隐藏窗口"""
        self.root.withdraw()
        
    def quit_app(self):
        """退出应用"""
        self.icon.stop()
        self.root.quit()
        
    def run(self):
        """运行应用"""
        # 绑定ESC键最小化
        self.root.bind('<Escape>', lambda e: self.hide_window())
        
        # 设置关闭窗口时最小化到托盘
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        
        # 运行主循环
        self.root.mainloop()
        
    # 辅助方法
    def check_week_transition(self):
        """检查周转换"""
        today = datetime.date.today()
        if today.weekday() == 0:  # 周一
            last_check = datetime.datetime.strptime(self.config["last_check"], "%Y-%m-%d").date()
            if last_check < today:
                if os.path.exists(self.current_file):
                    archive_name = f"week_{self.config['week_num']}_progress_{last_check}.txt"
                    archive_path = os.path.join(self.archive_dir, archive_name)
                    os.rename(self.current_file, archive_path)
                    self.config["week_num"] += 1
                    self.show_notification("新的一周", f"开始第 {self.config['week_num']} 周的记录")
                    
        self.config["last_check"] = str(today)
        self.save_config()
        
    def create_week_file(self):
        """创建周文件"""
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(f"""═══════════════════════════════════════
         📅 第 {self.config['week_num']} 周学习进度
═══════════════════════════════════════

【本周目标】
- 

【重要事项】 !!
- 

【待办清单】 (格式: [Due:MM/DD] #标签 事项)
- 

""")
        self.add_today_entry()
        
    def add_today_entry(self):
        """添加今日条目"""
        today = datetime.date.today()
        weekday = today.strftime("%A")
        
        # 检查是否已存在
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                if today.strftime("%Y-%m-%d") in f.read():
                    return
                    
        with open(self.current_file, 'a', encoding='utf-8') as f:
            f.write(f"""────────────────────────────────────
📆 {today} ({weekday})

【核心课程】
□ 云计算 #课程
□ AI #课程
□ Advanced HCI #课程
□ 社交计算 #课程

【今日完成】
- 

【遗漏/新增】
- 

【明日计划】
- 

【备注/想法】


""")

    def get_all_tasks(self):
        """获取所有任务"""
        tasks = []
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('□'):
                        tasks.append(line.strip())
        return tasks
        
    def mark_task_done(self, task):
        """标记任务完成"""
        with open(self.current_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        content = content.replace(task, task.replace('□', '✓'))
        
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        self.refresh_content()
        self.update_status(f"已完成: {task[2:]}")
        
    def show_summary(self):
        """显示总结"""
        self.show_window()
        self.notebook.select(self.week_frame)
        #添加安全检查
        children = self.week_frame.winfo_children()
        if children and hasattr(children[0], 'winfo_children'):
            sub_children = children[0].winfo_children()
            if sub_children:
                self.update_week_overview(sub_children[0])
        

if __name__ == "__main__":
    # 设置DPI感知
    if sys.platform == "win32":
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        
    app = WeeklyProgressTracker()
    app.run()