import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'stock_data.db')

DEFAULT_YEARS = 10

STOCK_FIELDS = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST,peTTM,pbMRQ,psTTM,pcfNcfTTM"

# 时间范围配置
TIME_RANGES = {
    '1年': 1,
    '3年': 3,
    '5年': 5,
    '10年': 10,
    '全部': None
}

# 估值类型配置
VALUATION_TYPES = {
    'PE': {
        'name': '市盈率',
        'short_name': 'PE',
        'description': '股价/每股收益',
        'low_threshold': 30,   # 低估阈值
        'high_threshold': 70   # 高估阈值
    },
    'PB': {
        'name': '市净率',
        'short_name': 'PB',
        'description': '股价/每股净资产',
        'low_threshold': 30,
        'high_threshold': 70
    }
}