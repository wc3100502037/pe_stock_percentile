import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import pandas as pd

# 导入中文字体配置（必须在导入matplotlib相关模块之前）
import font_config

from data_fetcher import DataFetcher
from database import StockDatabase
from valuation_calculator import ValuationCalculator
from chart_view import ChartView
from config import DEFAULT_YEARS, TIME_RANGES, VALUATION_TYPES
from pinyin_utils import get_pinyin_initials, match_stock_by_pinyin
from stock_list_fetcher import get_stock_list_from_db, is_stock_list_exists, update_stock_list


class DualSlider(tk.Canvas):
    """
    双滑块控件 - 在一个轴上显示两个可拖动的滑块
    
    用于选择日期范围，支持左右两个滑块分别控制起始和结束位置
    """
    
    def __init__(self, parent, from_=0, to=100, width=400, height=50, 
                 command=None, bg='#f0f0f0', troughcolor='#d3d3d3', 
                 slidercolor='#0078d4', **kwargs):
        """
        初始化双滑块控件
        
        Args:
            parent: 父容器
            from_: 最小值（默认0）
            to: 最大值（默认100）
            width: 控件宽度
            height: 控件高度
            command: 滑块变化时的回调函数，接收(left_val, right_val)两个参数
            bg: 背景颜色
            troughcolor: 轨道颜色
            slidercolor: 滑块颜色
            **kwargs: 其他Canvas参数
        """
        # 如果 width 为 0，使用默认宽度，后续会自适应
        init_width = width if width > 0 else 400
        super().__init__(parent, width=init_width, height=height, bg=bg, 
                        highlightthickness=0, **kwargs)
        
        self.from_ = from_
        self.to = to
        self.command = command
        self.troughcolor = troughcolor
        self.slidercolor = slidercolor
        self.init_width = width
        self.canvas_height = height
        
        # 滑块当前值 (0-100的百分比)
        self.left_val = 0
        self.right_val = 100
        
        # 滑块尺寸 - 使用更大的圆形滑块
        self.slider_radius = 12
        # 轨道高度
        self.trough_height = 8
        
        # 内边距
        self.padding = self.slider_radius + 10
        
        # 中心Y坐标
        self.center_y = height // 2
        
        # 初始化标志
        self._initialized = False
        
        # 绑定鼠标事件
        self.bind('<Button-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)
        
        # 绑定配置改变事件（用于自适应大小）
        self.bind('<Configure>', self._on_configure)
        
        self.dragging = None  # 'left' 或 'right'
        
    def _on_configure(self, event=None):
        """
        处理大小改变事件
        
        Args:
            event: 配置事件对象
        """
        # 获取当前实际大小
        new_width = self.winfo_width()
        new_height = self.winfo_height()
        
        if new_width > 1 and new_height > 1:
            self.canvas_width = new_width
            self.center_y = new_height // 2
            self.track_width = self.canvas_width - 2 * self.padding
            
            if not self._initialized:
                # 首次初始化
                self._init_draw()
                self._initialized = True
            else:
                # 重新绘制
                self._redraw()
    
    def _redraw(self):
        """
        重新绘制所有元素
        
        清除画布并重新绘制轨道、滑块和选中区域
        """
        # 删除所有元素
        self.delete('all')
        # 重新初始化绘制
        self._init_draw()
        # 更新滑块位置到当前值
        self._update_slider('left')
        self._update_slider('right')
        self._update_range()
        
    def _init_draw(self):
        """
        初始化绘制所有元素
        
        绘制轨道背景、选中区域和左右两个滑块
        """
        # 绘制轨道背景（灰色）
        self.track_bg = self.create_rectangle(
            self.padding, self.center_y - self.trough_height//2,
            self.canvas_width - self.padding, self.center_y + self.trough_height//2,
            fill=self.troughcolor, outline='', tags='track_bg'
        )
        
        # 选中的滑块区域（高亮显示）- 初始为全部
        self.range_rect = self.create_rectangle(
            self.padding, self.center_y - self.trough_height//2,
            self.canvas_width - self.padding, self.center_y + self.trough_height//2,
            fill=self.slidercolor, outline='', tags='range'
        )
        
        # 绘制左滑块（带阴影效果）
        self.left_slider_shadow = self._create_slider_circle(
            self.padding, self.center_y, '#999999', 'left_shadow'
        )
        self.left_slider = self._create_slider_circle(
            self.padding, self.center_y, self.slidercolor, 'left'
        )
        
        # 绘制右滑块（带阴影效果）
        self.right_slider_shadow = self._create_slider_circle(
            self.canvas_width - self.padding, self.center_y, '#999999', 'right_shadow'
        )
        self.right_slider = self._create_slider_circle(
            self.canvas_width - self.padding, self.center_y, self.slidercolor, 'right'
        )
    
    def _create_slider_circle(self, x, y, color, tag):
        """
        创建圆形滑块
        
        Args:
            x: 圆心x坐标
            y: 圆心y坐标
            color: 滑块颜色
            tag: 滑块标识标签
            
        Returns:
            int: 创建的滑块对象ID
        """
        r = self.slider_radius
        # 外圈白色边框
        self.create_oval(
            x - r - 2, y - r - 2,
            x + r + 2, y + r + 2,
            fill='white', outline='', tags=f'{tag}_border'
        )
        # 主滑块圆形
        slider = self.create_oval(
            x - r, y - r,
            x + r, y + r,
            fill=color, outline='white', width=2,
            tags=tag
        )
        return slider
    
    def _on_press(self, event):
        """
        鼠标按下事件处理
        
        检测点击位置，确定要拖动哪个滑块
        
        Args:
            event: 鼠标事件对象，包含点击位置坐标
        """
        # 检查点击的是哪个滑块
        left_x = self._val_to_x(self.left_val)
        right_x = self._val_to_x(self.right_val)
        
        # 计算到两个滑块的距离
        dist_left = abs(event.x - left_x)
        dist_right = abs(event.x - right_x)
        
        # 选择距离更近的滑块（增加检测范围）
        click_radius = self.slider_radius + 10
        if dist_left < dist_right:
            if dist_left <= click_radius:
                self.dragging = 'left'
        else:
            if dist_right <= click_radius:
                self.dragging = 'right'
    
    def _on_drag(self, event):
        """
        鼠标拖动事件处理
        
        根据鼠标位置更新滑块位置，并触发回调函数
        
        Args:
            event: 鼠标事件对象，包含当前位置坐标
        """
        if not self.dragging:
            return
        
        # 将鼠标位置转换为值
        new_val = self._x_to_val(event.x)
        new_val = max(0, min(100, new_val))
        
        if self.dragging == 'left':
            # 左滑块不能超过右滑块
            if new_val < self.right_val - 3:  # 保持最小间距
                self.left_val = new_val
                self._update_slider('left')
        else:  # right
            # 右滑块不能低于左滑块
            if new_val > self.left_val + 3:  # 保持最小间距
                self.right_val = new_val
                self._update_slider('right')
        
        # 更新选中范围显示
        self._update_range()
        
        # 调用回调函数
        if self.command:
            self.command(self.left_val, self.right_val)
    
    def _on_release(self, event):
        """
        鼠标释放事件处理
        
        结束滑块拖动状态
        
        Args:
            event: 鼠标事件对象
        """
        self.dragging = None
    
    def _val_to_x(self, val):
        """
        将百分比值转换为x坐标
        
        Args:
            val: 百分比值（0-100）
            
        Returns:
            float: 对应的x坐标
        """
        return self.padding + (val / 100) * self.track_width
    
    def _x_to_val(self, x):
        """
        将x坐标转换为百分比值
        
        Args:
            x: x坐标
            
        Returns:
            float: 对应的百分比值（0-100）
        """
        return ((x - self.padding) / self.track_width) * 100
    
    def _update_slider(self, which):
        """
        更新滑块位置
        
        根据当前值更新指定滑块的显示位置
        
        Args:
            which: 要更新的滑块，'left' 或 'right'
        """
        r = self.slider_radius
        if which == 'left':
            x = self._val_to_x(self.left_val)
            y = self.center_y
            # 更新阴影
            self.coords(self.left_slider_shadow,
                       x - r + 2, y - r + 2,
                       x + r + 2, y + r + 2)
            # 更新主滑块
            self.coords(self.left_slider,
                       x - r, y - r,
                       x + r, y + r)
            # 更新边框
            self.coords(f'left_border',
                       x - r - 2, y - r - 2,
                       x + r + 2, y + r + 2)
        else:
            x = self._val_to_x(self.right_val)
            y = self.center_y
            # 更新阴影
            self.coords(self.right_slider_shadow,
                       x - r + 2, y - r + 2,
                       x + r + 2, y + r + 2)
            # 更新主滑块
            self.coords(self.right_slider,
                       x - r, y - r,
                       x + r, y + r)
            # 更新边框
            self.coords(f'right_border',
                       x - r - 2, y - r - 2,
                       x + r + 2, y + r + 2)
    
    def _update_range(self):
        """
        更新选中范围的高亮显示
        
        根据左右滑块位置更新选中区域的显示
        """
        left_x = self._val_to_x(self.left_val)
        right_x = self._val_to_x(self.right_val)
        y = self.center_y
        self.coords(self.range_rect,
                   left_x, y - self.trough_height//2,
                   right_x, y + self.trough_height//2)
    
    def get_values(self):
        """
        获取当前滑块值
        
        Returns:
            tuple: (left_val, right_val) 左右滑块的当前值（0-100）
        """
        return (self.left_val, self.right_val)
    
    def set_values(self, left, right):
        """
        设置滑块值
        
        Args:
            left: 左滑块值（0-100）
            right: 右滑块值（0-100）
        """
        self.left_val = max(0, min(100, left))
        self.right_val = max(0, min(100, right))
        self._update_slider('left')
        self._update_slider('right')
        self._update_range()


class ProgressDialog:
    """
    进度对话框
    
    显示数据下载进度，支持取消操作
    """
    
    def __init__(self, parent, title="下载进度"):
        """
        初始化进度对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # 进度信息标签
        self.message_label = ttk.Label(self.dialog, text="准备下载...", font=('Arial', 10))
        self.message_label.pack(pady=10, padx=20)
        
        # 进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.dialog, 
            variable=self.progress_var,
            maximum=100,
            length=350,
            mode='determinate'
        )
        self.progress_bar.pack(pady=10, padx=20, fill=tk.X)
        
        # 百分比标签
        self.percent_label = ttk.Label(self.dialog, text="0%", font=('Arial', 9))
        self.percent_label.pack(pady=5)
        
        # 取消按钮
        self.cancelled = False
        self.cancel_btn = ttk.Button(self.dialog, text="取消", command=self._on_cancel)
        self.cancel_btn.pack(pady=10)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _on_cancel(self):
        self.cancelled = True
        self.message_label.config(text="正在取消...")
    
    def update_progress(self, message: str, percent: int = None):
        """更新进度"""
        self.message_label.config(text=message)
        if percent is not None:
            self.progress_var.set(percent)
            self.percent_label.config(text=f"{percent}%")
        self.dialog.update()
    
    def close(self):
        """关闭对话框"""
        self.dialog.grab_release()
        self.dialog.destroy()
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self.cancelled


class StockPEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("个股PE百分位分析工具")
        self.root.geometry("1400x900")

        self.data_fetcher = DataFetcher(progress_callback=self._on_progress)
        self.db = StockDatabase()
        self.current_df = None
        self.current_stock_code = None
        self.current_stock_name = None
        self.current_valuation_type = 'PE'  # 默认PE估值
        self.progress_dialog = None
        self._stock_list_cache = []  # 缓存股票列表用于拼音搜索

        self._create_widgets()
        self._load_stock_memory()

        # 启动后自动加载上证指数
        self.root.after(100, self._load_default_index)
        
        # 检查并更新股票列表（异步执行，避免阻塞界面）
        self.root.after(1000, self._check_and_update_stock_list)
    
    def _on_progress(self, message: str, percent: int = None):
        """进度回调函数"""
        if self.progress_dialog and self.progress_dialog.dialog.winfo_exists():
            self.progress_dialog.update_progress(message, percent)
    
    def _check_and_update_stock_list(self):
        """检查并更新股票列表"""
        # 如果没有股票列表，尝试获取
        if not is_stock_list_exists():
            print("股票列表不存在，正在获取...")
            try:
                # 在后台线程中更新股票列表
                import threading
                def update_in_background():
                    success = update_stock_list()
                    if success:
                        # 更新完成后，在主线程中刷新界面
                        self.root.after(0, self._load_stock_memory)
                
                thread = threading.Thread(target=update_in_background)
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(f"更新股票列表失败: {e}")
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        ttk.Label(control_frame, text="股票代码:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.stock_var = tk.StringVar()
        self.stock_combo = ttk.Combobox(control_frame, textvariable=self.stock_var, width=20)
        self.stock_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.stock_combo.bind('<Return>', lambda e: self._on_search())
        self.stock_combo.bind('<KeyRelease>', self._on_stock_input_change)
        
        ttk.Button(control_frame, text="查询", command=self._on_search).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="刷新数据", command=self._on_refresh).grid(row=0, column=3, padx=5)
        ttk.Button(control_frame, text="删除记忆", command=self._on_delete_memory).grid(row=0, column=4, padx=5)
        
        date_frame = ttk.Frame(control_frame)
        date_frame.grid(row=1, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(date_frame, text="开始日期:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * DEFAULT_YEARS)
        
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                                    foreground='white', borderwidth=2,
                                    date_pattern='yyyy-mm-dd',
                                    year=start_date.year, month=start_date.month, day=start_date.day)
        self.start_date.grid(row=0, column=1, padx=5)
        self.start_date.bind('<<DateEntrySelected>>', self._on_date_change)

        ttk.Label(date_frame, text="结束日期:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2,
                                  date_pattern='yyyy-mm-dd',
                                  year=end_date.year, month=end_date.month, day=end_date.day)
        self.end_date.grid(row=0, column=3, padx=5)
        self.end_date.bind('<<DateEntrySelected>>', self._on_date_change)
        
        ttk.Label(date_frame, text="时间范围:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.range_var = tk.StringVar(value='10年')
        range_combo = ttk.Combobox(date_frame, textvariable=self.range_var,
                                   values=list(TIME_RANGES.keys()), width=8, state='readonly')
        range_combo.grid(row=0, column=5, padx=5)
        range_combo.bind('<<ComboboxSelected>>', self._on_range_change)

        # 估值类型选择
        ttk.Label(date_frame, text="估值类型:").grid(row=0, column=6, sticky=tk.W, padx=5)
        self.valuation_var = tk.StringVar(value='PE')
        self.valuation_combo = ttk.Combobox(date_frame, textvariable=self.valuation_var,
                                       values=list(VALUATION_TYPES.keys()), width=6, state='readonly')
        self.valuation_combo.grid(row=0, column=7, padx=5)
        self.valuation_combo.bind('<<ComboboxSelected>>', self._on_valuation_change)
        
        # 网络状态标签
        self.network_status_label = ttk.Label(date_frame, text="● 网络正常", foreground="green")
        self.network_status_label.grid(row=0, column=8, sticky=tk.W, padx=10)
        # 初始化时检查网络状态
        self._update_network_status()
        
        slider_frame = ttk.LabelFrame(main_frame, text="日期范围选择（拖动滑块选择起止日期）", padding="10")
        slider_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        slider_frame.columnconfigure(0, weight=1)
        
        # 使用自定义双滑块控件 - 宽度设为0，让它自适应
        self.dual_slider = DualSlider(slider_frame, width=0, height=50, 
                                      command=self._on_dual_slider_change)
        self.dual_slider.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        
        # 日期范围标签
        self.range_label = ttk.Label(slider_frame, text="显示全部数据", width=25)
        self.range_label.grid(row=0, column=1, padx=10)
        
        info_frame = ttk.LabelFrame(main_frame, text="当前信息", padding="10")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        self.info_text = tk.Text(info_frame, width=30, height=20, wrap=tk.WORD)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        info_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.info_text['yscrollcommand'] = info_scroll.set
        
        chart_container = ttk.LabelFrame(main_frame, text="图表展示", padding="10")
        chart_container.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        chart_container.rowconfigure(0, weight=1)
        chart_container.columnconfigure(0, weight=1)
        
        self.chart_view = ChartView(chart_container)
    
    def _load_stock_memory(self):
        """加载股票列表（优先使用全市场列表）"""
        # 首先尝试从stock_list表获取全市场股票
        all_stocks = get_stock_list_from_db()
        
        if all_stocks:
            # 使用全市场股票列表
            self._stock_list_cache = all_stocks
            # 只显示前100只在下拉框中（避免过多）
            stock_list = [f"{code} - {name}" for code, name in all_stocks[:100]]
        else:
            # 如果没有全市场列表，使用记忆的股票
            stocks = self.db.get_stock_memory()
            stock_list = []
            self._stock_list_cache = []
            for code, name in stocks:
                if name and name != code:
                    stock_list.append(f"{code} - {name}")
                    self._stock_list_cache.append((code, name))
                else:
                    stock_list.append(code)
                    self._stock_list_cache.append((code, code))
        
        self.stock_combo['values'] = stock_list
    
    def _on_range_change(self, event=None):
        range_text = self.range_var.get()
        years = TIME_RANGES.get(range_text)

        if years:
            end = datetime.now()
            start = end - timedelta(days=365 * years)
            self.start_date.set_date(start)
            self.end_date.set_date(end)

    def _on_valuation_change(self, event=None):
        """估值类型切换"""
        new_type = self.valuation_var.get()
        if new_type != self.current_valuation_type:
            self.current_valuation_type = new_type
            # 如果有当前数据，重新计算并显示
            if self.current_df is not None and not self.current_df.empty:
                self._recalculate_and_display()

    def _update_network_status(self):
        """更新网络状态显示"""
        from data_fetcher import check_network_connection
        if check_network_connection():
            self.network_status_label.config(text="● 网络正常", foreground="green")
        else:
            self.network_status_label.config(text="● 网络未连接（使用本地数据）", foreground="red")
        # 每5秒检查一次网络状态
        self.root.after(5000, self._update_network_status)

    def _is_trading_day(self, date: datetime) -> bool:
        """判断是否为交易日（非周末）"""
        # 周六=5, 周日=6
        return date.weekday() < 5

    def _load_default_index(self):
        """加载默认上证指数数据"""
        DEFAULT_INDEX_CODE = 'sh.000001'
        DEFAULT_INDEX_NAME = '上证指数'

        try:
            # 设置日期范围（默认10年）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * DEFAULT_YEARS)
            start = start_date.strftime('%Y-%m-%d')
            end = end_date.strftime('%Y-%m-%d')

            # 更新日期选择器
            self.start_date.set_date(start_date)
            self.end_date.set_date(end_date)

            # 检查数据库中是否有数据
            df = self.db.get_stock_data(DEFAULT_INDEX_CODE, start, end)

            # 检查是否需要获取最新数据
            today = datetime.now().date()
            is_trading_day = self._is_trading_day(end_date)

            if not df.empty:
                # 获取数据库中最新日期
                db_latest_date = pd.to_datetime(df['date']).max().date()

                # 如果是交易日且数据库数据不是最新的，尝试获取最新数据
                if is_trading_day and db_latest_date < today:
                    # 显示提示信息
                    self.info_text.delete(1.0, tk.END)
                    self.info_text.insert(tk.END, f"正在获取最新数据...\n")
                    self.root.update()

                    try:
                        # 尝试获取最新数据
                        df_new, stock_name = self.data_fetcher.fetch_stock_data(
                            DEFAULT_INDEX_CODE, start, end, force_update=False
                        )
                        if not df_new.empty:
                            df = df_new
                            # 再次检查最新日期
                            db_latest_date = pd.to_datetime(df['date']).max().date()
                    except Exception as e:
                        print(f"获取最新数据失败: {e}")

                # 检查数据是否是最新的
                latest_date = pd.to_datetime(df['date']).max().date()
                date_info = ""
                if latest_date < today:
                    if is_trading_day:
                        date_info = f"\n【注意】当前非最新数据，最新数据日期: {latest_date}"
                    else:
                        date_info = f"\n【提示】今日非交易日，最新数据日期: {latest_date}"

            if df.empty:
                # 数据库中没有数据，从网络获取
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, f"正在下载 {DEFAULT_INDEX_NAME} 数据...\n")
                self.root.update()

                df, stock_name = self.data_fetcher.fetch_stock_data(DEFAULT_INDEX_CODE, start, end)

                if df.empty:
                    self.info_text.delete(1.0, tk.END)
                    self.info_text.insert(tk.END, "无法获取数据，请检查网络连接")
                    return

            # 保存数据
            self.current_df = df
            self.raw_df = df.copy()
            self.current_stock_code = DEFAULT_INDEX_CODE
            self.current_stock_name = DEFAULT_INDEX_NAME
            self.current_start_date = start
            self.current_end_date = end

            # 设置股票代码输入框
            self.stock_var.set(f"{DEFAULT_INDEX_CODE} - {DEFAULT_INDEX_NAME}")

            # 计算估值
            calculator = ValuationCalculator(df, self.current_valuation_type)
            df_with_valuation = calculator.calculate_percentile_in_range(start, end)
            self.current_df = df_with_valuation

            # 更新显示
            self._update_info_with_date_note(df_with_valuation, DEFAULT_INDEX_CODE, DEFAULT_INDEX_NAME, date_info)
            self.chart_view.plot_data(df_with_valuation, DEFAULT_INDEX_CODE, DEFAULT_INDEX_NAME,
                                      valuation_type=self.current_valuation_type)
            
            # 重置滑块到默认位置
            self.dual_slider.set_values(0, 100)
            self.range_label.config(text="显示全部数据")

            # 加载到历史记录
            self._load_stock_memory()

        except Exception as e:
            print(f"加载默认指数失败: {e}")
            import traceback
            traceback.print_exc()

    def _update_info_with_date_note(self, df, stock_code, stock_name=None, date_note=""):
        """更新信息面板，支持添加日期提示"""
        if df.empty:
            return

        latest = df.iloc[-1]
        earliest = df.iloc[0]

        # 检查是否使用了收盘价代替PE/PB（指数通常没有PE/PB数据）
        using_close_as_fallback = False
        if self.current_valuation_type == 'PE':
            if 'pe' in df.columns and df['pe'].equals(df['close']):
                using_close_as_fallback = True
            percentile = latest.get('pe_percentile', 0)
            valuation_label = "收盘价百分位" if using_close_as_fallback else "PE百分位"
        else:
            if 'pb' in df.columns and df['pb'].equals(df['close']):
                using_close_as_fallback = True
            percentile = latest.get('pb_percentile', 0)
            valuation_label = "收盘价百分位" if using_close_as_fallback else "PB百分位"

        # 获取阈值配置
        config = VALUATION_TYPES.get(self.current_valuation_type, {})
        low_threshold = config.get('low_threshold', 30)
        high_threshold = config.get('high_threshold', 70)

        # 判断估值水平
        if percentile < low_threshold:
            level = "低估"
            level_color = "绿色"
        elif percentile > high_threshold:
            level = "高估"
            level_color = "红色"
        else:
            level = "正常"
            level_color = "黄色"

        # 添加指数提示
        index_note = ""
        if using_close_as_fallback:
            index_note = "\n【提示】指数无PE/PB数据，使用收盘价计算百分位"

        info = f"""
股票代码: {stock_code}
股票名称: {stock_name or stock_code}
当前日期: {latest['date'].strftime('%Y-%m-%d')}
收盘价: {latest['close']:.2f}

{valuation_label}: {percentile:.2f}%
估值水平: {level} ({level_color})

数据范围: {earliest['date'].strftime('%Y-%m-%d')} 至 {latest['date'].strftime('%Y-%m-%d')}
数据条数: {len(df)}
{date_note}{index_note}
"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info)

    def _on_date_change(self, event=None):
        """日期变化时从数据库重新读取数据并计算百分位"""
        if self.current_stock_code:
            try:
                start = self.start_date.get_date().strftime('%Y-%m-%d')
                end = self.end_date.get_date().strftime('%Y-%m-%d')

                print(f"\n{'='*60}")
                print(f"日期变化: {start} 到 {end}")
                print(f"当前股票: {self.current_stock_code}")

                # 更新当前日期范围
                self.current_start_date = start
                self.current_end_date = end

                # 从数据库重新读取指定日期范围的数据
                df = self.db.get_stock_data(self.current_stock_code, start, end)
                print(f"从数据库读取数据条数: {len(df)}")

                if df.empty:
                    messagebox.showwarning("警告", "选定的日期范围内没有数据，请刷新数据")
                    return

                # 检查数据类型
                if 'peTTM' in df.columns:
                    print(f"peTTM数据类型: {df['peTTM'].dtype}")
                    print(f"peTTM前5个值: {df['peTTM'].head().tolist()}")

                # 保存原始数据
                self.raw_df = df.copy()

                # 使用估值计算器，在新的日期范围内计算百分位
                calculator = ValuationCalculator(df, self.current_valuation_type)
                df_with_valuation = calculator.calculate_percentile_in_range(start, end)

                # 检查结果
                if not df_with_valuation.empty and 'pe_percentile' in df_with_valuation.columns:
                    print(f"计算后数据条数: {len(df_with_valuation)}")
                    print(f"PE范围: {df_with_valuation['pe'].min():.2f} - {df_with_valuation['pe'].max():.2f}")
                    print(f"百分位范围: {df_with_valuation['pe_percentile'].min():.2f}% - {df_with_valuation['pe_percentile'].max():.2f}%")

                    # 找到最小和最大PE对应的百分位
                    min_idx = df_with_valuation['pe'].idxmin()
                    max_idx = df_with_valuation['pe'].idxmax()
                    print(f"最小PE={df_with_valuation.loc[min_idx, 'pe']:.2f}, 百分位={df_with_valuation.loc[min_idx, 'pe_percentile']:.2f}%")
                    print(f"最大PE={df_with_valuation.loc[max_idx, 'pe']:.2f}, 百分位={df_with_valuation.loc[max_idx, 'pe_percentile']:.2f}%")

                self.current_df = df_with_valuation

                self._update_info(df_with_valuation, self.current_stock_code, self.current_stock_name)
                self.chart_view.plot_data(df_with_valuation, self.current_stock_code, self.current_stock_name,
                                          valuation_type=self.current_valuation_type)
                
                # 重置滑块到默认位置
                self.dual_slider.set_values(0, 100)
                self.range_label.config(text="显示全部数据")

                print(f"{'='*60}\n")
            except Exception as e:
                print(f"日期变化处理错误: {e}")
                import traceback
                traceback.print_exc()
                pass  # 日期格式不正确时忽略
    
    def _on_dual_slider_change(self, left_val, right_val):
        """双滑块变化处理"""
        if self.current_df is None or self.current_df.empty:
            return
        
        total_points = len(self.current_df)
        
        # 计算起止索引
        start_idx = int((left_val / 100) * total_points)
        end_idx = int((right_val / 100) * total_points)
        
        # 边界检查
        if start_idx < 0:
            start_idx = 0
        if end_idx > total_points:
            end_idx = total_points
        if end_idx <= start_idx:
            end_idx = start_idx + 1
        
        # 更新标签
        start_date = self.current_df.iloc[start_idx]['date']
        end_date = self.current_df.iloc[end_idx - 1]['date']
        self.range_label.config(text=f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        
        # 绘制图表
        self.chart_view.plot_data(self.current_df, self.current_stock_code, self.current_stock_name, 
                                  start_idx, end_idx, self.current_valuation_type)
    
    def _on_stock_input_change(self, event=None):
        """处理股票输入框的实时输入，支持拼音搜索"""
        query = self.stock_var.get().strip()
        if not query:
            return
        
        # 如果输入是纯字母，尝试拼音搜索
        if query.isalpha():
            matches = match_stock_by_pinyin(query, self._stock_list_cache)
            if matches:
                # 更新下拉列表显示匹配结果（最多显示50条）
                display_list = [f"{code} - {name}" for code, name in matches[:50]]
                self.stock_combo['values'] = display_list
        elif query.isdigit():
            # 如果输入是数字（股票代码），在列表中过滤
            matches = [(code, name) for code, name in self._stock_list_cache 
                      if query in code]
            if matches:
                display_list = [f"{code} - {name}" for code, name in matches[:50]]
                self.stock_combo['values'] = display_list
        else:
            # 其他输入，恢复原始列表
            self._load_stock_memory()
    
    def _on_search(self):
        stock_input = self.stock_var.get().strip()
        if not stock_input:
            messagebox.showwarning("警告", "请输入股票代码")
            return

        stock_code = stock_input.split(' - ')[0].strip()
        
        # 标准化股票代码
        normalized_code = self.data_fetcher.try_normalize_stock_code(stock_code)
        print(f"搜索股票: 输入={stock_input}, 提取={stock_code}, 标准化={normalized_code}")

        try:
            start = self.start_date.get_date().strftime('%Y-%m-%d')
            end = self.end_date.get_date().strftime('%Y-%m-%d')
        except:
            messagebox.showerror("错误", "日期格式不正确")
            return

        # 显示进度对话框
        self.progress_dialog = ProgressDialog(self.root, title="正在获取数据")
        self.root.update()

        try:
            # 获取用户选择的日期范围的数据
            df, stock_name = self.data_fetcher.fetch_stock_data(stock_code, start, end)

            # 关闭进度对话框
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            if df.empty:
                messagebox.showwarning("警告", f"未找到股票 {stock_code} (标准化: {normalized_code}) 的数据\n请检查股票代码是否正确，或尝试刷新数据。")
                return

            self.current_df = df
            self.current_stock_code = stock_code
            self.current_stock_name = stock_name
            # 保存用户选择的日期范围
            self.current_start_date = start
            self.current_end_date = end
            # 保存原始数据（用于后续日期变化时重新计算）
            self.raw_df = df.copy()

            # 使用估值计算器，在用户选择的日期范围内计算百分位
            calculator = ValuationCalculator(df, self.current_valuation_type)
            df_with_valuation = calculator.calculate_percentile_in_range(start, end)
            self.current_df = df_with_valuation

            self._update_info(df_with_valuation, stock_code, stock_name)
            self.chart_view.plot_data(df_with_valuation, stock_code, stock_name,
                                      valuation_type=self.current_valuation_type)
            
            # 重置滑块到默认位置
            self.dual_slider.set_values(0, 100)
            self.range_label.config(text="显示全部数据")

            self._load_stock_memory()

        except Exception as e:
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            messagebox.showerror("错误", f"查询失败: {str(e)}")

    def _on_refresh(self):
        if not self.current_stock_code:
            messagebox.showwarning("警告", "请先查询股票")
            return

        # 显示进度对话框
        self.progress_dialog = ProgressDialog(self.root, title="正在刷新数据")
        self.root.update()

        try:
            start = self.start_date.get_date().strftime('%Y-%m-%d')
            end = self.end_date.get_date().strftime('%Y-%m-%d')

            df, stock_name = self.data_fetcher.fetch_stock_data(self.current_stock_code, start, end, force_update=True)

            # 关闭进度对话框
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            if not df.empty:
                self.current_df = df
                self.current_stock_name = stock_name
                # 保存用户选择的日期范围
                self.current_start_date = start
                self.current_end_date = end
                # 保存原始数据
                self.raw_df = df.copy()

                # 使用估值计算器，在选定的日期范围内计算百分位
                calculator = ValuationCalculator(df, self.current_valuation_type)
                df_with_valuation = calculator.calculate_percentile_in_range(start, end)
                self.current_df = df_with_valuation

                self._update_info(df_with_valuation, self.current_stock_code, stock_name)
                self.chart_view.plot_data(df_with_valuation, self.current_stock_code, stock_name,
                                          valuation_type=self.current_valuation_type)
                
                # 重置滑块到默认位置
                self.dual_slider.set_values(0, 100)
                self.range_label.config(text="显示全部数据")

                messagebox.showinfo("成功", "数据已更新")
        except Exception as e:
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            messagebox.showerror("错误", f"刷新失败: {str(e)}")
    
    def _on_delete_memory(self):
        stock_input = self.stock_var.get().strip()
        if not stock_input:
            messagebox.showwarning("警告", "请选择要删除的股票")
            return
        
        stock_code = stock_input.split(' - ')[0].strip()
        
        if messagebox.askyesno("确认", f"确定要删除 {stock_code} 的数据吗？"):
            self.db.delete_stock_data(stock_code)
            self._load_stock_memory()
            self.stock_var.set("")
            self.current_df = None
            self.current_stock_code = None
            self.current_stock_name = None
            self.chart_view.clear()
            self.info_text.delete(1.0, tk.END)
            messagebox.showinfo("成功", "数据已删除")

    def _recalculate_and_display(self):
        """重新计算并显示当前数据（用于PE/PB切换）"""
        if self.raw_df is None or self.raw_df.empty:
            return

        # 获取当前日期范围
        start = getattr(self, 'current_start_date', None)
        end = getattr(self, 'current_end_date', None)

        # 从原始数据中过滤当前日期范围
        import pandas as pd
        df_filtered = self.raw_df.copy()
        # 确保date列是datetime类型
        df_filtered['date'] = pd.to_datetime(df_filtered['date'])
        if start:
            start_dt = pd.to_datetime(start)
            df_filtered = df_filtered[df_filtered['date'] >= start_dt]
        if end:
            end_dt = pd.to_datetime(end)
            df_filtered = df_filtered[df_filtered['date'] <= end_dt]
        df_filtered = df_filtered.reset_index(drop=True)

        if df_filtered.empty:
            return

        # 使用新的估值类型在选定的日期范围内重新计算
        calculator = ValuationCalculator(df_filtered, self.current_valuation_type)
        df_with_valuation = calculator.calculate_percentile_in_range(start, end)
        self.current_df = df_with_valuation

        self._update_info(df_with_valuation, self.current_stock_code, self.current_stock_name)
        self.chart_view.plot_data(df_with_valuation, self.current_stock_code, self.current_stock_name,
                                  valuation_type=self.current_valuation_type)
        
        # 重置滑块到默认位置
        self.dual_slider.set_values(0, 100)
        self.range_label.config(text="显示全部数据")

    def _update_info(self, df, stock_code, stock_name=None):
        if df.empty:
            return

        latest = df.iloc[-1]
        earliest = df.iloc[0]

        # 根据估值类型获取百分位
        if self.current_valuation_type == 'PE':
            percentile = latest.get('pe_percentile', 0)
            valuation_label = "PE百分位"
        else:
            percentile = latest.get('pb_percentile', 0)
            valuation_label = "PB百分位"

        # 获取阈值配置
        config = VALUATION_TYPES.get(self.current_valuation_type, {})
        low_threshold = config.get('low_threshold', 30)
        high_threshold = config.get('high_threshold', 70)

        if percentile < low_threshold:
            status = "低估"
        elif percentile > high_threshold:
            status = "高估"
        else:
            status = "正常"

        # 显示公司名
        name_display = f" ({stock_name})" if stock_name and stock_name != stock_code else ""

        info = f"""
股票代码: {stock_code}{name_display}
估值类型: {self.current_valuation_type} ({config.get('name', '')})
数据区间: {earliest['date'].strftime('%Y-%m-%d')} 至 {latest['date'].strftime('%Y-%m-%d')}
数据条数: {len(df)} 条

=== 最新数据 ===
日期: {latest['date'].strftime('%Y-%m-%d')}
收盘价: {latest['close']:.2f}
{valuation_label}: {percentile:.2f}%
估值状态: {status}

=== 统计信息 ===
最高价: {df['close'].max():.2f}
最低价: {df['close'].min():.2f}
平均价: {df['close'].mean():.2f}

=== 百分位说明 ===
< {low_threshold}%: 低估 (绿色)
{low_threshold}%-{high_threshold}%: 正常 (橙色)
> {high_threshold}%: 高估 (红色)
"""

        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)


def main():
    root = tk.Tk()
    app = StockPEApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
