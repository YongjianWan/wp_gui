import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import pystray
from PIL import Image, ImageDraw
import threading
import os
import datetime
import json
import subprocess
import sys
import time
import winreg  # Windows注册表操作
try:
    from plyer import notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False
    print("提示: 安装 plyer 可启用桌面通知功能: pip install plyer")

# 设置控制台编码为UTF-8（Windows）
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

class WeeklyTracker:
    """周记应用 - 完全修复版本"""
    
    def __init__(self):
        # 文件路径配置
        self.config_file = "wp_config.json"
        self.current_file = "weekly_progress.txt"
        self.archive_dir = "archive"
        
        # 初始化变量
        self.icon = None
        self.context_menu = None
        self.is_closing = False
        
        # 加载配置和初始化文件
        self.load_config()
        self.init_files()
        
        # 创建主窗口
        self.create_main_window()
        
        # 初始化UI
        self.setup_ui()
        
        # 创建系统托盘
        self.create_tray_icon()
        
        # 启动提醒功能
        self.start_reminder_timer()
        
        # 初始隐藏主窗口
        self.root.withdraw()
        
        # 显示启动信息
        print("Weekly Tracker 启动成功！")
        self.show_notification("Weekly Tracker", "应用已启动，可在系统托盘中访问")
        
    def create_main_window(self):
        """创建主窗口"""
        try:
            self.root = tk.Tk()
            self.root.title("Weekly Tracker")
            self.root.geometry("1000x700")
            self.root.minsize(800, 600)
            
            # 设置窗口图标（安全方式）
            self.setup_window_icon()
            
            # 配置样式
            self.setup_styles()
            
        except Exception as e:
            print(f"创建主窗口错误: {e}")
            
    def setup_window_icon(self):
        """设置窗口图标"""
        try:
            if os.path.exists("wp_icon.ico") and sys.platform == "win32":
                self.root.iconbitmap(default="wp_icon.ico")
        except Exception as e:
            print(f"设置图标失败: {e}")
            
    def setup_styles(self):
        """设置样式"""
        try:
            style = ttk.Style()
            style.theme_use('clam')
            
            # 配置样式
            style.configure('Title.TLabel', font=('Microsoft YaHei', 14, 'bold'))
            style.configure('Status.TLabel', font=('Microsoft YaHei', 9))
            
        except Exception as e:
            print(f"设置样式失败: {e}")
            
    def load_config(self):
        """加载配置"""
        default_config = {
            "week_num": 1,
            "last_check": str(datetime.date.today()),
            "theme": "clam",
            "font_size": 11,
            "auto_save": True,
            "auto_startup": False,
            "reminder_enabled": True,
            "reminder_intervals": [9, 14, 18, 21],  # 提醒时间（小时）
            "last_reminder": ""
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                self.config = default_config.copy()
                self.config.update(loaded_config)
            else:
                self.config = default_config
            self.save_config()
        except Exception as e:
            print(f"配置加载错误: {e}")
            self.config = default_config
            
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"配置保存错误: {e}")
            
    def init_files(self):
        """初始化文件结构"""
        try:
            # 创建归档目录
            if not os.path.exists(self.archive_dir):
                os.makedirs(self.archive_dir)
            
            # 检查周转换
            self.check_week_transition()
            
            # 创建周文件
            if not os.path.exists(self.current_file):
                self.create_week_file()
        except Exception as e:
            print(f"文件初始化错误: {e}")
            
    def setup_ui(self):
        """设置UI界面"""
        try:
            # 创建主框架
            main_frame = ttk.Frame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 顶部工具栏
            self.create_toolbar(main_frame)
            
            # 主内容区域
            self.create_main_content(main_frame)
            
            # 底部状态栏
            self.create_status_bar(main_frame)
            
            # 初始化内容
            self.refresh_content()
            
        except Exception as e:
            print(f"UI初始化错误: {e}")
            
    def create_toolbar(self, parent):
        """创建顶部工具栏"""
        try:
            toolbar = ttk.Frame(parent)
            toolbar.pack(fill=tk.X, pady=(0, 10))
            
            # 左侧标题
            title_label = ttk.Label(
                toolbar,
                text=f"第 {self.config.get('week_num', 1)} 周记录",
                style='Title.TLabel'
            )
            title_label.pack(side=tk.LEFT, padx=10, pady=10)
            
            # 右侧按钮组
            button_frame = ttk.Frame(toolbar)
            button_frame.pack(side=tk.RIGHT, padx=10, pady=5)
            
            # 按钮列表
            buttons = [
                ("📝 快记", self.quick_note),
                ("✅ 任务", self.show_tasks),
                ("📊 总结", self.show_summary),
                ("⚙️ 设置", self.show_settings)
            ]
            
            for text, command in buttons:
                btn = ttk.Button(
                    button_frame,
                    text=text,
                    command=command,
                    width=8
                )
                btn.pack(side=tk.LEFT, padx=2)
        except Exception as e:
            print(f"创建工具栏错误: {e}")
            
    def create_main_content(self, parent):
        """创建主内容区域"""
        try:
            content_frame = ttk.Frame(parent)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # 创建PanedWindow实现分割窗口
            paned = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
            paned.pack(fill=tk.BOTH, expand=True)
            
            # 左侧：今日记录
            left_frame = ttk.LabelFrame(paned, text=" 今日记录", padding=10)
            paned.add(left_frame, weight=3)
            
            # 文本编辑区域
            self.create_text_editor(left_frame)
            
            # 右侧：功能面板
            right_frame = ttk.Frame(paned)
            paned.add(right_frame, weight=1)
            
            # 任务面板
            self.create_task_panel(right_frame)
            
            # 快捷操作
            self.create_quick_actions(right_frame)
            
        except Exception as e:
            print(f"创建主内容错误: {e}")
            
    def create_text_editor(self, parent):
        """创建文本编辑器"""
        try:
            # 工具栏
            editor_toolbar = ttk.Frame(parent)
            editor_toolbar.pack(fill=tk.X, pady=(0, 5))
            
            # 左侧按钮
            ttk.Button(editor_toolbar, text=" 保存", command=self.save_content, width=8).pack(side=tk.LEFT, padx=2)
            ttk.Button(editor_toolbar, text=" 刷新", command=self.refresh_content, width=8).pack(side=tk.LEFT, padx=2)
            ttk.Button(editor_toolbar, text=" 模板", command=self.insert_template, width=8).pack(side=tk.LEFT, padx=2)
            
            # 右侧状态
            status_frame = ttk.Frame(editor_toolbar)
            status_frame.pack(side=tk.RIGHT)
            
            self.word_count_label = ttk.Label(status_frame, text="字数: 0", style='Status.TLabel')
            self.word_count_label.pack(side=tk.RIGHT, padx=5)
            
            self.save_status_label = ttk.Label(status_frame, text="已保存", style='Status.TLabel')
            self.save_status_label.pack(side=tk.RIGHT, padx=5)
            
            # 文本区域
            text_frame = ttk.Frame(parent)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            self.text_area = scrolledtext.ScrolledText(
                text_frame,
                wrap=tk.WORD,
                font=('Consolas', self.config.get('font_size', 11)),
                relief='solid',
                borderwidth=1,
                undo=True
            )
            self.text_area.pack(fill=tk.BOTH, expand=True)
            
            # 绑定事件
            self.text_area.bind('<KeyRelease>', self.on_text_change)
            self.text_area.bind('<Button-3>', self.show_context_menu)
            
            # 创建右键菜单
            self.create_context_menu()
            
        except Exception as e:
            print(f"创建文本编辑器错误: {e}")
            
    def create_context_menu(self):
        """创建右键菜单"""
        try:
            self.context_menu = tk.Menu(self.root, tearoff=0)
            self.context_menu.add_command(label=" 标记完成", command=self.mark_line_done)
            self.context_menu.add_command(label=" 插入时间", command=self.insert_timestamp)
            self.context_menu.add_separator()
            self.context_menu.add_command(label=" 复制", command=self.copy_text)
            self.context_menu.add_command(label=" 粘贴", command=self.paste_text)
        except Exception as e:
            print(f"创建右键菜单错误: {e}")
            
    def create_task_panel(self, parent):
        """创建任务面板"""
        try:
            task_frame = ttk.LabelFrame(parent, text=" 待办任务", padding=10)
            task_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # 任务列表
            self.task_listbox = tk.Listbox(
                task_frame,
                font=('Microsoft YaHei', 10),
                height=12,
                selectmode=tk.SINGLE
            )
            self.task_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            
            # 任务按钮
            task_buttons = ttk.Frame(task_frame)
            task_buttons.pack(fill=tk.X)
            
            ttk.Button(task_buttons, text=" 添加", command=self.add_task).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
            ttk.Button(task_buttons, text=" 完成", command=self.complete_task).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
            
            # 初始化任务列表
            self.refresh_tasks()
            
        except Exception as e:
            print(f"创建任务面板错误: {e}")
            
    def create_quick_actions(self, parent):
        """创建快捷操作"""
        try:
            actions_frame = ttk.LabelFrame(parent, text="⚡ 快捷操作", padding=10)
            actions_frame.pack(fill=tk.X)
            
            actions = [
                ("时间戳", self.insert_timestamp),
                ("新周开始", self.new_week),
                ("导出记录", self.export_records),
                ("打开文件夹", self.open_folder)
            ]
            
            for text, command in actions:
                ttk.Button(
                    actions_frame,
                    text=text,
                    command=command
                ).pack(fill=tk.X, pady=2)
        except Exception as e:
            print(f"创建快捷操作错误: {e}")
            
    def create_status_bar(self, parent):
        """创建状态栏"""
        try:
            status_frame = ttk.Frame(parent)
            status_frame.pack(fill=tk.X, pady=(10, 0))
            
            # 分隔线
            ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))
            
            status_content = ttk.Frame(status_frame)
            status_content.pack(fill=tk.X)
            
            self.status_label = ttk.Label(status_content, text="就绪", style='Status.TLabel')
            self.status_label.pack(side=tk.LEFT)
            
            self.time_label = ttk.Label(status_content, text="", style='Status.TLabel')
            self.time_label.pack(side=tk.RIGHT)
            
            # 启动时钟
            self.update_clock()
            
        except Exception as e:
            print(f"创建状态栏错误: {e}")
            
    # 核心功能方法
    def quick_note(self):
        """快速记录"""
        try:
            note = simpledialog.askstring("快速记录", "请输入要记录的内容：", parent=self.root)
            if note and note.strip():
                timestamp = datetime.datetime.now().strftime("[%H:%M] ")
                current_content = self.text_area.get(1.0, tk.END)
                insertion_point = tk.END if current_content.strip() else 1.0
                
                if insertion_point == tk.END:
                    self.text_area.insert(tk.END, f"\n{timestamp}{note.strip()}")
                else:
                    self.text_area.insert(1.0, f"{timestamp}{note.strip()}\n")
                    
                self.update_status("已添加快速记录")
                self.auto_save()
        except Exception as e:
            print(f"快速记录错误: {e}")
            
    def show_tasks(self):
        """显示任务管理窗口"""
        try:
            task_window = tk.Toplevel(self.root)
            task_window.title("任务管理")
            task_window.geometry("600x400")
            task_window.transient(self.root)
            task_window.grab_set()
            
            # 任务列表
            frame = ttk.Frame(task_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            # 创建任务显示区域
            text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=('Microsoft YaHei', 11))
            text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # 显示任务
            tasks = self.get_all_tasks()
            if tasks:
                task_content = "\n".join(tasks)
                text_widget.insert(1.0, task_content)
            else:
                text_widget.insert(1.0, "暂无任务")
            
            text_widget.config(state=tk.DISABLED)
            
            # 关闭按钮
            ttk.Button(frame, text="关闭", command=task_window.destroy).pack()
            
        except Exception as e:
            print(f"显示任务错误: {e}")
            
    def show_summary(self):
        """显示总结"""
        try:
            summary_window = tk.Toplevel(self.root)
            summary_window.title("周记总结")
            summary_window.geometry("700x500")
            summary_window.transient(self.root)
            summary_window.grab_set()
            
            text_widget = scrolledtext.ScrolledText(summary_window, wrap=tk.WORD, font=('Microsoft YaHei', 11))
            text_widget.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            # 生成总结
            summary = self.generate_summary()
            text_widget.insert(1.0, summary)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"显示总结错误: {e}")
            
    def show_settings(self):
        """显示设置"""
        try:
            settings_window = tk.Toplevel(self.root)
            settings_window.title("设置")
            settings_window.geometry("500x400")
            settings_window.transient(self.root)
            settings_window.grab_set()
            
            # 创建滚动框架
            canvas = tk.Canvas(settings_window)
            scrollbar = ttk.Scrollbar(settings_window, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # 基本设置
            basic_frame = ttk.LabelFrame(scrollable_frame, text="基本设置", padding=15)
            basic_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # 字体大小设置
            ttk.Label(basic_frame, text="字体大小:").grid(row=0, column=0, sticky=tk.W, pady=5)
            font_var = tk.IntVar(value=self.config.get('font_size', 11))
            font_scale = ttk.Scale(basic_frame, from_=9, to=16, variable=font_var, orient=tk.HORIZONTAL)
            font_scale.grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
            
            # 开机自启设置
            startup_frame = ttk.LabelFrame(scrollable_frame, text="启动设置", padding=15)
            startup_frame.pack(fill=tk.X, padx=20, pady=10)
            
            auto_startup_var = tk.BooleanVar(value=self.config.get('auto_startup', False))
            ttk.Checkbutton(
                startup_frame, 
                text="开机自动启动", 
                variable=auto_startup_var
            ).pack(anchor=tk.W, pady=5)
            
            # 提醒设置
            reminder_frame = ttk.LabelFrame(scrollable_frame, text="提醒设置", padding=15)
            reminder_frame.pack(fill=tk.X, padx=20, pady=10)
            
            reminder_enabled_var = tk.BooleanVar(value=self.config.get('reminder_enabled', True))
            ttk.Checkbutton(
                reminder_frame, 
                text="启用定时提醒", 
                variable=reminder_enabled_var
            ).pack(anchor=tk.W, pady=5)
            
            ttk.Label(reminder_frame, text="提醒时间 (24小时制，逗号分隔):").pack(anchor=tk.W, pady=(10,0))
            reminder_times_var = tk.StringVar(value=",".join(map(str, self.config.get('reminder_intervals', [9, 14, 18, 21]))))
            ttk.Entry(reminder_frame, textvariable=reminder_times_var, width=30).pack(anchor=tk.W, pady=5)
            
            # 按钮框架
            button_frame = ttk.Frame(scrollable_frame)
            button_frame.pack(fill=tk.X, padx=20, pady=20)
            
            # 保存按钮
            def save_settings():
                try:
                    self.config['font_size'] = int(font_var.get())
                    self.config['auto_startup'] = auto_startup_var.get()
                    self.config['reminder_enabled'] = reminder_enabled_var.get()
                    
                    # 解析提醒时间
                    try:
                        reminder_times = [int(x.strip()) for x in reminder_times_var.get().split(',') if x.strip()]
                        self.config['reminder_intervals'] = reminder_times
                    except:
                        self.config['reminder_intervals'] = [9, 14, 18, 21]
                    
                    self.save_config()
                    
                    # 应用设置
                    if hasattr(self, 'text_area'):
                        self.text_area.config(font=('Consolas', self.config['font_size']))
                    
                    # 设置开机自启
                    if auto_startup_var.get():
                        self.set_auto_startup(True)
                    else:
                        self.set_auto_startup(False)
                    
                    self.update_status("设置已保存")
                    settings_window.destroy()
                except Exception as e:
                    print(f"保存设置错误: {e}")
                    messagebox.showerror("错误", f"保存设置失败: {e}")
                    
            ttk.Button(button_frame, text="保存设置", command=save_settings).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="取消", command=settings_window.destroy).pack(side=tk.LEFT, padx=5)
            
            # 配置滚动
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
        except Exception as e:
            print(f"显示设置错误: {e}")
            messagebox.showerror("错误", f"显示设置失败: {e}")
            
    # 事件处理方法
    def on_text_change(self, event):
        """文本变化事件"""
        try:
            content = self.text_area.get(1.0, tk.END)
            word_count = len(content.split())
            self.word_count_label.config(text=f"字数: {word_count}")
            self.save_status_label.config(text="未保存")
        except Exception as e:
            print(f"文本变化处理错误: {e}")
            
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            if self.context_menu:
                self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"显示右键菜单错误: {e}")
            
    def mark_line_done(self):
        """标记当前行完成"""
        try:
            current_line = self.text_area.index(tk.INSERT).split('.')[0]
            line_content = self.text_area.get(f"{current_line}.0", f"{current_line}.end")
            if '□' in line_content:
                new_content = line_content.replace('□', '✓')
                self.text_area.delete(f"{current_line}.0", f"{current_line}.end")
                self.text_area.insert(f"{current_line}.0", new_content)
                self.auto_save()
        except Exception as e:
            print(f"标记完成错误: {e}")
            
    def insert_timestamp(self):
        """插入时间戳"""
        try:
            timestamp = datetime.datetime.now().strftime("[%H:%M] ")
            self.text_area.insert(tk.INSERT, timestamp)
        except Exception as e:
            print(f"插入时间戳错误: {e}")
            
    def insert_template(self):
        """插入模板"""
        try:
            template = f"""
{datetime.date.today()} 记录

【今日任务】
□ 

【学习内容】
- 

【工作记录】
- 

【备注思考】
- 

"""
            self.text_area.insert(tk.INSERT, template)
        except Exception as e:
            print(f"插入模板错误: {e}")
            
    def copy_text(self):
        """复制文本"""
        try:
            if self.text_area.tag_ranges(tk.SEL):
                selection = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.root.clipboard_clear()
                self.root.clipboard_append(selection)
        except Exception as e:
            print(f"复制文本错误: {e}")
            
    def paste_text(self):
        """粘贴文本"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.text_area.insert(tk.INSERT, clipboard_content)
        except Exception as e:
            print(f"粘贴文本错误: {e}")
            
    # 任务管理方法
    def add_task(self):
        """添加任务"""
        try:
            task = simpledialog.askstring("添加任务", "请输入任务内容：", parent=self.root)
            if task and task.strip():
                timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M] ")
                task_line = f"{timestamp}□ {task.strip()}\n"
                
                # 添加到文件
                with open(self.current_file, 'a', encoding='utf-8') as f:
                    f.write(task_line)
                    
                self.refresh_content()
                self.refresh_tasks()
                self.update_status(f"已添加任务: {task}")
        except Exception as e:
            print(f"添加任务错误: {e}")
            
    def complete_task(self):
        """完成任务"""
        try:
            selection = self.task_listbox.curselection()
            if selection:
                task_text = self.task_listbox.get(selection[0])
                if '□' in task_text:
                    # 在文件中标记完成
                    if os.path.exists(self.current_file):
                        with open(self.current_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        content = content.replace(task_text, task_text.replace('□', '✓'))
                        
                        with open(self.current_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                            
                        self.refresh_content()
                        self.refresh_tasks()
                        self.update_status("任务已完成")
        except Exception as e:
            print(f"完成任务错误: {e}")
            
    def refresh_tasks(self):
        """刷新任务列表"""
        try:
            self.task_listbox.delete(0, tk.END)
            tasks = self.get_pending_tasks()
            for task in tasks:
                self.task_listbox.insert(tk.END, task)
        except Exception as e:
            print(f"刷新任务错误: {e}")
            
    def get_all_tasks(self):
        """获取所有任务"""
        tasks = []
        try:
            if os.path.exists(self.current_file):
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '□' in line or '✓' in line:
                            tasks.append(line)
        except Exception as e:
            print(f"获取任务错误: {e}")
        return tasks
        
    def get_pending_tasks(self):
        """获取待办任务"""
        tasks = []
        try:
            if os.path.exists(self.current_file):
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '□' in line:
                            tasks.append(line)
        except Exception as e:
            print(f"获取待办任务错误: {e}")
        return tasks[:10]  # 只显示前10个
        
    # 文件操作方法
    def refresh_content(self):
        """刷新内容"""
        try:
            if os.path.exists(self.current_file):
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(1.0, content)
                self.save_status_label.config(text="已保存")
                self.refresh_tasks()
        except Exception as e:
            print(f"刷新内容错误: {e}")
            
    def save_content(self):
        """保存内容"""
        try:
            content = self.text_area.get(1.0, tk.END)
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.save_status_label.config(text="已保存")
            self.update_status("内容已保存")
        except Exception as e:
            print(f"保存内容错误: {e}")
            
    def auto_save(self):
        """自动保存"""
        try:
            if self.config.get('auto_save', True):
                self.save_content()
        except Exception as e:
            print(f"自动保存错误: {e}")
            
    def new_week(self):
        """开始新的一周"""
        try:
            result = messagebox.askyesno("新的一周", "确定要开始新的一周吗？当前内容将被归档。", parent=self.root)
            if result:
                # 归档当前文件
                if os.path.exists(self.current_file):
                    archive_name = f"week_{self.config['week_num']}_{datetime.date.today()}.txt"
                    archive_path = os.path.join(self.archive_dir, archive_name)
                    
                    import shutil
                    shutil.copy2(self.current_file, archive_path)
                    
                self.config['week_num'] += 1
                self.save_config()
                self.create_week_file()
                self.refresh_content()
                self.update_status(f"开始第 {self.config['week_num']} 周")
                
                # 更新标题
                title_label = self.root.winfo_children()[0].winfo_children()[0].winfo_children()[0]
                if hasattr(title_label, 'config'):
                    title_label.config(text=f"第 {self.config['week_num']} 周记录")
                    
        except Exception as e:
            print(f"新周开始错误: {e}")
            
    def export_records(self):
        """导出记录"""
        try:
            export_file = f"weekly_export_{datetime.date.today()}.txt"
            import shutil
            shutil.copy2(self.current_file, export_file)
            self.update_status(f"已导出到: {export_file}")
            messagebox.showinfo("导出完成", f"记录已导出到: {export_file}", parent=self.root)
        except Exception as e:
            print(f"导出记录错误: {e}")
            
    def open_folder(self):
        """打开文件夹"""
        try:
            if sys.platform == "win32":
                os.startfile(os.getcwd())
            elif sys.platform == "darwin":
                subprocess.call(["open", os.getcwd()])
            else:
                subprocess.call(["xdg-open", os.getcwd()])
        except Exception as e:
            print(f"打开文件夹错误: {e}")
            
    # 辅助方法
    def generate_summary(self):
        """生成总结"""
        try:
            all_tasks = self.get_all_tasks()
            total_tasks = len(all_tasks)
            completed_tasks = len([t for t in all_tasks if '✓' in t])
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # 统计字数
            if os.path.exists(self.current_file):
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    word_count = len(content.split())
            else:
                word_count = 0
            
            return f"""
