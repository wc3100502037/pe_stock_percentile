# 代码规范 - 函数注释标准

## 函数注释格式

所有函数都应该包含标准的文档字符串（docstring），格式如下：

### 基本格式

```python
def function_name(param1, param2=None):
    """
    函数的简要描述（一句话）
    
    函数的详细描述（如果需要）
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述，默认为None
        
    Returns:
        返回值的描述
        
    Raises:
        ExceptionType: 异常描述（如果有）
    """
```

### 示例

#### 1. 简单函数

```python
def add(a, b):
    """
    计算两个数的和
    
    Args:
        a: 第一个数
        b: 第二个数
        
    Returns:
        两数之和
    """
    return a + b
```

#### 2. 带类型提示的函数

```python
def fetch_stock_data(stock_code: str, start_date: str = None) -> tuple:
    """
    获取股票历史数据
    
    从Baostock获取指定股票在日期范围内的历史K线数据，
    并自动缓存到本地数据库。
    
    Args:
        stock_code: 股票代码，如 'sh.600519' 或 '600519'
        start_date: 开始日期，格式 'YYYY-MM-DD'，默认为10年前
        
    Returns:
        tuple: (DataFrame, stock_name)
            - DataFrame: 包含股票历史数据的DataFrame
            - stock_name: 股票中文名称
            
    Raises:
        ConnectionError: 网络连接失败时
        ValueError: 股票代码无效时
    """
```

#### 3. 类方法

```python
class StockDatabase:
    def get_stock_data(self, stock_code: str, start_date: str = None) -> pd.DataFrame:
        """
        从数据库获取股票数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期，格式 'YYYY-MM-DD'
            
        Returns:
            pd.DataFrame: 股票历史数据，包含以下列：
                - date: 日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
                
        Example:
            >>> db = StockDatabase()
            >>> df = db.get_stock_data('sh.600519', '2024-01-01')
            >>> print(len(df))
            100
        """
```

## 注释规范要点

### 1. 必须包含的部分

- **简要描述**：函数的主要功能（一句话）
- **Args**：所有参数的名称和说明
- **Returns**：返回值的说明

### 2. 可选包含的部分

- **详细描述**：功能的详细说明
- **Raises**：可能抛出的异常
- **Example**：使用示例
- **Note**：注意事项

### 3. 注释风格

- 使用中文注释
- 描述要简洁明了
- 参数类型在类型提示中标注，注释中可不重复
- 返回值要说明类型和含义

## 文件头注释

每个Python文件应该包含模块级别的文档字符串：

```python
"""
模块名称 - 简短描述

详细描述模块的功能和用途

主要功能：
    - 功能1
    - 功能2
    - 功能3

Usage:
    import module_name
    result = module_name.function()

Author: Your Name
Date: 2024-01-01
"""
```

## 类注释

```python
class StockPEApp:
    """
    股票PE分析应用程序主类
    
    提供图形化界面用于：
    - 股票数据查询
    - PE/PB百分位计算
    - 数据可视化展示
    
    Attributes:
        root: Tkinter根窗口
        data_fetcher: 数据获取器实例
        db: 数据库实例
        current_df: 当前显示的数据
    """
```
