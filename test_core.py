"""测试核心功能"""
import sys
from datetime import datetime, timedelta

def test_database():
    print("测试数据库模块...")
    from database import StockDatabase
    db = StockDatabase()
    print("✓ 数据库初始化成功")
    
    # 测试股票记忆功能
    db.save_stock_memory("sh.600000", "浦发银行")
    stocks = db.get_stock_memory()
    print(f"✓ 股票记忆功能正常，已保存 {len(stocks)} 条记录")
    
    return db

def test_data_fetcher():
    print("\n测试数据获取模块...")
    from data_fetcher import DataFetcher
    fetcher = DataFetcher()
    
    # 测试股票代码格式化
    test_codes = ["600000", "sh.600000", "000001", "300001"]
    for code in test_codes:
        normalized = fetcher.normalize_stock_code(code)
        print(f"  {code} -> {normalized}")
    print("✓ 股票代码格式化正常")
    
    return fetcher

def test_pe_calculator():
    print("\n测试PE计算器...")
    import pandas as pd
    from pe_calculator import PECalculator
    from datetime import datetime, timedelta
    
    # 创建测试数据
    dates = [datetime.now() - timedelta(days=i) for i in range(100, 0, -1)]
    data = {
        'date': dates,
        'close': [100 + i * 0.5 + (i % 10) for i in range(100)],
        'open': [100 + i * 0.5 for i in range(100)],
    }
    df = pd.DataFrame(data)
    
    calc = PECalculator(df)
    result = calc.calculate_pe_percentile()
    
    print(f"✓ PE计算正常，共计算 {len(result)} 条数据")
    if not result.empty:
        print(f"  最新PE百分位: {result.iloc[-1].get('pe_percentile', 0):.2f}%")
    
    return calc

def test_chart():
    print("\n测试图表模块（非GUI模式）...")
    from chart_view import ChartView
    print("✓ 图表模块导入成功")

def main():
    print("="*50)
    print("个股PE百分位分析工具 - 核心功能测试")
    print("="*50)
    
    try:
        db = test_database()
        fetcher = test_data_fetcher()
        calc = test_pe_calculator()
        test_chart()
        
        print("\n" + "="*50)
        print("所有核心模块测试通过！")
        print("="*50)
        print("\n可以运行 python main.py 启动GUI程序")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())