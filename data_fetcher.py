import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from database import StockDatabase
from config import STOCK_FIELDS, DEFAULT_YEARS
import socket


def check_network_connection():
    """检查网络连接状态"""
    try:
        # 尝试连接百度服务器，超时3秒
        socket.create_connection(("www.baidu.com", 80), timeout=3)
        return True
    except OSError:
        return False


def is_trading_day(date: datetime) -> bool:
    """判断是否为交易日（非周末且非节假日）"""
    # 先判断是否为周末
    if date.weekday() >= 5:  # 周六=5, 周日=6
        return False
    
    # 简单节假日判断（主要节假日）
    # 注意：这里只包含固定日期的节假日，农历节日需要更复杂的计算
    month_day = (date.month, date.day)
    
    # 固定节假日（元旦、劳动节、国庆节等）
    fixed_holidays = [
        (1, 1),   # 元旦
        (5, 1),   # 劳动节
        (10, 1), (10, 2), (10, 3),  # 国庆节
    ]
    
    if month_day in fixed_holidays:
        return False
    
    return True


class DataFetcher:
    def __init__(self, progress_callback=None):
        self.db = StockDatabase()
        self._logged_in = False
        self.progress_callback = progress_callback  # 进度回调函数
        self._stock_name_cache = {}  # 缓存股票名称
    
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def _report_progress(self, message: str, percent: int = None):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(message, percent)
    
    def login(self):
        if not self._logged_in:
            self._report_progress("正在连接Baostock服务器...", 5)
            lg = bs.login()
            if lg.error_code == '0':
                self._logged_in = True
                self._report_progress("连接成功", 10)
                return True
            else:
                self._report_progress(f"连接失败: {lg.error_msg}", 0)
                return False
        return True
    
    def logout(self):
        if self._logged_in:
            bs.logout()
            self._logged_in = False
    
    def normalize_stock_code(self, code: str) -> str:
        """
        标准化股票代码
        支持格式：sh.600519, sz.000001, 600519, 000001
        """
        code = code.strip().lower()

        # 如果已经包含前缀，直接返回
        if '.' in code:
            return code

        # 根据股票代码规则判断市场
        # 沪市：60, 68, 69 开头（主板、科创板）
        # 深市：00, 30 开头（主板、创业板）
        # 北交所：4, 8 开头
        if code.startswith('6') or code.startswith('68') or code.startswith('69'):
            return f'sh.{code}'
        elif code.startswith('0') or code.startswith('3'):
            return f'sz.{code}'
        elif code.startswith('4') or code.startswith('8'):
            return f'bj.{code}'
        else:
            # 无法识别的代码，默认尝试沪市，后续会验证是否存在
            return f'sh.{code}'

    def try_normalize_stock_code(self, code: str) -> str:
        """
        尝试标准化股票代码，如果沪市不存在则尝试深市
        用于处理无法确定市场的裸代码
        """
        code = code.strip().lower()

        # 如果已经包含前缀，直接返回
        if '.' in code:
            return code

        # 根据规则先尝试确定的市场
        normalized = self.normalize_stock_code(code)

        # 验证股票是否存在
        if self.login():
            rs = bs.query_stock_basic(code=normalized)
            if rs.error_code == '0' and rs.next():
                return normalized

            # 如果不存在，尝试另一个市场
            if normalized.startswith('sh.'):
                alternative = f'sz.{code}'
            else:
                alternative = f'sh.{code}'

            rs = bs.query_stock_basic(code=alternative)
            if rs.error_code == '0' and rs.next():
                return alternative

        return normalized
    
    def get_stock_name(self, stock_code: str) -> str:
        """
        获取股票中文名称
        支持裸股票代码输入，自动匹配市场
        """
        # 尝试标准化并验证股票代码
        normalized_code = self.try_normalize_stock_code(stock_code)

        # 先检查缓存
        if normalized_code in self._stock_name_cache:
            return self._stock_name_cache[normalized_code]

        if not self.login():
            return stock_code

        try:
            # 使用query_stock_basic获取股票基本信息
            rs = bs.query_stock_basic(code=normalized_code)

            if rs.error_code == '0' and rs.next():
                data = rs.get_row_data()
                # 返回股票名称（code_name字段）
                stock_name = data[1] if len(data) > 1 and data[1] else stock_code
                self._stock_name_cache[normalized_code] = stock_name
                return stock_name
        except Exception as e:
            print(f"获取股票名称失败: {e}")

        return stock_code
    
    def fetch_stock_data(self, stock_code: str, start_date: str = None, end_date: str = None, 
                         force_update: bool = False) -> tuple:
        """
        获取股票数据
        返回: (DataFrame, stock_name) 元组
        支持裸股票代码输入（如 600519、000001），自动匹配市场
        """
        # 尝试标准化股票代码，如果不存在则尝试另一个市场
        normalized_code = self.try_normalize_stock_code(stock_code)
        print(f"[DEBUG] fetch_stock_data: 输入={stock_code}, 标准化={normalized_code}")

        # 获取股票名称
        self._report_progress("正在获取股票信息...", 2)
        stock_name = self.get_stock_name(stock_code)
        self._report_progress(f"股票: {stock_name}", 3)
        print(f"[DEBUG] 股票名称: {stock_name}")
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if start_date is None:
            start = datetime.now() - timedelta(days=365 * DEFAULT_YEARS)
            start_date = start.strftime('%Y-%m-%d')
        
        self._report_progress(f"准备获取 {normalized_code} ({stock_name}) 的数据...", 0)
        
        # 检查网络连接
        if not check_network_connection():
            self._report_progress("网络未连接，尝试使用本地数据...", 0)
            print("[DEBUG] 网络未连接")
            # 网络断开时，尝试使用本地数据
            existing_data = self.db.get_stock_data(normalized_code, start_date, end_date)
            if not existing_data.empty:
                self._report_progress(f"使用本地缓存数据 ({len(existing_data)} 条)", 100)
                print(f"[DEBUG] 网络断开，使用本地数据: {len(existing_data)} 条")
                return existing_data, stock_name
            else:
                self._report_progress("无网络且无本地数据", 0)
                return pd.DataFrame(), stock_name
        
        if not force_update:
            existing_data = self.db.get_stock_data(normalized_code, start_date, end_date)
            last_update = self.db.get_last_update_date(normalized_code)
            print(f"[DEBUG] 本地数据: {len(existing_data)} 条, 最后更新: {last_update}, 请求结束日期: {end_date}")
            
            if not existing_data.empty and last_update and last_update >= end_date:
                self._report_progress(f"使用本地缓存数据 ({len(existing_data)} 条)", 100)
                print(f"[DEBUG] 使用本地缓存数据")
                return existing_data, stock_name
            
            if last_update and last_update < end_date:
                # 判断是否需要更新到end_date（考虑交易日）
                last_update_date = datetime.strptime(last_update, '%Y-%m-%d')
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                
                # 找到从last_update+1到end_date之间的最后一个交易日
                current_date = last_update_date + timedelta(days=1)
                last_trading_day = None
                while current_date <= end_date_obj:
                    if is_trading_day(current_date):
                        last_trading_day = current_date
                    current_date += timedelta(days=1)
                
                if last_trading_day is None:
                    # last_update之后没有交易日，直接使用本地数据
                    self._report_progress(f"本地数据已是最新（无新交易日）", 100)
                    print(f"[DEBUG] 无新交易日，使用本地数据")
                    return existing_data, stock_name
                
                start_date = last_trading_day.strftime('%Y-%m-%d')
                self._report_progress(f"本地数据截止到 {last_update}，需要更新到 {start_date}", 15)
                print(f"[DEBUG] 需要更新数据，新开始日期: {start_date}")
        
        if not self.login():
            return pd.DataFrame(), stock_name
        
        self._report_progress(f"正在下载 {normalized_code} ({stock_name}) 从 {start_date} 到 {end_date} 的数据...", 20)
        
        rs = bs.query_history_k_data_plus(
            normalized_code,
            STOCK_FIELDS,
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"
        )
        
        if rs.error_code != '0':
            self._report_progress(f"查询失败: {rs.error_msg}", 0)
            return pd.DataFrame(), stock_name
        
        data_list = []
        total_count = 0
        batch_size = 100
        
        self._report_progress("正在接收数据...", 30)
        
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
            total_count += 1
            
            # 每100条更新一次进度
            if total_count % batch_size == 0:
                progress = min(30 + int(total_count / 10), 70)
                self._report_progress(f"已接收 {total_count} 条数据...", progress)
        
        if not data_list:
            self._report_progress("未获取到新数据", 0)
            print(f"[DEBUG] 未获取到新数据: {normalized_code}, error_code={rs.error_code}")
            
            # 如果本地有数据，返回本地数据（可能是非交易日）
            if not existing_data.empty:
                self._report_progress(f"使用本地缓存数据 ({len(existing_data)} 条)", 100)
                print(f"[DEBUG] 网络无新数据，使用本地缓存: {len(existing_data)} 条")
                return existing_data, stock_name
            
            return pd.DataFrame(), stock_name
        
        self._report_progress(f"接收到 {len(data_list)} 条数据，正在处理...", 75)
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 'volume',
                          'amount', 'turn', 'pctChg', 'peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        self._report_progress("正在保存到本地数据库...", 85)
        self.db.save_stock_data(df, normalized_code)
        self.db.save_stock_memory(normalized_code, stock_name)
        
        self._report_progress("正在加载完整数据...", 95)
        full_data = self.db.get_stock_data(normalized_code)
        
        self._report_progress(f"数据获取完成！共 {len(full_data)} 条", 100)
        
        return full_data, stock_name
