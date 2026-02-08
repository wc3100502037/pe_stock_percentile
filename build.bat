@echo off
chcp 65001 >nul
echo ==========================================
echo 股票估值百分位分析工具 - 打包脚本
echo ==========================================
echo.

REM 检查Python环境
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境，请先创建虚拟环境
    pause
    exit /b 1
)

echo [1/5] 检查并安装PyInstaller...
.venv\Scripts\python.exe -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo [错误] PyInstaller安装失败，请检查网络连接
    pause
    exit /b 1
)
echo [1/5] PyInstaller准备完成
echo.

echo [2/5] 清理旧打包文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo [2/5] 清理完成
echo.

echo [3/5] 开始打包...
echo 打包参数:
echo   - 单文件模式
echo   - 窗口模式(无控制台)
echo   - 包含数据文件
.
.venv\Scripts\python.exe -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "股票估值百分位分析工具" ^
    --icon "NONE" ^
    --add-data "config.py;." ^
    --add-data "database.py;." ^
    --add-data "data_fetcher.py;." ^
    --add-data "valuation_calculator.py;." ^
    --add-data "chart_view.py;." ^
    --add-data "font_config.py;." ^
    --add-data "gui.py;." ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --hidden-import matplotlib ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --hidden-import tkcalendar ^
    --hidden-import baostock ^
    --hidden-import sqlite3 ^
    main.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo [3/5] 打包完成
echo.

echo [4/5] 复制必要文件到输出目录...
if not exist "dist\config" mkdir "dist\config"
copy "config.py" "dist\" >nul 2>&1
copy "requirements.txt" "dist\" >nul 2>&1
xcopy /s /i /y "Doc" "dist\Doc\" >nul 2>&1
echo [4/5] 文件复制完成
echo.

echo [5/5] 创建启动脚本...
echo @echo off > "dist\启动程序.bat"
echo chcp 65001 ^>nul >> "dist\启动程序.bat"
echo echo 正在启动股票估值百分位分析工具... >> "dist\启动程序.bat"
echo start "" "股票估值百分位分析工具.exe" >> "dist\启动程序.bat"
echo [5/5] 启动脚本创建完成
echo.

echo ==========================================
echo 打包成功！
echo ==========================================
echo.
echo 输出文件位置:
echo   dist\股票估值百分位分析工具.exe
echo.
echo 使用说明:
echo   1. 将整个dist文件夹复制到目标位置
echo   2. 双击"启动程序.bat"或直接运行exe
echo   3. 首次运行可能需要等待解压
echo.
echo 注意事项:
echo   - 确保目标电脑有网络连接(用于获取股票数据)
echo   - 程序会在运行目录创建数据库文件
echo   - 建议将程序放在非系统盘运行
echo.
pause
