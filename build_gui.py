#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试报告生成器打包脚本
使用PyInstaller将GUI程序打包成可执行文件
"""

import os
import sys
import subprocess
from pathlib import Path

def install_requirements():
    """安装必要的依赖"""
    print("检查并安装依赖包...")
    
    requirements = [
        'pyinstaller',
        'tkinter'  # 通常Python自带，但某些环境可能需要单独安装
    ]
    
    for package in requirements:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"📦 正在安装 {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def create_spec_file():
    """创建PyInstaller配置文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['test_report_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'xml.etree.ElementTree',
        'pathlib',
        'datetime',
        'json',
        'webbrowser'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='测试报告生成器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定
)
'''
    
    with open('test_report_generator.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 已创建PyInstaller配置文件: test_report_generator.spec")

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    try:
        # 使用PyInstaller构建
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            'test_report_generator.spec'
        ]
        
        subprocess.check_call(cmd)
        print("✅ 构建完成!")
        
        # 检查输出文件
        exe_path = Path('dist') / '测试报告生成器.exe'
        if exe_path.exists():
            print(f"✅ 可执行文件已生成: {exe_path}")
            print(f"📁 文件大小: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        else:
            print("❌ 未找到生成的可执行文件")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        return False
    
    return True

def create_installer_info():
    """创建安装说明文件"""
    readme_content = """# 测试报告生成器

## 使用说明

1. 双击运行"测试报告生成器.exe"
2. 点击"浏览"按钮选择XML测试报告文件
3. 选择输出HTML文件的保存位置
4. 点击"生成报告"按钮
5. 生成完成后，点击"打开报告"在浏览器中查看

## 系统要求

- Windows 7 及以上版本
- 无需安装Python环境

## 功能特点

- 支持XML格式的测试报告解析
- 生成美观的HTML格式报告
- 支持测试步骤详细展示
- 支持NT（跳过）用例展示
- 响应式设计，支持各种屏幕尺寸

## 版本信息

版本: v6.0
更新日期: 2025年7月3日

## 联系方式

如有问题或建议，请联系fanshuhua@fshoo.cn。
"""
    
    with open('dist/使用说明.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ 已创建使用说明文件")

def main():
    """主函数"""
    print("=" * 60)
    print("测试报告生成器打包工具")
    print("=" * 60)
    
    # 检查必要文件
    required_files = ['test_report_gui.py', 'test_report_generator.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            return
    
    try:
        # 1. 安装依赖
        install_requirements()
        
        # 2. 创建配置文件
        create_spec_file()
        
        # 3. 构建可执行文件
        if build_executable():
            # 4. 创建说明文件
            create_installer_info()
            
            print("\n" + "=" * 60)
            print("✅ 打包完成!")
            print("📁 可执行文件位置: dist/测试报告生成器.exe")
            print("=" * 60)
        else:
            print("\n❌ 打包失败!")
            
    except Exception as e:
        print(f"\n❌ 打包过程中发生错误: {e}")

if __name__ == "__main__":
    main()
