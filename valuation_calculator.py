import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class ValuationCalculator:
    """估值计算器 - 支持PE和PB百分位计算"""

    def __init__(self, df: pd.DataFrame, valuation_type: str = 'PE'):
        """
        初始化估值计算器

        Args:
            df: 股票数据DataFrame
            valuation_type: 估值类型，'PE' 或 'PB'
        """
        self.df = df.copy()
        self.valuation_type = valuation_type.upper()
        self._prepare_data()

    def _prepare_data(self):
        """准备数据"""
        if self.df.empty:
            return

        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df.sort_values('date').reset_index(drop=True)
        self.df['close'] = pd.to_numeric(self.df['close'], errors='coerce')

        # 确保PE和PB列也是数值类型
        if 'peTTM' in self.df.columns:
            self.df['peTTM'] = pd.to_numeric(self.df['peTTM'], errors='coerce')
        if 'pbMRQ' in self.df.columns:
            self.df['pbMRQ'] = pd.to_numeric(self.df['pbMRQ'], errors='coerce')

    def set_valuation_type(self, valuation_type: str):
        """设置估值类型"""
        self.valuation_type = valuation_type.upper()

    def calculate_percentile_in_range(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        在指定日期范围内计算估值百分位
        百分位是基于选定范围内的数据分布计算的

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            包含估值百分位的DataFrame
        """
        if self.df.empty:
            return pd.DataFrame()

        df = self.df.copy()

        # 过滤日期范围
        if start_date:
            start = pd.to_datetime(start_date)
            df = df[df['date'] >= start]
        if end_date:
            end = pd.to_datetime(end_date)
            df = df[df['date'] <= end]

        df = df.reset_index(drop=True)

        if len(df) < 2:
            return df

        # 根据估值类型选择对应的值列
        if self.valuation_type == 'PE':
            value_col = 'peTTM'
            output_col = 'pe'
            percentile_col = 'pe_percentile'
        else:  # PB
            value_col = 'pbMRQ'
            output_col = 'pb'
            percentile_col = 'pb_percentile'

        # 检查是否有该列，如果没有则使用close作为回退
        if value_col not in df.columns:
            value_col = 'close'

        # 在选定的范围内计算百分位
        # 每个点的百分位 = (范围内比它小的值的数量) / (范围内总数量 - 1) * 100
        df['valuation_value'] = df[value_col]
        df['percentile'] = np.nan

        # 获取范围内的所有估值数据（过滤掉无效值）
        all_values = df[value_col].dropna().values

        if len(all_values) < 2:
            # 如果没有足够的有效数据，返回原始数据
            df[output_col] = df['valuation_value']
            df[percentile_col] = df['percentile']
            return df

        for i in range(len(df)):
            current_value = df.loc[i, value_col]
            if pd.isna(current_value):
                continue

            # 计算当前值在范围内的百分位
            # 使用严格小于的数量
            count_less = (all_values < current_value).sum()
            total = len(all_values)

            if total > 1:
                percentile = count_less / (total - 1) * 100
                df.loc[i, 'percentile'] = percentile

        # 设置输出列
        df[output_col] = df['valuation_value']
        df[percentile_col] = df['percentile']

        return df

    def calculate_percentile(self, window_days: int = None) -> pd.DataFrame:
        """
        计算估值百分位（基于最近N天的历史数据）

        Args:
            window_days: 时间窗口（天数），None表示使用全部数据

        Returns:
            包含估值百分位的DataFrame
        """
        if self.df.empty:
            return pd.DataFrame()

        df = self.df.copy()

        if window_days:
            cutoff_date = df['date'].max() - timedelta(days=window_days)
            df = df[df['date'] >= cutoff_date].reset_index(drop=True)

        if len(df) < 2:
            return df

        # 根据估值类型选择对应的值列
        if self.valuation_type == 'PE':
            value_col = 'peTTM'
            output_col = 'pe'
            percentile_col = 'pe_percentile'
        else:  # PB
            value_col = 'pbMRQ'
            output_col = 'pb'
            percentile_col = 'pb_percentile'

        # 检查是否有该列，如果没有则使用close作为回退
        if value_col not in df.columns:
            value_col = 'close'

        # 计算估值百分位（基于历史数据的滚动百分位）
        df['valuation_value'] = df[value_col]
        df['percentile'] = np.nan

        for i in range(len(df)):
            current_value = df.loc[i, value_col]
            if pd.isna(current_value):
                continue

            historical_values = df.loc[:i, value_col].dropna().values

            if len(historical_values) > 1:
                percentile = (historical_values < current_value).sum() / (len(historical_values) - 1) * 100
                df.loc[i, 'percentile'] = percentile

        # 设置输出列
        df[output_col] = df['valuation_value']
        df[percentile_col] = df['percentile']

        return df

    def get_current_percentile(self, years: int = None) -> dict:
        """获取当前估值百分位信息"""
        df = self.calculate_percentile(years * 365 if years else None)

        if df.empty:
            return {}

        latest = df.iloc[-1]

        result = {
            'date': latest['date'].strftime('%Y-%m-%d'),
            'close': latest['close'],
            'valuation_type': self.valuation_type,
            'total_days': len(df)
        }

        if self.valuation_type == 'PE':
            result['pe'] = latest.get('pe', latest['close'])
            result['pe_percentile'] = latest.get('percentile', 0)
        else:
            result['pb'] = latest.get('pb', latest['close'])
            result['pb_percentile'] = latest.get('percentile', 0)

        result['percentile'] = latest.get('percentile', 0)

        return result

    def get_percentile_for_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指定日期范围内的估值百分位（旧方法，保留兼容）"""
        return self.calculate_percentile_in_range(start_date, end_date)