╔═══════════════════════════════════════╗
║          第 {self.config['week_num']} 周总结报告              ║
╚═══════════════════════════════════════╝

生成日期: {datetime.date.today()}
总字数: {word_count}

任务统计:
• 总任务数: {total_tasks}
• 已完成: {completed_tasks}
• 完成率: {completion_rate:.1f}%

📈 本周进展:
• 保持记录习惯
• 任务管理有序
• 总结回顾及时

💡 下周计划:
• 继续保持记录习惯
• 提高任务完成效率
• 定期进行回顾总结

═══════════════════════════════════════
生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        except Exception as e:
            print(f"生成总结错误: {e}")
            return f"生成总结时出错: {e}"
            
    def update_status(self, message):
        """更新状态"""
        try:
            if hasattr(self, 'status_label'):
                self.status_label.config(text=message)
                self.root.after(3000, lambda: self.status_label.config(text="就绪"))
        except Exception as e:
            print(f"更新状态错误: {e}")
            
    def update_clock(self):
        """更新时钟"""
        try:
            if hasattr(self, 'time_label') and not self.is_closing:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                self.time_label.config(text=current_time)
                self.root.after(1000, self.update_clock)
        except Exception as e:
            print(f"更新时钟错误: {e}")
            
    # 系统托盘
    def create_tray_icon(self):
        """创建系统托盘图标"""
        try:
            # 创建简单图标
            image = Image.new('RGB', (64, 64), color='#4A90E2')
            draw = ImageDraw.Draw(image)
            draw.text((20, 20), "WP", fill='white')
            
            menu = pystray.Menu(
                pystray.MenuItem("打开", self.show_window, default=True),
                pystray.MenuItem("快记", self.quick_note_tray),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self.quit_app)
            )
            
            self.icon = pystray.Icon("weekly_tracker", image, "Weekly Tracker", menu)
            
            # 在后台线程运行
            def run_icon():
                try:
                    self.icon.run()
                except Exception as e:
                    print(f"托盘图标运行错误: {e}")
                    
            threading.Thread(target=run_icon, daemon=True).start()
        except Exception as e:
            print(f"创建托盘图标失败: {e}")
            
    def quick_note_tray(self):
        """托盘快速记录"""
        try:
            self.root.after(0, lambda: self.quick_note())
        except Exception as e:
            print(f"托盘快记错误: {e}")
            
    def show_window(self):
        """显示窗口"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.refresh_content()
        except Exception as e:
            print(f"显示窗口错误: {e}")
            
    def hide_window(self):
        """隐藏窗口"""
        try:
            self.root.withdraw()
        except Exception as e:
            print(f"隐藏窗口错误: {e}")
            
    # 文件初始化方法
    def check_week_transition(self):
        """检查周转换"""
        try:
            today = datetime.date.today()
            last_check = datetime.datetime.strptime(self.config.get("last_check", str(today)), "%Y-%m-%d").date()
            
            # 简化周转换逻辑
            if (today - last_check).days > 7:
                self.config["week_num"] += 1
                
            self.config["last_check"] = str(today)
            self.save_config()
        except Exception as e:
            print(f"检查周转换错误: {e}")
            
    def create_week_file(self):
        """创建周文件"""
        try:
            template = f"""═══════════════════════════════════════
         第 {self.config['week_num']} 周学习进度
