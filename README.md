# CANoe报告转换工具

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://python.org)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-green.svg)](https://docs.python.org/3/library/tkinter.html)

## 项目简介

CANoe报告转换工具是一个用于将CANoe测试报告从XML格式转换为HTML格式的桌面应用程序。该工具提供了友好的图形用户界面，支持批量转换和美观的报告展示。

## 功能特点

- 🔄 **格式转换**: 将XML格式的测试报告转换为HTML格式
- 🎨 **美观界面**: 现代化的GUI设计，操作简单直观
- 📊 **详细展示**: 支持测试步骤详细展示和NT（跳过）用例展示
- 📱 **响应式设计**: 支持各种屏幕尺寸，适配不同设备
- 🚀 **一键打包**: 内置打包脚本，可生成独立可执行文件
- 🌐 **浏览器预览**: 生成的报告可直接在浏览器中查看

## 项目结构

```
CANoe报告转换工具/
├── test_report_generator.py    # 核心转换逻辑
├── test_report_gui.py          # GUI界面程序
├── build_gui.py                # 打包脚本
├── requirements.txt            # 依赖包列表
├── 打包程序.bat               # 一键打包批处理文件
├── build/                      # 构建输出目录
├── dist/                       # 打包后的可执行文件目录
├── .gitignore                  # Git忽略文件
└── README.md                   # 项目说明文档
```

## 快速开始

### 环境要求

- Python 3.7 或更高版本
- Windows 7 及以上版本（推荐Windows 10）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

#### 方式一：直接运行Python脚本

```bash
python test_report_gui.py
```

#### 方式二：使用打包后的可执行文件

1. 运行打包脚本：
   ```bash
   python build_gui.py
   ```
   或者双击 `打包程序.bat`

2. 打包完成后，在 `dist` 目录下会生成 `测试报告生成器.exe`

3. 双击运行可执行文件

## 使用方法

1. **启动程序**: 双击运行 `测试报告生成器.exe` 或执行Python脚本
2. **选择输入文件**: 点击"浏览"按钮选择XML测试报告文件
3. **选择输出位置**: 选择HTML文件的保存位置
4. **生成报告**: 点击"生成报告"按钮开始转换
5. **查看结果**: 生成完成后，点击"打开报告"在浏览器中查看

## 支持的文件格式

- **输入格式**: XML (CANoe测试报告格式)
- **输出格式**: HTML (响应式网页格式)

## 开发说明

### 主要模块

- `test_report_generator.py`: 核心转换引擎，负责解析XML文件和生成HTML报告
- `test_report_gui.py`: GUI界面程序，基于Tkinter构建
- `build_gui.py`: 打包脚本，使用PyInstaller将程序打包成可执行文件

### 技术栈

- **后端**: Python 3.7+
- **GUI框架**: Tkinter
- **XML解析**: xml.etree.ElementTree
- **打包工具**: PyInstaller


## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 联系方式

- 作者: fanshuhua
- 邮箱: fanshuhua@fshoo.cn
- 项目地址: [GitHub Repository](https://github.com/fshoocn/CANoeTestReportGenerator)


## 更新日志

### v6.0 (2025-07-03)
- 优化用户界面设计
- 提升转换性能
- 修复已知bug
- 增加错误处理机制

---

⭐ 如果这个项目对您有帮助，请给我们一个star！
