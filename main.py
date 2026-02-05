#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个股PE百分位分析工具
基于Python + Tkinter + Matplotlib + Baostock

功能：
- 查询个股历史数据
- 计算PE历史百分位
- 可视化展示股价和PE百分位走势
- 支持本地数据缓存
"""

import sys
import os

def check_dependencies():
    """检查必要的依赖库"""
    missing = []
    
    try:
        import tkinter
    except ImportError:
        missing.append("tkinter")
    
    try:
        import tkcalendar
    except ImportError:
        missing.append("tkcalendar")
    
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        import baostock
    except ImportError:
        missing.append("baostock")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    if missing:
        print("缺少以下依赖库，请先安装：")
        print(f"pip install {' '.join(missing)}")
        print("\n或者运行：")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主函数"""
    if not check_dependencies():
        sys.exit(1)
    
    from gui import main as gui_main
    gui_main()

if __name__ == "__main__":
    main()