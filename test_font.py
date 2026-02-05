"""测试中文字体配置"""
import matplotlib.pyplot as plt
import font_config

print("字体配置信息:")
print(font_config.get_font_info())

# 创建测试图表
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot([1, 2, 3], [1, 4, 2])
ax.set_title('中文标题测试 - 股价走势', fontsize=14)
ax.set_xlabel('日期', fontsize=12)
ax.set_ylabel('价格 (元)', fontsize=12)
ax.legend(['收盘价'], loc='upper left')
ax.grid(True, alpha=0.3)

# 添加文本注释
ax.text(2, 3, '这是一个中文文本测试\n百分位: 75.5%', 
        fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('test_chinese.png', dpi=100, bbox_inches='tight')
print("\n测试图表已保存到 test_chinese.png")
print("如果图片中的中文显示正常，则字体配置成功！")