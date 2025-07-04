@echo off
chcp 65001 >nul
echo ========================================
echo 测试报告生成器 - 一键打包工具
echo ========================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 请先安装Python 3.6或更高版本
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

echo 开始打包过程...
echo ----------------------------------------
python build_gui.py

echo.
echo ----------------------------------------
echo 打包完成！
echo.
echo 生成的文件位置：
echo   📁 可执行文件: dist\测试报告生成器.exe
echo   📋 使用说明: dist\使用说明.txt
echo.
echo 按任意键退出...
pause >nul
