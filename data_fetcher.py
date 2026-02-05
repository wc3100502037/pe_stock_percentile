import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from database import StockDatabase
from config import STOCK_FIELDS, DEFAULT_YEARS


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

        # 获取股票名称
        self._report_progress("正在获取股票信息...", 2)
        stock_name = self.get_stock_name(stock_code)
        self._report_progress(f"股票: {stock_name}", 3)
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if start_date is None:
            start = datetime.now() - timedelta(days=365 * DEFAULT_YEARS)
            start_date = start.strftime('%Y-%m-%d')
        
        self._report_progress(f"准备获取 {normalized_code} ({stock_name}) 的数据...", 0)
        
        if not force_update:
            existing_data = self.db.get_stock_data(normalized_code, start_date, end_date)
            last_update = self.db.get_last_update_date(normalized_code)
            
            if not existing_data.empty and last_update and last_update >= end_date:
                self._report_progress(f"使用本地缓存数据 ({len(existing_data)} 条)", 100)
                return existing_data, stock_name
            
            if last_update and last_update < end_date:
                start_date = (datetime.strptime(last_update, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                self._report_progress(f"本地数据截止到 {last_update}，需要更新", 15)
        
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
            self._report_progress("未获取到数据", 0)
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
