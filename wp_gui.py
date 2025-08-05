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

class WeeklyProgressTracker:
    def __init__(self):
        self.config_file = "wp_config.json"
        self.current_file = "weekly_progress.txt"
        self.habits_file = ".habits_tracker.json"
        self.week_counter_file = ".week_counter.txt"
        self.archive_dir = "archive"
        
        # 初始化配置
        self.load_config()
        self.init_files()
        
        # 创建主窗口但先隐藏
        self.root = tk.Tk()
        self.root.title("周进度追踪器")
        self.root.geometry("800x600")
        self.root.withdraw()  # 先隐藏主窗口
        
        # 设置窗口图标
        self.root.iconbitmap(default=self.create_icon_file())
        
        # 初始化UI
        self.setup_ui()
        
        # 创建系统托盘
        self.create_tray_icon()
        
    def create_icon_file(self):
        """创建一个简单的图标文件"""
        icon_path = "wp_icon.ico"
        if not os.path.exists(icon_path):
            # 创建一个简单的图标
            img = Image.new('RGB', (64, 64), color='#4A90E2')
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), "WP", fill='white')
            img.save(icon_path, format='ICO')
        return icon_path
        
    def load_config(self):
        """加载配置"""
        default_config = {
            "week_num": 1,
            "last_check": str(datetime.date.today()),
            "theme": "modern"
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
        """初始化必要的文件和文件夹"""
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
            
        # 检查是否需要创建新周文件
        self.check_week_transition()
        
        # 如果当前周文件不存在，创建它
        if not os.path.exists(self.current_file):
            self.create_week_file()
            
    def check_week_transition(self):
        """检查是否需要归档上周文件"""
        today = datetime.date.today()
        if today.weekday() == 0:  # 周一
            last_check = datetime.datetime.strptime(self.config["last_check"], "%Y-%m-%d").date()
            if last_check < today:
                # 归档上周文件
                if os.path.exists(self.current_file):
                    archive_name = f"week_{self.config['week_num']}_progress_{last_check}.txt"
                    archive_path = os.path.join(self.archive_dir, archive_name)
                    os.rename(self.current_file, archive_path)
                    self.config["week_num"] += 1
                    
        self.config["last_check"] = str(today)
        self.save_config()
        
    def create_week_file(self):
        """创建新周文件"""
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(f"""═══════════════════════════════════════
         📅 第 {self.config['week_num']} 周学习进度
═══════════════════════════════════════

【本周目标】
- 

【重要事项】 !!
- 

【待办清单】 (格式: [Due:MM/DD] #标签 事项)
- [Due:08/10] #作业 示例：完成项目

""")
        self.add_today_entry()
        
    def add_today_entry(self):
        """添加今日记录条目"""
        today = datetime.date.today()
        weekday = today.strftime("%A")
        
        # 检查今天是否已有记录
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if today.strftime("%Y-%m-%d") in content:
                    return
                    
        # 添加今日记录
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
            
    def setup_ui(self):
        """设置主界面"""
        # 创建顶部工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 工具栏按钮
        ttk.Button(toolbar, text="📝 今日记录", command=self.open_today).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✅ 标记完成", command=self.mark_done_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⚡ 快速记录", command=self.quick_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📊 周总结", command=self.show_summary).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔥 习惯追踪", command=self.show_habits).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⏱️ 计时器", command=self.show_timer).pack(side=tk.LEFT, padx=2)
        
        # 主显示区域
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 文本显示区
        self.text_area = scrolledtext.ScrolledText(
            self.main_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=30,
            font=("Microsoft YaHei", 10)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # 底部状态栏
        self.status_bar = ttk.Label(self.root, text="准备就绪", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 加载并显示当前内容
        self.refresh_content()
        
    def refresh_content(self):
        """刷新显示内容"""
        if os.path.exists(self.current_file):
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, content)
                
    def open_today(self):
        """打开今日记录"""
        self.add_today_entry()
        # 使用默认文本编辑器打开
        if sys.platform == "win32":
            os.startfile(self.current_file)
        else:
            subprocess.call(["open", self.current_file])
        self.update_status("已打开今日记录")
        
    def quick_add_dialog(self):
        """快速添加对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("快速记录")
        dialog.geometry("400x150")
        
        ttk.Label(dialog, text="请输入要记录的内容：").pack(pady=10)
        
        entry = ttk.Entry(dialog, width=50)
        entry.pack(pady=5, padx=20)
        entry.focus()
        
        def add_quick():
            content = entry.get()
            if content:
                self.quick_add(content)
                dialog.destroy()
                
        ttk.Button(dialog, text="添加", command=add_quick).pack(pady=10)
        entry.bind('<Return>', lambda e: add_quick())
        
    def quick_add(self, content):
        """快速添加记录"""
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M]")
        with open(self.current_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} 快速记录: {content}\n")
        self.refresh_content()
        self.update_status(f"已添加: {content}")
        
    def mark_done_dialog(self):
        """标记完成对话框"""
        # 读取所有任务
        tasks = self.get_all_tasks()
        if not tasks:
            messagebox.showinfo("提示", "没有找到待完成的任务")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("标记任务完成")
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text="选择要标记为完成的任务：").pack(pady=10)
        
        # 任务列表
        listbox = tk.Listbox(dialog, height=15, width=60)
        listbox.pack(pady=5, padx=20)
        
        for i, task in enumerate(tasks):
            listbox.insert(tk.END, f"{i+1}. {task}")
            
        def mark_selected():
            selection = listbox.curselection()
            if selection:
                task_index = selection[0]
                self.mark_task_done(tasks[task_index])
                dialog.destroy()
                
        ttk.Button(dialog, text="标记完成", command=mark_selected).pack(pady=10)
        
    def get_all_tasks(self):
        """获取所有未完成的任务"""
        tasks = []
        with open(self.current_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip().startswith('□'):
                    tasks.append(line.strip())
        return tasks
        
    def mark_task_done(self, task):
        """标记任务为完成"""
        with open(self.current_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        content = content.replace(task, task.replace('□', '✓'))
        
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        self.refresh_content()
        self.update_status(f"已完成: {task[2:]}")
        
    def show_summary(self):
        """显示周总结"""
        summary = self.generate_summary()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("本周进度总结")
        dialog.geometry("600x500")
        
        text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, width=70, height=25)
        text.pack(padx=10, pady=10)
        text.insert(1.0, summary)
        text.config(state=tk.DISABLED)
        
    def generate_summary(self):
        """生成周总结"""
        completed = 0
        pending = 0
        
        with open(self.current_file, 'r', encoding='utf-8') as f:
            content = f.read()
            completed = content.count('✓')
            pending = content.count('□')
            
        total = completed + pending
        percent = (completed / total * 100) if total > 0 else 0
        
        summary = f"""════════════════════════════════════
        本周进度总结
════════════════════════════════════

📊 任务完成情况:
  ✅ 完成: {completed} 项
  ⏳ 待办: {pending} 项
  📈 完成率: {percent:.1f}%

📌 进度条:
  [{'█' * int(percent/10)}{'░' * (10-int(percent/10))}] {percent:.1f}%

💡 改进建议:
"""
        
        if percent < 50:
            summary += "  • 完成率较低，建议调整任务优先级\n"
        if pending > 10:
            summary += "  • 待办事项较多，建议分解大任务\n"
        summary += "  • 保持每日记录习惯，追踪进度\n"
        
        return summary
        
    def show_habits(self):
        """显示习惯追踪"""
        if not os.path.exists(self.habits_file):
            habits_data = {"streak": 1, "last_date": str(datetime.date.today())}
            with open(self.habits_file, 'w') as f:
                json.dump(habits_data, f)
        else:
            with open(self.habits_file, 'r') as f:
                habits_data = json.load(f)
                
        dialog = tk.Toplevel(self.root)
        dialog.title("习惯追踪")
        dialog.geometry("400x300")
        
        # 大字显示连续天数
        streak_label = ttk.Label(dialog, text=f"🔥 {habits_data['streak']}", 
                                font=("Arial", 48, "bold"))
        streak_label.pack(pady=20)
        
        ttk.Label(dialog, text="连续记录天数", font=("Arial", 16)).pack()
        
        # 显示积分规则
        rules_text = """
📝 每日记录: +10分
✅ 完成任务: +5分  
🎯 达成目标: +20分
        """
        ttk.Label(dialog, text=rules_text, font=("Arial", 12)).pack(pady=20)
        
    def show_timer(self):
        """显示计时器"""
        self.timer_window = tk.Toplevel(self.root)
        self.timer_window.title("任务计时器")
        self.timer_window.geometry("300x200")
        
        self.timer_label = ttk.Label(self.timer_window, text="00:00:00", 
                                    font=("Arial", 24))
        self.timer_label.pack(pady=20)
        
        self.timer_running = False
        self.timer_start = None
        
        button_frame = ttk.Frame(self.timer_window)
        button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(button_frame, text="开始", 
                                      command=self.start_timer)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="停止", 
                                     command=self.stop_timer,
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
    def start_timer(self):
        """开始计时"""
        self.timer_running = True
        self.timer_start = datetime.datetime.now()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_timer()
        
    def stop_timer(self):
        """停止计时"""
        self.timer_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # 记录时长
        duration = datetime.datetime.now() - self.timer_start
        minutes = int(duration.total_seconds() / 60)
        self.quick_add(f"任务用时: {minutes} 分钟")
        
    def update_timer(self):
        """更新计时器显示"""
        if self.timer_running:
            elapsed = datetime.datetime.now() - self.timer_start
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.config(text=time_str)
            
            self.timer_window.after(1000, self.update_timer)
            
    def update_status(self, message):
        """更新状态栏"""
        self.status_bar.config(text=f"{datetime.datetime.now().strftime('%H:%M:%S')} - {message}")
        
    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建图标
        image = Image.new('RGB', (64, 64), color='#4A90E2')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')
        draw.text((24, 24), "WP", fill='#4A90E2')
        
        # 创建菜单
        menu = pystray.Menu(
            pystray.MenuItem("打开主窗口", self.show_window, default=True),
            pystray.MenuItem("今日记录", self.open_today),
            pystray.MenuItem("快速记录", lambda: self.root.after(0, self.quick_add_dialog)),
            pystray.MenuItem("查看总结", lambda: self.root.after(0, self.show_summary)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.quit_app)
        )
        
        # 创建托盘图标
        self.icon = pystray.Icon("weekly_progress", image, "周进度追踪", menu)
        
        # 在新线程中运行托盘图标
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
    def show_window(self):
        """显示主窗口"""
        self.root.deiconify()
        self.root.lift()
        self.refresh_content()
        
    def quit_app(self):
        """退出应用"""
        self.icon.stop()
        self.root.quit()
        
    def run(self):
        """运行应用"""
        # 设置关闭窗口时最小化到托盘
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        self.root.mainloop()
        
    def hide_window(self):
        """隐藏窗口到托盘"""
        self.root.withdraw()

if __name__ == "__main__":
    app = WeeklyProgressTracker()
    app.run()