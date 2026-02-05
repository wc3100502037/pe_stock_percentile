"""
测试 ValuationCalculator 的百分位计算
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from valuation_calculator import ValuationCalculator

# 创建测试数据
dates = pd.date_range(start='2020-01-01', periods=10, freq='D')
pe_values = [15, 18, 12, 20, 16, 14, 22, 17, 19, 13]

df = pd.DataFrame({
    'date': dates,
    'peTTM': pe_values,
    'close': [100 + i for i in range(10)]
})

print("测试数据:")
print(df[['date', 'peTTM']])
print()

# 使用 ValuationCalculator 计算
start_date = '2020-01-01'
end_date = '2020-01-10'

calculator = ValuationCalculator(df, 'PE')
result = calculator.calculate_percentile_in_range(start_date, end_date)

print("计算结果:")
print(result[['date', 'pe', 'pe_percentile']])
print()

# 验证结果
print("验证:")
print(f"最小PE={result['pe'].min()}, 对应百分位={result.loc[result['pe'].idxmin(), 'pe_percentile']:.1f}%")
print(f"最大PE={result['pe'].max()}, 对应百分位={result.loc[result['pe'].idxmax(), 'pe_percentile']:.1f}%")
print()

# 测试缩小日期范围
print("=" * 50)
print("测试缩小日期范围: 2020-01-05 到 2020-01-10")
start_date2 = '2020-01-05'
end_date2 = '2020-01-10'

result2 = calculator.calculate_percentile_in_range(start_date2, end_date2)
print(result2[['date', 'pe', 'pe_percentile']])
print()

print("验证:")
print(f"最小PE={result2['pe'].min()}, 对应百分位={result2.loc[result2['pe'].idxmin(), 'pe_percentile']:.1f}%")
print(f"最大PE={result2['pe'].max()}, 对应百分位={result2.loc[result2['pe'].idxmax(), 'pe_percentile']:.1f}%")