═══════════════════════════════════════

【本周目标】
- 

【重要事项】
- 

【待办清单】
- 

"""
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(template)
                
            self.add_today_entry()
        except Exception as e:
            print(f"创建周文件错误: {e}")
            
    def add_today_entry(self):
        """添加今日条目"""
        try:
            today = datetime.date.today()
            weekday_names = {
                0: "星期一", 1: "星期二", 2: "星期三", 3: "星期四",
                4: "星期五", 5: "星期六", 6: "星期日"
            }
            weekday = weekday_names.get(today.weekday(), "")
            
            today_template = f"""
────────────────────────────────────
{today} ({weekday})

【今日任务】
□ 

【学习记录】
- 

【备注想法】
- 

"""
            
            with open(self.current_file, 'a', encoding='utf-8') as f:
                f.write(today_template)
        except Exception as e:
            print(f"添加今日条目错误: {e}")
            
    # 开机自启功能
    def set_auto_startup(self, enable=True):
        """设置开机自启"""
        try:
            if sys.platform == "win32":
                key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
                app_name = "WeeklyTracker"
                app_path = os.path.abspath(sys.argv[0])
                
                if enable:
                    # 添加到开机启动
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
                    print("✅ 开机自启已启用")
                else:
                    # 从开机启动中移除
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                            winreg.DeleteValue(key, app_name)
                        print("❌ 开机自启已禁用")
                    except FileNotFoundError:
                        pass  # 键不存在，无需删除
            else:
                print("开机自启功能目前仅支持Windows系统")
        except Exception as e:
            print(f"设置开机自启错误: {e}")
            
    # 提醒功能
    def start_reminder_timer(self):
        """启动提醒定时器"""
        try:
            if self.config.get('reminder_enabled', True):
                self.check_reminder()
                # 每10分钟检查一次提醒
                self.root.after(600000, self.start_reminder_timer)  # 10分钟 = 600000毫秒
        except Exception as e:
            print(f"提醒定时器错误: {e}")
            
    def check_reminder(self):
        """检查是否需要发送提醒"""
        try:
            if not self.config.get('reminder_enabled', True):
                return
                
            now = datetime.datetime.now()
            current_hour = now.hour
            today_str = now.strftime("%Y-%m-%d")
            
            # 检查今天是否已经发送过这个时间点的提醒
            last_reminder = self.config.get('last_reminder', '')
            reminder_key = f"{today_str}_{current_hour}"
            
            if reminder_key != last_reminder:
                reminder_times = self.config.get('reminder_intervals', [9, 14, 18, 21])
                
                if current_hour in reminder_times:
                    self.send_reminder()
                    self.config['last_reminder'] = reminder_key
                    self.save_config()
        except Exception as e:
            print(f"检查提醒错误: {e}")
            
    def send_reminder(self):
        """发送提醒通知"""
        try:
            messages = [
                "记录一下今天的学习进展吧！",
                "检查一下待办任务的完成情况",
                "回顾今天的工作内容",
                "记录一些想法和感悟"
            ]
            
            import random
            message = random.choice(messages)
            
            if HAS_PLYER:
                notification.notify(
                    title="Weekly Tracker 提醒",
                    message=message,
                    app_icon=os.path.abspath("wp_icon.ico") if os.path.exists("wp_icon.ico") else None,
                    timeout=10
                )
            else:
                # 使用tkinter弹窗作为备选
                def show_reminder():
                    reminder_window = tk.Toplevel(self.root)
                    reminder_window.title("Weekly Tracker 提醒")
                    reminder_window.geometry("300x150")
                    reminder_window.transient(self.root)
                    reminder_window.attributes('-topmost', True)
                    
                    ttk.Label(reminder_window, text=message, font=('Microsoft YaHei', 11)).pack(pady=20)
                    ttk.Button(reminder_window, text="知道了", command=reminder_window.destroy).pack(pady=10)
                    
                    # 5秒后自动关闭
                    reminder_window.after(5000, reminder_window.destroy)
                    
                self.root.after(0, show_reminder)
                
            print(f"提醒已发送: {message}")
        except Exception as e:
            print(f"发送提醒错误: {e}")
    
    def show_notification(self, title, message):
        """显示通知"""
        try:
            if HAS_PLYER:
                notification.notify(
                    title=title,
                    message=message,
                    app_icon=os.path.abspath("wp_icon.ico") if os.path.exists("wp_icon.ico") else None,
                    timeout=5
                )
            else:
                print(f"{title}: {message}")
        except Exception as e:
            print(f"显示通知错误: {e}")
            
    def quit_app(self):
        """退出应用"""
        try:
            self.is_closing = True
            self.save_content()
            if self.icon:
                self.icon.stop()
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"退出应用错误: {e}")
            
    def run(self):
        """运行应用"""
        try:
            # 绑定快捷键
            self.root.bind('<Control-s>', lambda e: self.save_content())
            self.root.bind('<Control-n>', lambda e: self.quick_note())
            self.root.bind('<Escape>', lambda e: self.hide_window())
            
            # 设置关闭窗口时最小化到托盘
            self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
            
            # 运行主循环
            self.root.mainloop()
        except Exception as e:
            print(f"运行应用错误: {e}")

if __name__ == "__main__":
    try:
        app = WeeklyTracker()
        app.run()
    except Exception as e:
        print(f"启动应用失败: {e}")
        import traceback
        traceback.print_exc()
