"""
测试完整场景：模拟从数据库读取数据并计算百分位
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from valuation_calculator import ValuationCalculator

# 创建模拟的真实数据（从数据库读取的格式）
dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
np.random.seed(42)
pe_values = np.random.uniform(10, 30, 100)  # PE在10-30之间随机

# 模拟数据库返回的数据框（注意：PE值可能是字符串类型）
df = pd.DataFrame({
    'date': dates,
    'code': ['sh.000001'] * 100,
    'open': [100.0] * 100,
    'high': [110.0] * 100,
    'low': [90.0] * 100,
    'close': [105.0] * 100,
    'volume': [1000000] * 100,
    'amount': [100000000.0] * 100,
    'turn': [5.0] * 100,
    'pctChg': [1.0] * 100,
    'peTTM': pe_values.astype(str),  # 模拟从数据库读取的字符串类型
    'pbMRQ': [1.5] * 100,
    'psTTM': [2.0] * 100,
    'pcfNcfTTM': [10.0] * 100
})

print("原始数据类型:")
print(f"peTTM类型: {df['peTTM'].dtype}")
print(f"peTTM前5个值: {df['peTTM'].head().tolist()}")
print()

# 测试场景1：计算完整范围的百分位
print("=" * 60)
print("场景1：完整范围（2020-01-01 到 2020-04-09）")
print("=" * 60)

calculator = ValuationCalculator(df, 'PE')
result = calculator.calculate_percentile_in_range('2020-01-01', '2020-04-09')

print(f"数据条数: {len(result)}")
print(f"PE范围: {result['pe'].min():.2f} - {result['pe'].max():.2f}")
print(f"百分位范围: {result['pe_percentile'].min():.2f}% - {result['pe_percentile'].max():.2f}%")
print()

# 验证最小值和最大值
min_idx = result['pe'].idxmin()
max_idx = result['pe'].idxmax()
print(f"最小PE={result.loc[min_idx, 'pe']:.2f}, 百分位={result.loc[min_idx, 'pe_percentile']:.2f}%")
print(f"最大PE={result.loc[max_idx, 'pe']:.2f}, 百分位={result.loc[max_idx, 'pe_percentile']:.2f}%")
print()

# 测试场景2：缩小日期范围
print("=" * 60)
print("场景2：缩小范围（2020-03-01 到 2020-04-09）")
print("=" * 60)

result2 = calculator.calculate_percentile_in_range('2020-03-01', '2020-04-09')

print(f"数据条数: {len(result2)}")
print(f"PE范围: {result2['pe'].min():.2f} - {result2['pe'].max():.2f}")
print(f"百分位范围: {result2['pe_percentile'].min():.2f}% - {result2['pe_percentile'].max():.2f}%")
print()

# 验证最小值和最大值
min_idx2 = result2['pe'].idxmin()
max_idx2 = result2['pe'].idxmax()
print(f"最小PE={result2.loc[min_idx2, 'pe']:.2f}, 百分位={result2.loc[min_idx2, 'pe_percentile']:.2f}%")
print(f"最大PE={result2.loc[max_idx2, 'pe']:.2f}, 百分位={result2.loc[max_idx2, 'pe_percentile']:.2f}%")
print()

# 显示部分数据
print("前10条数据:")
print(result2[['date', 'pe', 'pe_percentile']].head(10).to_string(index=False))
