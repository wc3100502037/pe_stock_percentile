import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import pandas as pd

# 导入中文字体配置
import font_config

class ChartView:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.fig = Figure(figsize=(12, 10), dpi=100)
        # 创建三个子图：股价、PE/PB值、PE/PB百分位
        self.ax1 = self.fig.add_subplot(311)  # 股价
        self.ax2 = self.fig.add_subplot(312)  # PE/PB值
        self.ax3 = self.fig.add_subplot(313)  # PE/PB百分位

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.draw()

        self.toolbar = NavigationToolbar2Tk(self.canvas, parent_frame)
        self.toolbar.update()

        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar.pack(fill=tk.X)

        # 垂直线
        self.vline1 = None
        self.vline2 = None
        self.vline3 = None

        # 注释框
        self.annot1 = None
        self.annot2 = None
        self.annot3 = None

        self.data = None
        self.stock_code = ""

        self._setup_hover()
    
    def _setup_hover(self):
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_hover)
        self.fig.canvas.mpl_connect('axes_leave_event', self._on_leave)
    
    def _on_leave(self, event):
        """鼠标离开图表时清除悬停效果"""
        self._clear_hover_elements()
        self.canvas.draw_idle()
    
    def _clear_hover_elements(self):
        """清除悬停元素"""
        # 清除垂直线
        if self.vline1:
            self.vline1.remove()
            self.vline1 = None
        if self.vline2:
            self.vline2.remove()
            self.vline2 = None
        if self.vline3:
            self.vline3.remove()
            self.vline3 = None

        # 清除注释
        if self.annot1:
            self.annot1.remove()
            self.annot1 = None
        if self.annot2:
            self.annot2.remove()
            self.annot2 = None
        if self.annot3:
            self.annot3.remove()
            self.annot3 = None
    
    def _on_hover(self, event):
        if self.data is None or self.data.empty:
            return

        if event.inaxes not in [self.ax1, self.ax2, self.ax3]:
            return

        x = event.xdata
        if x is None:
            return

        try:
            # 将matplotlib的日期数字转换为datetime
            x_date = mdates.num2date(x)
            # 转换为naive datetime（去掉时区信息）以便比较
            x_date = x_date.replace(tzinfo=None)
        except:
            return

        # 找到最接近的数据点
        data_dates = pd.to_datetime(self.data['date'])
        time_diffs = abs(data_dates - x_date)
        closest_idx = time_diffs.idxmin()

        # 如果距离太远，不显示
        min_diff = time_diffs.min()
        if min_diff.days > 5:  # 超过5天就不显示
            return

        row = self.data.loc[closest_idx]

        date_str = row['date'].strftime('%Y-%m-%d')
        close = row['close']

        # 根据估值类型获取对应的数据
        if self.valuation_type == 'PE':
            valuation_value = row.get('pe', close)
            percentile = row.get('pe_percentile', 0)
            valuation_label = "PE"
        else:  # PB
            valuation_value = row.get('pb', close)
            percentile = row.get('pb_percentile', 0)
            valuation_label = "PB"

        # 获取当前数据点的y值
        y1 = close
        y2 = valuation_value if pd.notna(valuation_value) else 0
        y3 = percentile if pd.notna(percentile) else 0

        # 获取鼠标所在的x坐标（matplotlib日期格式）
        x_num = mdates.date2num(row['date'])

        info_text = f"日期: {date_str}\n股价: {close:.2f}\n{valuation_label}: {valuation_value:.2f}\n百分位: {percentile:.2f}%"

        self._update_hover_display(x_num, y1, y2, y3, info_text)
    
    def _update_hover_display(self, x, y1, y2, y3, text):
        """更新悬停显示效果"""
        self._clear_hover_elements()

        # 在第一个子图（股价）添加垂直线和注释
        self.vline1 = self.ax1.axvline(x=x, color='gray', linestyle='--', alpha=0.7, linewidth=1)
        self.annot1 = self.ax1.annotate(
            text,
            xy=(x, y1),
            xytext=(15, 15),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.9, ec='orange'),
            fontsize=9,
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='orange')
        )

        # 在第二个子图（PE/PB值）添加垂直线和注释
        self.vline2 = self.ax2.axvline(x=x, color='gray', linestyle='--', alpha=0.7, linewidth=1)
        self.annot2 = self.ax2.annotate(
            text,
            xy=(x, y2),
            xytext=(15, 15),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='lightgreen', alpha=0.9, ec='green'),
            fontsize=9,
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='green')
        )

        # 在第三个子图（百分位）添加垂直线和注释
        self.vline3 = self.ax3.axvline(x=x, color='gray', linestyle='--', alpha=0.7, linewidth=1)
        self.annot3 = self.ax3.annotate(
            text,
            xy=(x, y3),
            xytext=(15, 15),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='lightblue', alpha=0.9, ec='blue'),
            fontsize=9,
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='blue')
        )

        self.canvas.draw_idle()
    
    def plot_data(self, df, stock_code, stock_name=None, start_date_idx=0, valuation_type='PE'):
        self.data = df
        self.stock_code = stock_code
        self.stock_name = stock_name or stock_code
        self.valuation_type = valuation_type

        # 清除之前的悬停元素
        self._clear_hover_elements()

        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        if df is None or df.empty:
            self.ax1.text(0.5, 0.5, '无数据', ha='center', va='center', transform=self.ax1.transAxes)
            self.canvas.draw()
            return

        df_plot = df.iloc[start_date_idx:].copy()

        if df_plot.empty:
            df_plot = df.copy()

        dates = df_plot['date']
        closes = df_plot['close']

        # 根据估值类型获取数据
        if valuation_type == 'PE':
            valuation_values = df_plot.get('pe', pd.Series([0]*len(df_plot)))
            percentiles = df_plot.get('pe_percentile', df_plot.get('percentile', pd.Series([0]*len(df_plot))))
            valuation_value_title = 'PE值走势'
            valuation_percentile_title = 'PE历史百分位'
            valuation_value_label = 'PE值'
            valuation_percentile_label = 'PE百分位'
            line_color = 'purple'
            fill_color = 'purple'
        else:  # PB
            valuation_values = df_plot.get('pb', pd.Series([0]*len(df_plot)))
            percentiles = df_plot.get('pb_percentile', df_plot.get('percentile', pd.Series([0]*len(df_plot))))
            valuation_value_title = 'PB值走势'
            valuation_percentile_title = 'PB历史百分位'
            valuation_value_label = 'PB值'
            valuation_percentile_label = 'PB百分位'
            line_color = 'darkblue'
            fill_color = 'blue'

        # 第一个子图：绘制股价图
        self.ax1.plot(dates, closes, 'b-', linewidth=1.5, label='收盘价')
        # 显示股票代码和公司名
        display_name = f'{stock_code} ({stock_name})' if stock_name and stock_name != stock_code else stock_code
        self.ax1.set_title(f'{display_name} - 股价走势', fontsize=12, fontweight='bold')
        self.ax1.set_ylabel('价格', fontsize=10)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend(loc='upper left')

        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        self.ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(self.ax1.xaxis.get_majorticklabels(), rotation=45)

        # 第二个子图：绘制PE/PB值图
        self.ax2.plot(dates, valuation_values, color='green', linewidth=1.5, label=valuation_value_label)
        self.ax2.set_title(valuation_value_title, fontsize=12)
        self.ax2.set_ylabel(valuation_value_label, fontsize=10)
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend(loc='upper left')

        self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        self.ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(self.ax2.xaxis.get_majorticklabels(), rotation=45)

        # 第三个子图：绘制估值百分位图
        self.ax3.plot(dates, percentiles, color=line_color, linewidth=1.5, label=valuation_percentile_label)
        self.ax3.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='30% (低估)')
        self.ax3.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='70% (高估)')
        self.ax3.fill_between(dates, 0, percentiles, alpha=0.3, color=fill_color)

        self.ax3.set_title(valuation_percentile_title, fontsize=12)
        self.ax3.set_xlabel('日期', fontsize=10)
        self.ax3.set_ylabel('百分位 (%)', fontsize=10)
        self.ax3.set_ylim(0, 100)
        self.ax3.grid(True, alpha=0.3)
        self.ax3.legend(loc='upper left')

        self.ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        self.ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(self.ax3.xaxis.get_majorticklabels(), rotation=45)

        self.fig.tight_layout()
        self.canvas.draw()

    def clear(self):
        self._clear_hover_elements()
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.canvas.draw()
