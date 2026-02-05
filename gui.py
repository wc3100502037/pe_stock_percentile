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


class ProgressDialog:
    """进度对话框"""
    def __init__(self, parent, title="下载进度"):
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

        self._create_widgets()
        self._load_stock_memory()

        # 启动后自动加载上证指数
        self.root.after(100, self._load_default_index)
    
    def _on_progress(self, message: str, percent: int = None):
        """进度回调函数"""
        if self.progress_dialog and self.progress_dialog.dialog.winfo_exists():
            self.progress_dialog.update_progress(message, percent)
    
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
        valuation_combo = ttk.Combobox(date_frame, textvariable=self.valuation_var,
                                       values=list(VALUATION_TYPES.keys()), width=6, state='readonly')
        valuation_combo.grid(row=0, column=7, padx=5)
        valuation_combo.bind('<<ComboboxSelected>>', self._on_valuation_change)
        
        slider_frame = ttk.LabelFrame(main_frame, text="起始日期选择", padding="10")
        slider_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        slider_frame.columnconfigure(0, weight=1)
        
        self.slider = ttk.Scale(slider_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                command=self._on_slider_change)
        self.slider.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        
        self.slider_label = ttk.Label(slider_frame, text="显示全部数据")
        self.slider_label.grid(row=0, column=1, padx=5)
        
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
        stocks = self.db.get_stock_memory()
        # 按最近使用时间排序，显示格式：代码 - 公司名
        stock_list = []
        for code, name in stocks:
            if name and name != code:
                stock_list.append(f"{code} - {name}")
            else:
                stock_list.append(code)
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

        info = f"""
股票代码: {stock_code}
股票名称: {stock_name or stock_code}
当前日期: {latest['date'].strftime('%Y-%m-%d')}
收盘价: {latest['close']:.2f}

{valuation_label}: {percentile:.2f}%
估值水平: {level} ({level_color})

数据范围: {earliest['date'].strftime('%Y-%m-%d')} 至 {latest['date'].strftime('%Y-%m-%d')}
数据条数: {len(df)}
{date_note}
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

                print(f"{'='*60}\n")
            except Exception as e:
                print(f"日期变化处理错误: {e}")
                import traceback
                traceback.print_exc()
                pass  # 日期格式不正确时忽略
    
    def _on_slider_change(self, value):
        if self.current_df is None or self.current_df.empty:
            return
        
        slider_val = int(float(value))
        total_points = len(self.current_df)
        start_idx = int((slider_val / 100) * total_points)
        
        if start_idx >= total_points:
            start_idx = total_points - 1
        
        if start_idx < total_points:
            start_date = self.current_df.iloc[start_idx]['date']
            self.slider_label.config(text=f"从 {start_date.strftime('%Y-%m-%d')} 开始")
            
            self.chart_view.plot_data(self.current_df, self.current_stock_code, self.current_stock_name, start_idx)
    
    def _on_search(self):
        stock_input = self.stock_var.get().strip()
        if not stock_input:
            messagebox.showwarning("警告", "请输入股票代码")
            return

        stock_code = stock_input.split(' - ')[0].strip()

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
                messagebox.showwarning("警告", f"未找到股票 {stock_code} 的数据")
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
