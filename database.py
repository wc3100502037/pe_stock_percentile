import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_PATH

class StockDatabase:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                preclose REAL,
                volume REAL,
                amount REAL,
                adjustflag TEXT,
                turn REAL,
                tradestatus TEXT,
                pctChg REAL,
                isST TEXT,
                peTTM REAL,
                pbMRQ REAL,
                psTTM REAL,
                pcfNcfTTM REAL,
                UNIQUE(date, code)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT,
                last_updated TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_history_code_date 
            ON stock_history(code, date)
        ''')
        
        conn.commit()
        conn.close()
    
    def save_stock_data(self, df: pd.DataFrame, stock_code: str):
        if df.empty:
            return
        
        conn = self.get_connection()
        
        df = df.copy()
        df['code'] = stock_code
        
        columns = ['date', 'code', 'open', 'high', 'low', 'close', 'preclose',
                   'volume', 'amount', 'adjustflag', 'turn', 'tradestatus', 'pctChg', 'isST',
                   'peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']
        
        existing_columns = [col for col in columns if col in df.columns]
        df_to_save = df[existing_columns]
        
        for _, row in df_to_save.iterrows():
            try:
                placeholders = ', '.join(['?' for _ in existing_columns])
                columns_str = ', '.join(existing_columns)
                
                cursor = conn.cursor()
                cursor.execute(f'''
                    INSERT OR REPLACE INTO stock_history ({columns_str})
                    VALUES ({placeholders})
                ''', tuple(row))
            except Exception as e:
                print(f"Error saving row: {e}")
        
        conn.commit()
        conn.close()
    
    def get_stock_data(self, stock_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        conn = self.get_connection()
        
        query = "SELECT * FROM stock_history WHERE code = ?"
        params = [stock_code]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date ASC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_last_update_date(self, stock_code: str) -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(date) FROM stock_history WHERE code = ?
        ''', (stock_code,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else None
    
    def save_stock_memory(self, stock_code: str, stock_name: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO stock_memory (code, name, last_updated)
            VALUES (?, ?, ?)
        ''', (stock_code, stock_name, datetime.now().strftime('%Y-%m-%d')))
        
        conn.commit()
        conn.close()
    
    def get_stock_memory(self) -> list:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT code, name FROM stock_memory ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def delete_stock_data(self, stock_code: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM stock_history WHERE code = ?', (stock_code,))
        cursor.execute('DELETE FROM stock_memory WHERE code = ?', (stock_code,))
        
        conn.commit()
        conn.close()