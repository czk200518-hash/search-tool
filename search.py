import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
from pathlib import Path
import threading
import time
import queue
from datetime import datetime, timedelta

class ModernButton(ttk.Button):
    """自定义现代化按钮"""
    def __init__(self, master=None, **kwargs):
        kwargs.setdefault('style', 'Accent.TButton')
        super().__init__(master, **kwargs)

class FileSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 文件搜索工具")
        
        # 获取屏幕分辨率
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # 设置窗口大小
        window_width = 600
        window_height = 950
        
        # 设置窗口位置居中
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置最小窗口大小
        self.root.minsize(500, 750)
        
        # 线程控制变量
        self.stop_search_flag = threading.Event()
        self.search_thread = None
        self.results_queue = queue.Queue()
        self.current_file_count = 0
        self.current_folder_count = 0
        self.scanned_files = 0
        self.scanned_folders = 0
        
        # 时间统计
        self.search_start_time = None
        
        # 缓存已访问的文件夹路径，避免重复扫描
        self.visited_folders = set()
        
        # 默认文件格式列表
        self.default_file_extensions = [
            "所有文件", ".txt", ".pdf", ".doc", ".docx", 
            ".xls", ".xlsx", ".py", ".java", ".cpp", ".html", 
            ".css", ".js", ".jpg", ".png", ".mp3", ".mp4"
        ]
        
        # 配置文件路径
        self.config_file = self.get_config_file_path()
        
        # 加载自定义文件格式列表
        self.custom_file_extensions = self.load_custom_formats()
        
        # 设置UI样式和布局
        self.setup_styles()
        self.setup_ui()
    
    def get_config_file_path(self):
        """获取配置文件路径"""
        # 获取用户主目录
        home_dir = Path.home()
        
        # 创建应用配置目录
        config_dir = home_dir / ".file_search_tool"
        config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        return config_dir / "config.json"
    
    def load_custom_formats(self):
        """从配置文件加载自定义文件格式"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    custom_formats = config_data.get('custom_formats', [])
                    
                    # 验证格式是否有效
                    valid_formats = []
                    for fmt in custom_formats:
                        if isinstance(fmt, str) and len(fmt) <= 20:
                            if not fmt.startswith('.'):
                                fmt = '.' + fmt
                            valid_formats.append(fmt)
                    
                    return valid_formats
        except Exception as e:
            print(f"加载配置文件失败: {e}")
        
        return []
    
    def save_custom_formats(self):
        """保存自定义文件格式到配置文件"""
        try:
            config_data = {
                'custom_formats': self.custom_file_extensions,
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def setup_styles(self):
        """设置现代化UI样式"""
        style = ttk.Style()
        
        # 使用clam主题
        style.theme_use('clam')
        
        # 定义简洁的配色方案
        self.colors = {
            'primary': '#4a6ee0',
            'primary_light': '#6b8aed',
            'secondary': '#6c757d',
            'success': '#28a745',
            'background': '#f8f9fa',
            'surface': '#ffffff',
            'border': '#e9ecef',
            'text': '#2c3e50',
            'text_light': '#7f8c8d',
            'accent': '#e74c3c',
            'hover': '#f1f5fd',
        }
        
        # 基础字体
        base_font = ('Microsoft YaHei', 10)
        heading_font = ('Microsoft YaHei', 11, 'bold')
        title_font = ('Microsoft YaHei', 14, 'bold')
        
        # 配置标签样式
        style.configure('Title.TLabel', 
                       font=title_font,
                       foreground=self.colors['text'])
        
        style.configure('Heading.TLabel',
                       font=heading_font,
                       foreground=self.colors['primary'])
        
        style.configure('Normal.TLabel',
                       font=base_font,
                       foreground=self.colors['text'])
        
        # 配置按钮样式
        style.configure('Accent.TButton',
                       font=('Microsoft YaHei', 10, 'bold'),
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       padding=(16, 8),
                       relief='flat')
        
        style.map('Accent.TButton',
                 background=[('active', self.colors['primary_light']),
                            ('disabled', self.colors['border']),
                            ('pressed', '#3a5ad0')])
        
        style.configure('Secondary.TButton',
                       font=('Microsoft YaHei', 10),
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       borderwidth=1,
                       relief='flat',
                       padding=(12, 6))
        
        style.map('Secondary.TButton',
                 background=[('active', self.colors['hover']),
                            ('disabled', self.colors['border'])])
        
        # 配置进度条样式
        style.configure('Custom.Horizontal.TProgressbar',
                       background=self.colors['primary'],
                       troughcolor=self.colors['border'],
                       bordercolor=self.colors['border'],
                       thickness=12)
        
        # 配置树形视图样式
        style.configure('Treeview',
                       font=base_font,
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['surface'],
                       borderwidth=1,
                       relief='flat',
                       rowheight=25)
        
        style.configure('Treeview.Heading',
                       font=('Microsoft YaHei', 10, 'bold'),
                       background=self.colors['background'],
                       foreground=self.colors['text'],
                       relief='flat',
                       borderwidth=1)
        
        style.map('Treeview.Heading',
                 background=[('active', self.colors['hover'])])
        
        # 配置组合框样式
        style.configure('TCombobox',
                       font=base_font,
                       background=self.colors['surface'],
                       fieldbackground=self.colors['surface']) 
        
        style.map('TCombobox',
                 fieldbackground=[('readonly', self.colors['surface'])],
                 background=[('readonly', self.colors['surface'])])
        
        style.configure('Custom.TCheckbutton',
                       font=('Microsoft YaHei', 10),
                       foreground=self.colors['text'])
        
        style.map('Custom.TCheckbutton',
                 indicatorcolor=[('selected', self.colors['primary']),
                                ('alternate', self.colors['primary']),
                                ('!selected', self.colors['border']),
                                ('disabled', self.colors['border'])])
        
        # 设置窗口背景色
        self.root.configure(bg=self.colors['background'])
        
        self.root.option_add('*TCombobox*Listbox.font', base_font)
        
    def setup_ui(self):
        """设置简洁的UI布局"""

        main_container = ttk.Frame(self.root, padding="15")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(2, weight=1)
        
        # 标题区域
        title_frame = ttk.Frame(main_container)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        title_label = ttk.Label(title_frame, 
                               text="文件搜索工具",
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(title_frame,
                                 text="v2.0\nby-86",
                                 style='Normal.TLabel',
                                 foreground=self.colors['text_light'])
        version_label.pack(side=tk.RIGHT)
        
        # 搜索配置区域
        config_panel = ttk.Frame(main_container, padding=(15, 10))
        config_panel.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        config_panel.columnconfigure(1, weight=1)
        
        # 关键词
        ttk.Label(config_panel, text="搜索内容", 
                 style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        self.keyword_entry = ttk.Entry(config_panel, font=('Microsoft YaHei', 11))
        self.keyword_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), 
                               padx=(10, 0), pady=(0, 8))
        self.keyword_entry.insert(0, "输入文件名或关键词")
        self.keyword_entry.bind("<FocusIn>", lambda e: self.keyword_entry.delete(0, tk.END) if self.keyword_entry.get() == "输入文件名或关键词" else None)
        
        # 路径选择
        path_frame = ttk.Frame(config_panel)
        path_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        
        ttk.Label(path_frame, text="搜索位置", 
                 style='Heading.TLabel').pack(side=tk.LEFT)
        
        self.path_var = tk.StringVar(value=os.getcwd())
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var,
                                   font=('Microsoft YaHei', 10))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        self.browse_btn = ModernButton(path_frame, text="浏览", 
                                      command=self.browse_directory, width=8)
        self.browse_btn.pack(side=tk.LEFT)
        
        # 搜索选项
        options_frame = ttk.Frame(config_panel)
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 搜索类型
        type_frame = ttk.Frame(options_frame)
        type_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(type_frame, text="类型", 
                 style='Normal.TLabel').pack(anchor=tk.W)
        
        self.search_files_var = tk.BooleanVar(value=True)
        self.search_folders_var = tk.BooleanVar(value=False)
        
        type_subframe = ttk.Frame(type_frame)
        type_subframe.pack(fill=tk.X, pady=(5, 0))
        
        self.file_checkbox = ttk.Checkbutton(type_subframe, text=" 文件", 
                                            variable=self.search_files_var,
                                            style='Custom.TCheckbutton')
        self.file_checkbox.pack(side=tk.LEFT, padx=(0, 10))
        
        self.folder_checkbox = ttk.Checkbutton(type_subframe, text=" 文件夹", 
                                              variable=self.search_folders_var,
                                              style='Custom.TCheckbutton')
        self.folder_checkbox.pack(side=tk.LEFT)
        
        # 文件类型
        filetype_frame = ttk.Frame(options_frame)
        filetype_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(filetype_frame, text="文件格式", 
                 style='Normal.TLabel').pack(anchor=tk.W)
        
        # 文件格式选择区域
        filetype_select_frame = ttk.Frame(filetype_frame)
        filetype_select_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.ext_var = tk.StringVar(value="所有文件")
        self.ext_combo = ttk.Combobox(filetype_select_frame, textvariable=self.ext_var, 
                                     width=12, state="readonly", height=10)
        self.ext_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # 添加自定义文件格式
        self.add_format_btn = ttk.Button(filetype_select_frame, text="+", 
                                         command=self.open_add_format_dialog, 
                                         style='Secondary.TButton', width=3)
        self.add_format_btn.pack(side=tk.LEFT)
        
        self.update_file_extensions()
        
        # 搜索选项
        search_opts_frame = ttk.Frame(options_frame)
        search_opts_frame.pack(side=tk.LEFT)
        
        ttk.Label(search_opts_frame, text="选项", 
                 style='Normal.TLabel').pack(anchor=tk.W)
        
        self.case_var = tk.BooleanVar()
        self.deep_var = tk.BooleanVar(value=True)
        
        opts_subframe = ttk.Frame(search_opts_frame)
        opts_subframe.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Checkbutton(opts_subframe, text="区分大小写", 
                       variable=self.case_var,
                       style='Custom.TCheckbutton').pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(opts_subframe, text="包含子文件夹", 
                       variable=self.deep_var,
                       style='Custom.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        # 控制按钮区域
        button_frame = ttk.Frame(main_container)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.search_btn = ModernButton(button_frame, text="开始搜索", 
                                      command=self.start_search, width=12)
        self.search_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.stop_btn = ttk.Button(button_frame, text="停止", 
                                   command=self.stop_search, 
                                   style='Secondary.TButton', width=10, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.clear_btn = ttk.Button(button_frame, text="清空", 
                                    command=self.clear_results, 
                                    style='Secondary.TButton', width=10)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, padx=(15, 15))
        
        self.export_btn = ttk.Button(button_frame, text="导出结果", 
                                    command=self.export_results, 
                                    style='Secondary.TButton', width=10)
        self.export_btn.pack(side=tk.LEFT)
        
        stats_frame = ttk.Frame(main_container, padding=(0, 5))
        stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        self.time_label = ttk.Label(stats_grid, text="时间: --:--:--", 
                                   style='Normal.TLabel')
        self.time_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.found_label = ttk.Label(stats_grid, text="找到: 0 项", 
                                    style='Normal.TLabel')
        self.found_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.speed_label = ttk.Label(stats_grid, text="速度: --/秒", 
                                    style='Normal.TLabel')
        self.speed_label.grid(row=0, column=2, sticky=tk.W)
        
        self.progress = ttk.Progressbar(stats_frame, 
                                       style='Custom.Horizontal.TProgressbar',
                                       mode='determinate',
                                       length=100)
        self.progress.pack(fill=tk.X, pady=(8, 0))
        
        # 搜索结果区域
        results_frame = ttk.Frame(main_container)
        results_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        results_header = ttk.Frame(results_frame)
        results_header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(results_header, text="搜索结果", 
                 style='Heading.TLabel').pack(side=tk.LEFT)
        
        self.results_count_var = tk.StringVar(value="共 0 项")
        ttk.Label(results_header, textvariable=self.results_count_var,
                 style='Normal.TLabel',
                 foreground=self.colors['text_light']).pack(side=tk.RIGHT)
        
        columns = ("类型", "名称", "大小", "路径")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        # 列标题和宽度
        col_widths = {
            "类型": 60,
            "名称": 250,
            "大小": 80,
            "路径": 350
        }
        
        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, width=col_widths[col], 
                           anchor=tk.CENTER if col in ["类型", "大小"] else tk.W)
        
        # 滚动条
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        vsb.grid(row=1, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=2, column=0, sticky=(tk.W, tk.E), columnspan=2)
        
        self.tree.bind("<Double-Button-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_container, textvariable=self.status_var, 
                              anchor=tk.W, padding=(0, 8),
                              style='Normal.TLabel',
                              foreground=self.colors['text_light'])
        status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0, 
                                   font=('Microsoft YaHei', 9),
                                   bg=self.colors['surface'],
                                   fg=self.colors['text'])
        self.context_menu.add_command(label="打开", command=self.open_item)
        self.context_menu.add_command(label="打开所在位置", command=self.open_item_location)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制路径", command=self.copy_item_path)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.after(100, self.process_results_queue)
        
        self.keyword_entry.focus_set()
        
        self.update_time_timer()
    
    def browse_directory(self):
        """选择目录"""
        directory = filedialog.askdirectory(initialdir=self.path_var.get())
        if directory:
            self.path_var.set(directory)
    
    def update_file_extensions(self):
        """更新文件格式列表"""
        # 合并默认格式和自定义格式
        all_extensions = self.default_file_extensions + self.custom_file_extensions

        seen = set()
        unique_extensions = []
        for ext in all_extensions:
            if ext not in seen:
                seen.add(ext)
                unique_extensions.append(ext)
        
        self.ext_combo['values'] = unique_extensions
    
    def open_add_format_dialog(self):
        """打开添加文件格式对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加文件格式")
        dialog_width = 350
        dialog_height = 220
        
        # 对话框位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.resizable(False, False)
        dialog.transient(self.root) 
        dialog.grab_set()  
        
        # 对话框样式
        dialog.configure(bg=self.colors['background'])
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="请输入文件格式:", 
                 style='Heading.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        format_var = tk.StringVar()
        format_entry = ttk.Entry(main_frame, textvariable=format_var, 
                                font=('Microsoft YaHei', 11), width=25)
        format_entry.pack(fill=tk.X, pady=(0, 10))
        format_entry.focus_set()
        
        custom_frame = ttk.Frame(main_frame)
        custom_frame.pack(fill=tk.X, pady=(0, 10))
        
        if self.custom_file_extensions:
            custom_text = "当前自定义格式: " + ", ".join(self.custom_file_extensions)
        else:
            custom_text = "当前没有自定义格式"
        
        ttk.Label(custom_frame, text=custom_text,
                 style='Info.TLabel',
                 foreground=self.colors['text_light'],
                 wraplength=300).pack(anchor=tk.W)
        
        ttk.Label(main_frame, text="示例：.exe, .zip, .rar, .json, .xml",
                 style='Info.TLabel',
                 foreground=self.colors['text_light']).pack(anchor=tk.W, pady=(0, 15))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="取消", 
                  command=dialog.destroy,
                  style='Secondary.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame, text="添加", 
                  command=lambda: self.add_custom_format(format_var.get(), dialog),
                  style='Accent.TButton').pack(side=tk.RIGHT)
        
        dialog.bind('<Return>', lambda e: self.add_custom_format(format_var.get(), dialog))
    
    def add_custom_format(self, file_format, dialog):
        """添加自定义文件格式"""

        file_format = file_format.strip()
        
        if not file_format:
            messagebox.showwarning("警告", "请输入文件格式！", parent=dialog)
            return
        
        if not file_format.startswith('.'):
            file_format = '.' + file_format
        
        # 检查格式
        if len(file_format) > 20:
            messagebox.showwarning("警告", "文件格式过长，请使用简短的格式！", parent=dialog)
            return

        if file_format in self.default_file_extensions + self.custom_file_extensions:
            messagebox.showinfo("提示", f"文件格式 '{file_format}' 已经存在！", parent=dialog)
            return
        
        self.custom_file_extensions.append(file_format)
        
        # 保存到配置文件
        self.save_custom_formats()
        
        # 更新文件格式列表
        self.update_file_extensions()
        
        # 设置新添加的格式为当前选择
        self.ext_var.set(file_format)
        
        dialog.destroy()
        
        # 显示成功消息
        self.status_var.set(f"已添加文件格式: {file_format}")
    
    def start_search(self):
        """开始搜索"""
        keyword = self.keyword_entry.get().strip()
        if not keyword or keyword == "输入文件名或关键词":
            messagebox.showwarning("提示", "请输入搜索关键词！")
            self.keyword_entry.focus_set()
            return
        
        # 检查是否选择了搜索内容
        if not self.search_files_var.get() and not self.search_folders_var.get():
            messagebox.showwarning("提示", "请选择搜索类型（文件或文件夹）！")
            return
        
        # 重置停止标志
        self.stop_search_flag.clear()
        
        # 清空之前的搜索结果
        self.clear_results()
        
        # 清空结果队列
        while not self.results_queue.empty():
            try:
                self.results_queue.get_nowait()
            except queue.Empty:
                break
        
        # 重置统计信息和缓存
        self.current_file_count = 0
        self.current_folder_count = 0
        self.scanned_files = 0
        self.scanned_folders = 0
        self.visited_folders.clear()
        
        # 更新UI
        self.search_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.clear_btn.config(state='disabled')
        self.export_btn.config(state='disabled')
        self.progress['value'] = 0
        
        # 设置搜索开始时间
        self.search_start_time = time.time()
        
        # 更新状态
        self.update_stats()
        
        self.status_var.set(f"正在搜索: '{keyword}'")
        
        # 启动搜索线程
        self.search_thread = threading.Thread(target=self.perform_search, daemon=True)
        self.search_thread.start()
    
    def stop_search(self):
        """停止搜索"""
        self.stop_search_flag.set()
        self.status_var.set("正在停止...")
    
    def clear_results(self):
        """清空搜索结果"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.current_file_count = 0
        self.current_folder_count = 0
        self.update_stats()
        self.status_var.set("就绪")
    
    def export_results(self):
        """导出搜索结果到文件"""
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("提示", "没有搜索结果可导出！")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="导出搜索结果"
        )
        
        if not file_path:
            return
        
        try:
            ext = Path(file_path).suffix.lower()
            with open(file_path, 'w', encoding='utf-8') as f:
                if ext == '.csv':
                    # CSV格式
                    f.write("类型,名称,大小,路径\n")
                    for item in items:
                        values = self.tree.item(item, 'values')
                        f.write(','.join(values) + '\n')
                else:
                    # 文本格式
                    f.write(f"搜索结果\n")
                    f.write(f"搜索时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"关键词: {self.keyword_entry.get()}\n")
                    f.write(f"位置: {self.path_var.get()}\n")
                    f.write(f"共找到: {len(items)} 项\n")
                    f.write("-" * 60 + "\n\n")
                    
                    for item in items:
                        values = self.tree.item(item, 'values')
                        item_type, name, size, path = values
                        f.write(f"[{item_type}] {name}\n")
                        f.write(f"大小: {size}\n")
                        f.write(f"路径: {path}\n\n")
            
            messagebox.showinfo("成功", f"导出完成！\n{file_path}")
            self.status_var.set(f"已导出: {len(items)} 项")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def perform_search(self):
        """执行搜索（优化版）- 在单独的线程中运行"""
        try:
            keyword = self.keyword_entry.get()
            search_path = self.path_var.get()
            case_sensitive = self.case_var.get()
            
            # 获取搜索参数
            search_files = self.search_files_var.get()
            search_folders = self.search_folders_var.get()
            search_subdirs = self.deep_var.get()
            
            file_ext = None
            selected_ext = self.ext_combo.get()
            if selected_ext != "所有文件":
                file_ext = selected_ext.lower()
            
            search_path_obj = Path(search_path)
            
            if not search_path_obj.exists():
                self.results_queue.put({"type": "error", "message": "搜索路径不存在！"})
                return
            
            # 预处理关键词
            if not case_sensitive:
                keyword = keyword.lower()
            
            # 开始搜索
            processed_items = 0
            matched_items = 0
            last_update_time = time.time()
            
            def search_directory(dir_path, depth=0):
                nonlocal processed_items, matched_items, last_update_time
                
                if self.stop_search_flag.is_set():
                    return
                
                dir_path_str = str(dir_path)
                if dir_path_str in self.visited_folders:
                    return
                self.visited_folders.add(dir_path_str)
                
                try:
                    with os.scandir(dir_path_str) as it:
                        subdirs = []
                        
                        for entry in it:
                            if self.stop_search_flag.is_set():
                                return
                            
                            if entry.is_dir():
                                if search_folders:
                                    folder_name = entry.name
                                    check_name = folder_name.lower() if not case_sensitive else folder_name
                                    
                                    if keyword in check_name:
                                        matched_items += 1
                                        folder_info = {
                                            'type': 'folder_result',
                                            'name': folder_name,
                                            'path': entry.path,
                                            'size': self.format_size(0)
                                        }
                                        self.results_queue.put(folder_info)
                                
                                if search_subdirs:
                                    subdirs.append(entry.path)
                            
                            elif entry.is_file() and search_files:
                                processed_items += 1
                                self.scanned_files = processed_items
                                
                                if file_ext:
                                    if not entry.name.lower().endswith(file_ext):
                                        continue
                                
                                file_name = entry.name
                                check_name = file_name.lower() if not case_sensitive else file_name
                                
                                if keyword in check_name:
                                    matched_items += 1
                                    try:
                                        size = entry.stat().st_size
                                        file_info = {
                                            'type': 'file_result',
                                            'name': file_name,
                                            'path': entry.path,
                                            'size': self.format_size(size)
                                        }
                                        self.results_queue.put(file_info)
                                    except:
                                        pass
                                
                                current_time = time.time()
                                if processed_items % 200 == 0 or current_time - last_update_time > 0.5:
                                    last_update_time = current_time
                                    self.results_queue.put({
                                        "type": "progress", 
                                        "processed": processed_items,
                                        "matched": matched_items
                                    })
                        
                        for subdir in subdirs:
                            if self.stop_search_flag.is_set():
                                return
                            search_directory(Path(subdir), depth + 1)
                
                except (PermissionError, FileNotFoundError):
                    pass
                except Exception as e:
                    print(f"搜索错误: {e}")
            
            # 开始搜索
            search_directory(search_path_obj)
            
            # 搜索完成
            self.results_queue.put({
                "type": "complete", 
                "processed": processed_items,
                "matched": matched_items
            })
            
        except Exception as e:
            self.results_queue.put({"type": "error", "message": str(e)})
    
    def process_results_queue(self):
        """处理结果队列（在主线程中运行）"""
        try:
            # 处理队列中的所有结果
            processed_count = 0

            # 每次循环最多处理200个结果
            max_process_per_cycle = 200  
            
            while not self.results_queue.empty() and processed_count < max_process_per_cycle:
                result = self.results_queue.get_nowait()
                
                if result.get("type") == "file_result":
                    # 显示文件搜索结果
                    self.display_file_result(result)
                    self.current_file_count += 1
                    
                elif result.get("type") == "folder_result":
                    # 显示文件夹搜索结果
                    self.display_folder_result(result)
                    self.current_folder_count += 1
                    
                elif result.get("type") == "progress":
                    # 更新进度
                    processed = result.get("processed", 0)
                    matched = result.get("matched", 0)
                    self.update_stats()
                    
                    if processed > 0:
                        progress_value = min((processed % 1000) / 10, 90)
                        self.progress['value'] = progress_value
                
                elif result.get("type") == "complete":
                    # 搜索完成
                    processed = result.get("processed", 0)
                    matched = result.get("matched", 0)
                    self.search_complete(processed, matched)
                    break
                    
                elif result.get("type") == "error":
                    # 发生错误
                    error_msg = result.get("message", "未知错误")
                    messagebox.showerror("错误", f"搜索出错: {error_msg}")
                    self.search_complete(0, 0)
                    break
                
                processed_count += 1
                
                # 每处理50个项目就更新一次UI计数
                if processed_count % 50 == 0:
                    self.update_stats()
                
        except queue.Empty:
            pass
        
        # 继续处理队列
        self.root.after(30, self.process_results_queue)  
    
    def display_file_result(self, file_info):
        """显示文件搜索结果"""
        item_id = self.tree.insert("", "end", values=(
            "📄",
            file_info['name'],
            file_info['size'],
            file_info['path']
        ))
        
        # 为不同类型的文件设置不同颜色
        file_ext = Path(file_info['path']).suffix.lower()
        if file_ext in ['.txt', '.py', '.java', '.cpp', '.html', '.css', '.js']:
            self.tree.tag_configure('text_file', foreground=self.colors['primary'])
            self.tree.item(item_id, tags=('text_file',))
        elif file_ext in ['.pdf', '.doc', '.docx']:
            self.tree.tag_configure('document_file', foreground=self.colors['accent'])
            self.tree.item(item_id, tags=('document_file',))
        elif file_ext in ['.jpg', '.png', '.gif']:
            self.tree.tag_configure('image_file', foreground=self.colors['success'])
            self.tree.item(item_id, tags=('image_file',))
    
    def display_folder_result(self, folder_info):
        """显示文件夹搜索结果"""
        item_id = self.tree.insert("", "end", values=(
            "📁",
            folder_info['name'],
            folder_info['size'],
            folder_info['path']
        ))
        
        self.tree.tag_configure('folder', foreground=self.colors['text'])
        self.tree.item(item_id, tags=('folder',))
    
    def update_stats(self):
        """更新统计信息"""
        total_found = self.current_file_count + self.current_folder_count
        
        # 更新统计标签
        self.found_label.config(text=f"找到: {total_found:,} 项")
        
        # 更新结果计数
        self.results_count_var.set(f"共 {total_found:,} 项")
    
    def update_time_timer(self):
        """更新时间的定时器"""
        if self.search_start_time is not None and not self.stop_search_flag.is_set():
            current_time = time.time()
            elapsed_seconds = current_time - self.search_start_time
            
            # 格式化已用时间
            elapsed_str = str(timedelta(seconds=int(elapsed_seconds)))
            self.time_label.config(text=f"时间: {elapsed_str}")
            
            # 计算搜索速度
            total_scanned = self.scanned_files + self.scanned_folders
            if total_scanned > 0 and elapsed_seconds > 0:
                items_per_second = total_scanned / elapsed_seconds
                self.speed_label.config(text=f"速度: {items_per_second:.0f}/秒")
        
        # 继续更新时间
        self.root.after(1000, self.update_time_timer)
    
    def search_complete(self, processed, matched):
        """搜索完成"""
        self.progress['value'] = 100
        self.search_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.clear_btn.config(state='normal')
        self.export_btn.config(state='normal')
        
        total_found = self.current_file_count + self.current_folder_count
        
        if self.stop_search_flag.is_set():
            self.status_var.set(f"搜索已停止 - 找到 {total_found:,} 项")
        else:
            self.status_var.set(f"搜索完成 - 找到 {total_found:,} 项")
        
        # 更新统计
        self.update_stats()
        
        # 重置时间统计
        self.search_start_time = None
    
    def on_double_click(self, event):
        """双击打开文件或文件夹"""
        selection = self.tree.selection()
        if selection:
            self.open_item()
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def open_item(self):
        """打开选中的文件或文件夹"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            path = values[3]  # 路径在第4列
            
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(path)
                elif os.name == 'posix':  # macOS, Linux
                    import subprocess
                    if sys.platform == 'darwin':
                        subprocess.run(['open', path])
                    else:
                        subprocess.run(['xdg-open', path])
                self.status_var.set(f"已打开: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开: {str(e)}")
    
    def open_item_location(self):
        """打开文件或文件夹所在位置"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            path = values[3]
            
            # 获取所在文件夹
            if os.path.isfile(path):
                location = os.path.dirname(path)
            else:
                location = os.path.dirname(path) if os.path.dirname(path) else path
            
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(location)
                elif os.name == 'posix':  # macOS, Linux
                    import subprocess
                    if sys.platform == 'darwin':
                        subprocess.run(['open', location])
                    else:
                        subprocess.run(['xdg-open', location])
            except Exception as e:
                messagebox.showerror("错误", f"无法打开位置: {str(e)}")
    
    def copy_item_path(self):
        """复制文件或文件夹路径到剪贴板"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            path = item['values'][3]
            
            self.root.clipboard_clear()
            self.root.clipboard_append(path)
            self.status_var.set("已复制路径")
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.0f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def on_closing(self):
        """窗口关闭时的处理"""
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search_flag.set()
            self.search_thread.join(timeout=0.5)
        
        # 保存配置文件
        self.save_custom_formats()
        
        self.root.destroy()

def main():
    root = tk.Tk()
    
    # 设置DPI
    if sys.platform == 'win32':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    app = FileSearchGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()