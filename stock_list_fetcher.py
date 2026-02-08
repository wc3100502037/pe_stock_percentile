"""
股票列表获取模块 - 获取所有A股股票列表并存储到本地
"""
import baostock as bs
import pandas as pd
from database import StockDatabase
from datetime import datetime


def fetch_all_stock_list():
    """
    从Baostock获取所有A股股票列表
    返回: DataFrame包含code, code_name等字段
    """
    # 登录Baostock
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return pd.DataFrame()
    
    print("正在获取所有A股股票列表...")
    
    # 使用query_stock_basic不带code参数获取所有股票
    rs = bs.query_stock_basic(code="")
    
    if rs.error_code != '0':
        print(f"获取股票列表失败: {rs.error_msg}")
        bs.logout()
        return pd.DataFrame()
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    # 创建DataFrame
    df = pd.DataFrame(data_list, columns=rs.fields)
    
    bs.logout()
    
    print(f"成功获取 {len(df)} 只股票信息")
    
    # 只保留需要的列
    if 'code' in df.columns and 'code_name' in df.columns:
        # 过滤掉指数，只保留股票（type=1是股票，type=2是指数）
        if 'type' in df.columns:
            df = df[df['type'] == '1'].copy()
        
        # 选择需要的列
        result_df = df[['code', 'code_name']].copy()
        result_df.columns = ['code', 'name']
        
        # 过滤掉没有名称的股票
        result_df = result_df[result_df['name'].notna() & (result_df['name'] != '')]
        
        print(f"过滤后剩余 {len(result_df)} 只股票")
        return result_df
    
    return pd.DataFrame()


def save_stock_list_to_db(df: pd.DataFrame):
    """
    将股票列表保存到数据库
    """
    if df.empty:
        print("没有数据需要保存")
        return
    
    db = StockDatabase()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 创建股票列表表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 清空旧数据
    cursor.execute('DELETE FROM stock_list')
    
    # 插入新数据
    inserted = 0
    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO stock_list (code, name)
                VALUES (?, ?)
            ''', (row['code'], row['name']))
            inserted += 1
        except Exception as e:
            print(f"保存 {row['code']} 失败: {e}")
    
    conn.commit()
    conn.close()
    print(f"股票列表已保存到数据库，共 {inserted} 只")


def get_stock_list_from_db() -> list:
    """
    从数据库获取股票列表
    返回: [(code, name), ...]
    """
    db = StockDatabase()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT code, name FROM stock_list ORDER BY code
        ''')
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"从数据库获取股票列表失败: {e}")
        conn.close()
        return []


def is_stock_list_exists() -> bool:
    """
    检查数据库中是否已有股票列表
    """
    db = StockDatabase()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT COUNT(*) FROM stock_list')
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except:
        conn.close()
        return False


def update_stock_list():
    """
    更新股票列表的主函数
    """
    df = fetch_all_stock_list()
    if not df.empty:
        save_stock_list_to_db(df)
        print("股票列表更新完成！")
        return True
    else:
        print("获取股票列表失败")
        return False


if __name__ == "__main__":
    update_stock_list()
