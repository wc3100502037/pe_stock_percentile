"""
测试PE百分位计算
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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

# 手动计算百分位
all_values = df['peTTM'].values
print("所有PE值:", all_values)
print("排序后:", sorted(all_values))
print()

print("手动计算百分位:")
for i, (date, pe) in enumerate(zip(df['date'], df['peTTM'])):
    count_less = (all_values < pe).sum()
    total = len(all_values)
    percentile = count_less / (total - 1) * 100
    print(f"{date.strftime('%Y-%m-%d')}: PE={pe:2d}, 比它小的={count_less}, 总数={total}, 百分位={percentile:.1f}%")

print()
print("预期结果:")
print("PE=12 (最低) 应该接近 0%")
print("PE=22 (最高) 应该接近 100%")
print("PE=16 (中间) 应该在 40-60% 之间")
