"""
中文字体配置模块
解决matplotlib中文显示问题
"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import os

def setup_chinese_font():
    """配置matplotlib中文字体"""
    system = platform.system()
    
    # 设置全局字体配置
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    if system == 'Windows':
        # Windows系统常见中文字体
        chinese_fonts = [
            'Microsoft YaHei',      # 微软雅黑
            'SimHei',               # 黑体
            'SimSun',               # 宋体
            'NSimSun',              # 新宋体
            'FangSong',             # 仿宋
            'KaiTi',                # 楷体
            'Arial Unicode MS',
        ]
    elif system == 'Darwin':  # macOS
        chinese_fonts = [
            'Arial Unicode MS',
            'Heiti TC',
            'PingFang HK',
            'STHeiti',
        ]
    else:  # Linux
        chinese_fonts = [
            'WenQuanYi Micro Hei',
            'WenQuanYi Zen Hei',
            'Noto Sans CJK SC',
            'Source Han Sans SC',
        ]
    
    # 获取系统可用字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 找到第一个可用的中文字体
    selected_font = None
    for font in chinese_fonts:
        if font in available_fonts:
            selected_font = font
            break
    
    if selected_font:
        plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
        print(f"已设置中文字体: {selected_font}")
    else:
        print("警告: 未找到合适的中文字体，中文可能显示为方框")
        print("可用字体:", available_fonts[:20], "...")
    
    return selected_font

def get_font_info():
    """获取当前字体配置信息"""
    return {
        'sans-serif': plt.rcParams['font.sans-serif'][:5],
        'axes.unicode_minus': plt.rcParams['axes.unicode_minus']
    }

# 自动配置字体
if __name__ != '__main__':
    setup_chinese_font()