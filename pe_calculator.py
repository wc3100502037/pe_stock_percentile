import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class PECalculator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        if self.df.empty:
            return
        
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df.sort_values('date').reset_index(drop=True)
        
        self.df['close'] = pd.to_numeric(self.df['close'], errors='coerce')
    
    def calculate_pe_percentile(self, window_days: int = None) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame()
        
        df = self.df.copy()
        
        if window_days:
            cutoff_date = df['date'].max() - timedelta(days=window_days)
            df = df[df['date'] >= cutoff_date].reset_index(drop=True)
        
        if len(df) < 2:
            return df
        
        df['pe_percentile'] = np.nan
        df['price_percentile'] = np.nan
        
        for i in range(len(df)):
            current_price = df.loc[i, 'close']
            
            historical_prices = df.loc[:i, 'close'].values
            
            if len(historical_prices) > 1:
                percentile = (historical_prices < current_price).sum() / (len(historical_prices) - 1) * 100
                df.loc[i, 'price_percentile'] = percentile
        
        df['pe'] = df['close']
        df['pe_percentile'] = df['price_percentile']
        
        return df
    
    def get_current_percentile(self, years: int = None) -> dict:
        df = self.calculate_pe_percentile(years * 365 if years else None)
        
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        return {
            'date': latest['date'].strftime('%Y-%m-%d'),
            'close': latest['close'],
            'pe': latest.get('pe', latest['close']),
            'pe_percentile': latest.get('pe_percentile', 0),
            'price_percentile': latest.get('price_percentile', 0),
            'total_days': len(df)
        }
    
    def get_percentile_for_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        df = self.df.copy()
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        df = df[(df['date'] >= start) & (df['date'] <= end)].reset_index(drop=True)
        
        if df.empty:
            return pd.DataFrame()
        
        df['pe_percentile'] = np.nan
        df['price_percentile'] = np.nan
        
        for i in range(len(df)):
            current_price = df.loc[i, 'close']
            historical_prices = df.loc[:i, 'close'].values
            
            if len(historical_prices) > 1:
                percentile = (historical_prices < current_price).sum() / (len(historical_prices) - 1) * 100
                df.loc[i, 'price_percentile'] = percentile
        
        df['pe'] = df['close']
        df['pe_percentile'] = df['price_percentile']
        
        return df