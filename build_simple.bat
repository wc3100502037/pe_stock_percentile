@echo off
chcp 65001 >nul
echo ==========================================
echo 股票估值百分位分析工具 - 打包脚本
echo ==========================================
echo.

REM 检查Python环境
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境
    echo 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

echo [1/4] 检查PyInstaller...
.venv\Scripts\python.exe -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装PyInstaller...
    .venv\Scripts\python.exe -m pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller安装失败
        pause
        exit /b 1
    )
)
echo [1/4] PyInstaller已就绪
echo.

echo [2/4] 清理旧文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo [2/4] 清理完成
echo.

echo [3/4] 开始打包...
echo 这可能需要几分钟，请耐心等待...
echo.
.venv\Scripts\python.exe -m PyInstaller build.spec --clean

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo [3/4] 打包完成
echo.

echo [4/4] 整理输出文件...
if not exist "dist\Doc" mkdir "dist\Doc"
xcopy /s /i /y "Doc" "dist\Doc\" >nul 2>&1
copy "requirements.txt" "dist\" >nul 2>&1
echo [4/4] 文件整理完成
echo.

echo ==========================================
echo 打包成功！
echo ==========================================
echo.
echo 输出位置: dist\股票估值百分位分析工具.exe
echo.
echo 使用说明:
echo   1. 复制整个dist文件夹到目标电脑
echo   2. 直接运行exe文件即可
echo.
pause
