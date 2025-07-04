#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试报告生成器 - 解析XML测试报告并生成美观的HTML报告
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import os
import json

class TestReportData:
    """测试报告数据类"""
    
    def __init__(self):
        self.start_time = ""
        self.end_time = ""
        self.timestamp = ""
        self.verdicts = ""
        self.title = ""
        self.preparation = None
        self.test_groups = []
        self.test_items = []  # 按顺序存储所有测试项（包括skipped和testcase）
        self.engineer_info = {}
        self.testsetup_info = {}
        self.hardware_info = {}

class TestCase:
    """测试用例类"""
    
    def __init__(self):
        self.item_type = "testcase"
        self.start_time = ""
        self.timestamp = ""
        self.title = ""
        self.end_time = ""
        self.end_timestamp = ""
        self.description = ""
        self.verdict = ""
        self.test_steps = []

class SkippedTest:
    """跳过的测试类"""
    
    def __init__(self):
        self.item_type = "skipped"
        self.start_time = ""
        self.timestamp = ""
        self.title = ""

class TestStep:
    """测试步骤类"""
    
    def __init__(self):
        self.timestamp = ""
        self.level = ""
        self.type = ""
        self.ident = ""
        self.result = ""
        self.content = ""
        self.tabular_info = None

class TabularInfo:
    """表格信息类"""
    
    def __init__(self):
        self.expand = ""
        self.description = ""
        self.headings = []
        self.rows = []

class TestReportParser:
    """测试报告解析器"""
    
    def __init__(self, xml_file_path):
        self.xml_file_path = xml_file_path
        self.report_data = TestReportData()
    
    def parse(self):
        """解析XML文件"""
        try:
            print("开始解析XML文件...")
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            
            # 解析根元素属性
            self.report_data.start_time = root.get('starttime', '')
            self.report_data.end_time = root.get('endtime', '')
            self.report_data.timestamp = root.get('timestamp', '')
            self.report_data.verdicts = root.get('verdicts', '')
            
            # 如果根元素没有结束时间，从completion或verdict元素获取
            if not self.report_data.end_time:
                # 先尝试从completion/compend获取
                completion_elem = root.find('completion')
                if completion_elem is not None:
                    compend_elem = completion_elem.find('compend')
                    if compend_elem is not None:
                        self.report_data.end_time = compend_elem.get('endtime', '')
                
                # 如果还没有，从verdict元素获取
                if not self.report_data.end_time:
                    verdict_elem = root.find('verdict')
                    if verdict_elem is not None:
                        self.report_data.end_time = verdict_elem.get('endtime', '') or verdict_elem.get('time', '')
            
            # 如果还是没有结束时间，使用最后一个测试用例的结束时间
            if not self.report_data.end_time:
                # 这个逻辑会在解析完所有测试用例后执行
                pass
            
            # 解析title
            title_elem = root.find('title')
            if title_elem is not None:
                self.report_data.title = title_elem.text or ''
            
            # 解析测试组和测试用例
            self._parse_test_groups(root)
            
            # 解析工程师信息
            self._parse_engineer_info(root)
            
            # 解析测试设置信息
            self._parse_testsetup_info(root)
            
            # 解析硬件信息
            self._parse_hardware_info(root)
            
            # 如果还是没有结束时间，使用最后一个测试用例的结束时间
            if not self.report_data.end_time and self.report_data.test_items:
                # 从后向前查找第一个有结束时间的测试用例
                for test_item in reversed(self.report_data.test_items):
                    if hasattr(test_item, 'end_time') and test_item.end_time:
                        self.report_data.end_time = test_item.end_time
                        break
                    elif hasattr(test_item, 'start_time') and test_item.start_time:
                        self.report_data.end_time = test_item.start_time
                        break
            
            print("XML解析完成，开始生成HTML报告...")
            return self.report_data
            
        except ET.ParseError as e:
            print(f"XML解析错误: {e}")
            return None
        except Exception as e:
            print(f"解析过程中发生错误: {e}")
            return None
    
    def _parse_test_groups(self, root):
        """解析测试组 - 按照XML中的实际顺序递归解析"""
        # 直接从根元素开始递归解析，保持XML中的顺序
        self._parse_elements_recursive(root)
    
    def _parse_elements_recursive(self, parent_elem):
        """递归解析XML元素，保持XML中的顺序"""
        for child in parent_elem:
            if child.tag == 'skipped':
                skipped = SkippedTest()
                skipped.start_time = child.get('starttime', '')
                skipped.timestamp = child.get('timestamp', '')
                
                title_elem = child.find('title')
                if title_elem is not None:
                    skipped.title = title_elem.text or ''
                
                self.report_data.test_items.append(skipped)
            
            elif child.tag == 'testcase':
                test_case = TestCase()
                test_case.start_time = child.get('starttime', '')
                test_case.timestamp = child.get('timestamp', '')
                
                # 查找verdict
                verdict_elem = child.find('verdict')
                if verdict_elem is not None:
                    test_case.verdict = verdict_elem.get('result', '')
                    test_case.end_time = verdict_elem.get('endtime', '')
                    test_case.end_timestamp = verdict_elem.get('endtimestamp', '')
                
                # 查找title和description
                title_elem = child.find('title')
                if title_elem is not None:
                    test_case.title = title_elem.text or ''
                
                desc_elem = child.find('description')
                if desc_elem is not None:
                    test_case.description = desc_elem.text or ''
                
                # 解析测试步骤
                for step_elem in child.findall('teststep'):
                    step = self._parse_test_step(step_elem)
                    test_case.test_steps.append(step)
                
                self.report_data.test_items.append(test_case)
            
            elif child.tag == 'testgroup':
                # 递归处理嵌套的testgroup，保持顺序
                self._parse_elements_recursive(child)
            
            # 忽略其他元素类型（如title, preparation等）
    
    def _parse_test_step(self, step_elem):
        """解析测试步骤"""
        step = TestStep()
        step.timestamp = step_elem.get('timestamp', '')
        step.level = step_elem.get('level', '')
        step.type = step_elem.get('type', '')
        step.ident = step_elem.get('ident', '')
        step.result = step_elem.get('result', '')
        step.content = step_elem.text or ''
        
        # 解析tabularinfo
        tabular_elem = step_elem.find('tabularinfo')
        if tabular_elem is not None:
            step.tabular_info = self._parse_tabular_info(tabular_elem)
        
        return step
    
    def _parse_tabular_info(self, tabular_elem):
        """解析表格信息"""
        tabular = TabularInfo()
        tabular.expand = tabular_elem.get('expand', '')
        
        desc_elem = tabular_elem.find('description')
        if desc_elem is not None:
            tabular.description = desc_elem.text or ''
        
        # 解析表头
        heading_elem = tabular_elem.find('heading')
        if heading_elem is not None:
            for cell_elem in heading_elem.findall('cell'):
                tabular.headings.append(cell_elem.text or '')
        
        # 解析行数据
        for row_elem in tabular_elem.findall('row'):
            row_data = []
            for cell_elem in row_elem.findall('cell'):
                row_data.append(cell_elem.text or '')
            tabular.rows.append(row_data)
        
        return tabular
    
    def _parse_engineer_info(self, root):
        """解析工程师信息"""
        engineer_elem = root.find('engineer')
        if engineer_elem is not None:
            for xinfo_elem in engineer_elem.findall('.//xinfo'):
                name_elem = xinfo_elem.find('name')
                desc_elem = xinfo_elem.find('description')
                
                name = name_elem.text if name_elem is not None else ''
                desc = desc_elem.text if desc_elem is not None else ''
                
                self.report_data.engineer_info[name] = desc
    
    def _parse_testsetup_info(self, root):
        """解析测试设置信息"""
        testsetup_elem = root.find('testsetup')
        if testsetup_elem is not None:
            for xinfo_elem in testsetup_elem.findall('.//xinfo'):
                name_elem = xinfo_elem.find('name')
                desc_elem = xinfo_elem.find('description')
                
                name = name_elem.text if name_elem is not None else ''
                desc = desc_elem.text if desc_elem is not None else ''
                
                self.report_data.testsetup_info[name] = desc
    
    def _parse_hardware_info(self, root):
        """解析硬件信息"""
        hardware_elems = root.findall('hardware')
        for hardware_elem in hardware_elems:
            hardware_name = hardware_elem.get('name', 'Unknown Hardware')
            hardware_category = hardware_elem.get('category', '')
            
            # 创建硬件类别的主键
            hardware_key = f"{hardware_name}_{hardware_category}" if hardware_category else hardware_name
            
            # 初始化硬件信息
            self.report_data.hardware_info[hardware_key] = {
                'name': hardware_name,
                'category': hardware_category,
                'devices': []
            }
            
            # 查找 xinfoset
            xinfoset_elems = hardware_elem.findall('.//xinfoset')
            for xinfoset_elem in xinfoset_elems:
                xinfoset_type = xinfoset_elem.get('type', '')
                
                # 查找所有 xinfoobject
                xinfoobject_elems = xinfoset_elem.findall('xinfoobject')
                for xinfoobject_elem in xinfoobject_elems:
                    xinfoobject_type = xinfoobject_elem.get('type', '')
                    
                    # 解析设备信息
                    device_info = {
                        'type': xinfoobject_type,
                        'properties': {}
                    }
                    
                    # 提取所有 xinfo 属性
                    xinfo_elems = xinfoobject_elem.findall('xinfo')
                    for xinfo_elem in xinfo_elems:
                        key = xinfo_elem.get('key', '')
                        name_elem = xinfo_elem.find('name')
                        desc_elem = xinfo_elem.find('description')
                        
                        name = name_elem.text if name_elem is not None else ''
                        desc = desc_elem.text if desc_elem is not None else ''
                        
                        device_info['properties'][key] = {
                            'name': name,
                            'description': desc
                        }
                    
                    # 添加设备到硬件信息中
                    self.report_data.hardware_info[hardware_key]['devices'].append(device_info)
            
            # 如果没有找到设备信息，但有直接的 xinfo 元素，则按旧方式处理
            if not self.report_data.hardware_info[hardware_key]['devices']:
                direct_xinfo_elems = hardware_elem.findall('.//xinfo')
                if direct_xinfo_elems:
                    device_info = {
                        'type': 'general',
                        'properties': {}
                    }
                    
                    for xinfo_elem in direct_xinfo_elems:
                        key = xinfo_elem.get('key', '')
                        name_elem = xinfo_elem.find('name')
                        desc_elem = xinfo_elem.find('description')
                        
                        name = name_elem.text if name_elem is not None else ''
                        desc = desc_elem.text if desc_elem is not None else ''
                        
                        device_info['properties'][key] = {
                            'name': name,
                            'description': desc
                        }
                    
                    self.report_data.hardware_info[hardware_key]['devices'].append(device_info)

class HTMLReportGenerator:
    """HTML报告生成器"""
    STEPS_PER_PAGE = 200  # 定义每页的步骤数

    def __init__(self, report_data):
        self.report_data = report_data
    
    def generate(self, output_file_path):
        """生成HTML报告"""
        output_path = Path(output_file_path)
        
        # 创建JS文件夹
        js_folder_name = f"{output_path.stem}_js"
        js_folder = output_path.parent / js_folder_name
        js_folder.mkdir(exist_ok=True)
        
        # 主数据文件放在JS文件夹内
        data_file_path = js_folder / f"{output_path.stem}_data.js"

        # 直接将JS数据写入文件，传入JS文件夹名称
        with open(data_file_path, 'w', encoding='utf-8') as f:
            self._write_js_data(f, js_folder_name)

        # 生成独立的步骤数据文件到JS文件夹
        self._write_steps_files(js_folder, output_path.stem)

        # 生成HTML内容，引用JS文件夹中的文件
        html_content = self._generate_html(f"{js_folder_name}/{output_path.stem}_data.js")
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML报告已生成: {output_file_path}")
        print(f"JS文件夹已创建: {js_folder}")
        print(f"主数据文件: {data_file_path}")
        print(f"步骤文件已按需生成在JS文件夹中")

    def _write_js_data(self, f, js_folder_name):
        """将JS数据直接写入文件流，以节省内存 - 按需加载优化版本"""
        
        # 1. 写入基本测试数据（不包含详细步骤）
        f.write("window.testData = [\n")
        
        is_first_item = True
        for i, test_item in enumerate(self.report_data.test_items):
            if not is_first_item:
                f.write(",\n")
            
            item_dict = {}
            if test_item.item_type == "skipped":
                item_dict = {
                    'index': i,
                    'item_type': 'skipped',
                    'title': test_item.title,
                    'start_time': test_item.start_time
                }
            elif test_item.item_type == "testcase":
                item_dict = {
                    'index': i,
                    'item_type': 'testcase',
                    'title': test_item.title,
                    'start_time': test_item.start_time,
                    'end_time': test_item.end_time,
                    'verdict': test_item.verdict,
                    'description': test_item.description,
                    'steps_count': len(test_item.test_steps),
                    'has_steps': len(test_item.test_steps) > 0,
                    'steps_file': f'{js_folder_name}/steps_{i}.js' if len(test_item.test_steps) > 0 else None
                }

            json.dump(item_dict, f, ensure_ascii=False, indent=2)
            is_first_item = False
        
        f.write("\n];\n\n")

        # 2. 步骤缓存和加载管理
        f.write("window.stepsCache = new Map();\n")
        f.write("window.maxCacheSize = 3;\n")
        f.write("window.loadingSteps = new Set();\n\n")  # 跟踪正在加载的测试用例

        # 3. 写入 systemInfo
        f.write("window.systemInfo = ")
        system_info = {
            'engineer': self.report_data.engineer_info,
            'testsetup': self.report_data.testsetup_info,
            'hardware': self.report_data.hardware_info
        }
        json.dump(system_info, f, ensure_ascii=False, indent=2)
        f.write(";")

    def _write_steps_files(self, js_folder, output_stem):
        """为每个有步骤的测试用例生成独立的步骤数据文件"""
        for i, test_item in enumerate(self.report_data.test_items):
            if test_item.item_type == "testcase" and len(test_item.test_steps) > 0:
                steps_file_path = js_folder / f"steps_{i}.js"
                
                with open(steps_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"window.stepsData_{i} = [\n")
                    
                    is_first_step = True
                    for step in test_item.test_steps:
                        if not is_first_step:
                            f.write(",\n")
                        
                        # 压缩步骤数据结构
                        step_dict = {
                            't': step.timestamp,  # timestamp简写
                            'i': step.ident,      # ident简写
                            'r': step.result,     # result简写
                            'c': step.content     # content简写
                        }
                        
                        # 只在有表格信息时才添加
                        if step.tabular_info and (step.tabular_info.headings or step.tabular_info.rows):
                            step_dict['tab'] = {
                                'd': step.tabular_info.description or '',
                                'h': step.tabular_info.headings,
                                'r': step.tabular_info.rows
                            }
                        
                        json.dump(step_dict, f, ensure_ascii=False, separators=(',', ':'))
                        is_first_step = False
                    
                    f.write("\n];\n")
                    f.write(f"\nif (window.onStepsLoaded_{i}) {{")
                    f.write(f"\n    window.onStepsLoaded_{i}(window.stepsData_{i});")
                    f.write(f"\n}}")
                
                print(f"步骤文件已生成: {steps_file_path}")

    def _generate_html(self, data_file_name):
        """生成HTML内容"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - {self.report_data.title}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="main-content">
            <div class="left-panel" id="leftPanel">
                {self._generate_test_list()}
            </div>
            <div class="resizer" id="resizer"></div>
            <div class="right-panel" id="rightPanel">
                {self._generate_system_info()}
            </div>
        </div>
    </div>
    
    <script src="{data_file_name}"></script>
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>
"""
    
    def _get_css(self):
        """获取CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 100%;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 30px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            height: 100vh;
            border-radius: 0;
            overflow: hidden;
        }
        
        .main-content {
            display: flex;
            flex: 1;
            overflow: hidden;
            background: #f8f9fa;
            position: relative;
        }
        
        .left-panel {
            width: 40%;
            min-width: 250px;
            max-width: 70%;
            border-right: 1px solid #dee2e6;
            overflow-y: auto;
            background: #ffffff;
            padding: 1.5rem;
            box-shadow: 2px 0 10px rgba(0,0,0,0.05);
            transition: width 0.1s ease-out;
        }
        
        .resizer {
            width: 6px;
            background: #dee2e6;
            cursor: col-resize;
            position: relative;
            flex-shrink: 0;
            transition: background-color 0.2s ease;
        }
        
        .resizer:hover {
            background: #667eea;
        }
        
        .resizer::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 2px;
            height: 40px;
            background: white;
            border-radius: 1px;
            opacity: 0;
            transition: opacity 0.2s ease;
        }
        
        .resizer:hover::before {
            opacity: 0.8;
        }
        
        .resizer.resizing {
            background: #667eea;
        }
        
        .resizer.resizing::before {
            opacity: 1;
        }
        
        .right-panel {
            flex: 1;
            overflow-y: auto;
            background: white;
            padding: 2rem;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .summary {
            padding: 2rem;
            background: #f8f9fa;
            border-bottom: 3px solid #667eea;
            margin-bottom: 0;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
        }
        
        .summary-card {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid #e9ecef;
        }
        
        .summary-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 25px rgba(0,0,0,0.15);
        }
        
        .summary-card h3 {
            color: #667eea;
            font-size: 1.2rem;
            margin-bottom: 0.75rem;
            font-weight: 600;
        }
        
        .summary-card .value {
            font-size: 2.2rem;
            font-weight: 700;
            color: #333;
            line-height: 1.2;
        }
        
        .filter-container {
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: white;
            border-radius: 8px;
            border: 1px solid #dee2e6;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .filter-buttons {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }
        
        .filter-btn {
            padding: 0.6rem 1.2rem;
            border: 1px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .filter-btn:hover {
            background: #667eea;
            color: white;
            transform: translateY(-1px);
        }
        
        .filter-btn.active {
            background: #667eea;
            color: white;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }
        
        .filter-stats {
            color: #6c757d;
            font-size: 0.9rem;
            font-weight: 500;
            text-align: center;
            padding: 0.5rem;
            background: #f8f9fa;
            border-radius: 6px;
        }
        
        .test-item {
            margin-bottom: 0.75rem;
            cursor: pointer;
            border-radius: 8px;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .test-item:hover {
            transform: translateX(3px);
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }
        
        .test-item.active {
            background: #667eea;
            color: white;
            transform: translateX(5px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .test-item.active .result-badge {
            background: rgba(255,255,255,0.2);
            color: white;
            border-color: rgba(255,255,255,0.3);
        }
        
        .test-case-header {
            padding: 0.8rem 1.2rem;
            background: white;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }
        
        .test-item.active .test-case-header {
            background: #667eea;
            border-color: #667eea;
            color: white;
        }
        
        .test-case-title {
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.3;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .test-case-title .result-badge {
            order: -1;
            flex-shrink: 0;
        }
        
        .test-case-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
            opacity: 0.8;
        }
        
        .result-badge {
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            border: 1px solid transparent;
            transition: all 0.3s ease;
        }
        
        .result-pass {
            background: #d4edda;
            color: #155724;
        }
        
        .result-fail {
            background: #f8d7da;
            color: #721c24;
        }
        
        .result-warn {
            background: #fff3cd;
            color: #856404;
        }
        
        .result-nt {
            background: #e2e3e5;
            color: #383d41;
        }
        
        .result-na {
            background: transparent;
            color: #6c757d;
        }
        
        /* NT用例专用样式 */
        .nt-reason-container {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #dee2e6;
        }

        .nt-reason-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            padding: 0.8rem;
            background: white;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }

        .nt-reason-item:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            border-color: #6c757d;
        }

        .nt-reason-item:last-child {
            margin-bottom: 0;
        }

        .nt-reason-icon {
            font-size: 1.2rem;
            margin-right: 0.8rem;
            min-width: 2rem;
            text-align: center;
        }

        .nt-reason-item span:last-child {
            color: #495057;
            font-weight: 500;
        }
        
        .detail-section {
            margin-bottom: 2rem;
            animation: fadeIn 0.3s ease-in;
        }
        
        .detail-section h3 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
            font-size: 1.3rem;
            font-weight: 600;
        }
        
        .detail-section h2 {
            color: #333;
            font-size: 1.6rem;
            margin-bottom: 1.5rem;
            text-align: center;
            font-weight: 600;
        }
        
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }
        
        .report-header h3 {
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            border: none;
            color: white;
        }
        
        .report-header p {
            margin: 0.3rem 0;
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .summary-stats {
            margin-bottom: 2rem;
            animation: fadeIn 0.3s ease-in;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .stat-card {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid #e9ecef;
        }
        
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 25px rgba(0,0,0,0.15);
        }
        
        .stat-value {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        
        .stat-label {
            font-size: 0.95rem;
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-card.pass {
            border-color: #28a745;
        }
        
        .stat-card.pass .stat-value {
            color: #28a745;
        }
        
        .stat-card.fail {
            border-color: #dc3545;
        }
        
        .stat-card.fail .stat-value {
            color: #dc3545;
        }
        
        .stat-card.warn {
            border-color: #ffc107;
        }
        
        .stat-card.warn .stat-value {
            color: #ffc107;
        }
        
        .stat-card.skip {
            border-color: #6c757d;
        }
        
        .stat-card.skip .stat-value {
            color: #6c757d;
        }
        
        .stat-card.rate {
            border-color: #17a2b8;
        }
        
        .stat-card.rate .stat-value {
            color: #17a2b8;
        }
        
        /* 测试步骤表格样式 */
        .test-steps-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            font-size: 0.9rem;
        }
        
        .test-steps-table th,
        .test-steps-table td {
            padding: 0.5rem;
            text-align: left;
            border: 1px solid #ddd;
            vertical-align: top;
        }
        
        .TableHeadingCell {
            background: #667eea;
            color: white;
            font-weight: bold;
            text-align: center;
        }
        
        .DefineCell {
            background: #f8f9fa;
            font-weight: bold;
            text-align: center;
            min-width: 120px;
        }
        
        .NumberCell {
            background: #ffffff;
            text-align: center;
            font-weight: bold;
            min-width: 80px;
        }
        
        .DefaultCell {
            background: #ffffff;
            padding: 0.5rem;
        }
        
        .PositiveResultCell {
            background: #d4edda;
            color: #155724;
            text-align: center;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .NegativeResultCell {
            background: #f8d7da;
            color: #721c24;
            text-align: center;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .WarningCell {
            background: #fff3cd;
            color: #856404;
            text-align: center;
            font-weight: bold;
        }

        /* --- 新增：步骤控制和分页样式 --- */
        .steps-controls {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 1.5rem;
            padding: 1.5rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }

        .step-search-input {
            padding: 0.75rem 1rem;
            border: 1px solid #dee2e6;
            border-radius: 20px;
            width: 280px;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        .step-search-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .step-filter-btn {
            padding: 0.6rem 1.2rem;
            border: 1px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
            font-weight: 500;
        }
        .step-filter-btn:hover {
            background: #e9edff;
            transform: translateY(-1px);
        }
        .step-filter-btn.active {
            background: #667eea;
            color: white;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }

        .pagination-controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.75rem;
            padding: 1.5rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 2rem;
        }
        .pagination-controls button {
            padding: 0.6rem 1.2rem;
            border: 1px solid #dee2e6;
            background: white;
            color: #495057;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        .pagination-controls button:hover:not(:disabled) {
            background: #667eea;
            color: white;
            border-color: #667eea;
            transform: translateY(-1px);
        }
        .pagination-controls button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .page-jump-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .page-jump-input {
            width: 60px;
            text-align: center;
            padding: 0.6rem;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            font-size: 0.9rem;
        }
        .pagination-controls .page-jump-btn {
            padding: 0.6rem 1rem;
            background: white !important;
            color: #495057 !important;
            border: 1px solid #dee2e6 !important;
            font-weight: 500;
        }
        .pagination-controls .page-jump-btn:hover {
            background: #667eea !important;
            border-color: #667eea !important;
            color: white !important;
            transform: translateY(-1px);
        }

        /* 右键菜单样式 */
        .context-menu {
            position: fixed;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            padding: 0.5rem 0;
            z-index: 10000;
            min-width: 200px;
            font-size: 0.9rem;
            display: none;
        }

        .context-menu-item {
            padding: 0.75rem 1rem;
            cursor: pointer;
            transition: background-color 0.2s;
            color: #333;
            border-bottom: 1px solid #f8f9fa;
        }

        .context-menu-item:last-child {
            border-bottom: none;
        }

        .context-menu-item:hover {
            background: #f8f9fa;
            color: #667eea;
        }

        .context-menu-item.disabled {
            color: #6c757d;
            cursor: not-allowed;
            opacity: 0.6;
        }

        .context-menu-item.disabled:hover {
            background: transparent;
            color: #6c757d;
        }

        /* 步骤上下文弹窗样式 */
        .step-context-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 20000;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }

        .step-context-content {
            background: white;
            border-radius: 12px;
            max-width: 90%;
            max-height: 80%;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
        }

        .step-context-header {
            padding: 1.5rem;
            border-bottom: 1px solid #dee2e6;
            background: #f8f9fa;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .step-context-header h3 {
            margin: 0;
            color: #333;
            font-size: 1.2rem;
        }

        .step-context-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #6c757d;
            padding: 0.25rem;
            border-radius: 4px;
            transition: all 0.2s;
        }

        .step-context-close:hover {
            background: #dee2e6;
            color: #333;
        }

        .step-context-body {
            padding: 1.5rem;
            overflow-y: auto;
            flex: 1;
        }

        .step-context-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }

        .step-context-table th,
        .step-context-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }

        .step-context-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
            position: sticky;
            top: 0;
            z-index: 1;
        }

        .step-context-table tr.current-step {
            background: #e6f2ff;
            border: 2px solid #667eea;
        }

        .step-context-table tr.current-step td {
            font-weight: 600;
            color: #667eea;
        }

        .step-context-table .step-index {
            width: 60px;
            text-align: center;
            font-weight: 600;
            color: #6c757d;
        }

        .step-context-table .step-timestamp {
            width: 140px;
            font-family: monospace;
            font-size: 0.8rem;
        }

        .step-context-table .step-ident {
            width: 120px;
            font-family: monospace;
            font-size: 0.8rem;
        }

        .step-context-table .step-result {
            width: 80px;
            text-align: center;
        }

        .step-context-table .step-content {
            max-width: 400px;
            word-wrap: break-word;
        }

        /* 弹窗中的表格样式 - 与主页面保持一致 */
        .step-context-modal .InfoTableExpand {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5rem;
            font-size: 0.8rem;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            overflow: hidden;
        }

        .step-context-modal .InfoTableExpand caption {
            background: #e9ecef;
            padding: 0.5rem;
            font-weight: 600;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
            color: #495057;
        }

        .step-context-modal .InfoTableExpand th,
        .step-context-modal .InfoTableExpand td {
            padding: 0.4rem 0.6rem;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }

        .step-context-modal .InfoTableExpand th {
            background: #e9ecef;
            font-weight: 600;
            color: #495057;
        }

        .step-context-modal .InfoTableExpand tbody tr:hover {
            background: #f1f3f4;
        }

        .step-context-modal .InfoTableExpand tbody tr:last-child td {
            border-bottom: none;
        }
        }
        /* --- 样式结束 --- */

        /* 嵌套表格样式 */
        .NoMarginBottom {
            margin-bottom: 0;
            width: 100%;
            border-collapse: collapse;
        }
        
        .InfoTableExpand {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5rem;
            border: 1px solid #ccc;
        }
        
        .InfoTableExpand td {
            padding: 0.3rem 0.5rem;
            border: 1px solid #ddd;
            font-size: 0.85rem;
        }
        
        .Undecorated {
            text-decoration: none;
            color: #667eea;
            font-weight: bold;
        }
        
        .Undecorated:hover {
            color: #5a6fd8;
        }

        /* 加载指示器样式 */
        .loading-indicator {
            text-align: center;
            padding: 3rem;
            color: #6c757d;
            font-style: italic;
        }

        .loading-indicator p {
            margin: 0;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 12px;
            border: 2px dashed #dee2e6;
            font-size: 1.1rem;
            color: #495057;
        }

        /* 进度条样式 */
        .progress-container {
            width: 100%;
            max-width: 450px;
            margin: 1.5rem auto;
            background-color: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border: 1px solid #dee2e6;
        }

        .progress-bar {
            height: 12px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            transition: width 0.4s ease;
            width: 0%;
            box-shadow: 0 2px 5px rgba(102, 126, 234, 0.3);
        }

        .progress-text {
            margin-top: 0.75rem;
            font-size: 1rem;
            color: #495057;
            font-weight: 500;
        }

        .loading-spinner {
            display: inline-block;
            width: 24px;
            height: 24px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 0.75rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* NT状态（跳过测试）页面美化样式 */
        .skipped-header {
            display: flex;
            align-items: center;
            padding: 2rem;
            background: linear-gradient(135deg, #ffc107 0%, #ff8c00 100%);
            color: white;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(255, 193, 7, 0.3);
        }

        .skipped-icon {
            font-size: 4rem;
            margin-right: 1.5rem;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        .skipped-info h2 {
            margin: 0 0 0.5rem 0;
            font-size: 1.8rem;
            border: none;
            color: white;
        }

        .skipped-badge {
            background: rgba(255, 255, 255, 0.2);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
            display: inline-block;
        }

        .skipped-info-card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #ffc107;
        }

        .info-row {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
        }

        .info-item {
            display: flex;
            align-items: center;
            flex: 1;
            min-width: 200px;
        }

        .info-icon {
            font-size: 2rem;
            margin-right: 1rem;
            color: #ffc107;
        }

        .info-content {
            flex: 1;
        }

        .info-label {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.25rem;
        }

        .info-value {
            font-size: 1.1rem;
            font-weight: bold;
            color: #333;
        }

        .skipped-explanation {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid #e9ecef;
        }

        .explanation-header {
            display: flex;
            align-items: center;
            margin-bottom: 1.5rem;
        }

        .explanation-icon {
            font-size: 1.5rem;
            margin-right: 0.8rem;
            color: #17a2b8;
        }

        .explanation-header h3 {
            margin: 0;
            color: #333;
            border: none;
        }

        .explanation-content {
            color: #555;
            line-height: 1.6;
        }

        .reason-item {
            display: flex;
            align-items: center;
            margin-bottom: 0.8rem;
        }

        .reason-bullet {
            margin-right: 0.8rem;
            color: #ffc107;
            font-weight: bold;
        }

        .reason-list {
            margin-left: 1rem;
            margin-top: 1rem;
        }

        .reason-icon {
            margin-right: 0.8rem;
            font-size: 1.1rem;
            color: #667eea;
        }

        /* 工程师信息和测试设置样式 */
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .info-item {
            background: white;
            padding: 1.2rem;
            border-radius: 8px;
            border: 1px solid #dee2e6;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            min-height: 80px;
        }

        .info-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border-color: #667eea;
        }

        .info-label {
            font-weight: bold;
            color: #495057;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            
            /* 处理标题溢出 */
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 100%;
            cursor: help;
        }

        .info-label:before {
            content: "📋";
            margin-right: 0.5rem;
            font-size: 1rem;
        }

        .info-value {
            color: #6c757d;
            font-size: 1rem;
            line-height: 1.5;
            flex: 1;
            
            /* 处理超长文本溢出 */
            word-wrap: break-word;
            word-break: break-all;
            overflow-wrap: break-word;
            hyphens: auto;
            
            /* 如果文本太长，显示省略号 */
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            position: relative;
        }

        .info-value:hover {
            /* 悬停时显示完整文本 */
            -webkit-line-clamp: unset;
            overflow: visible;
            background: #f8f9fa;
            padding: 0.5rem;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            z-index: 10;
            position: relative;
        }

        /* 为长文本添加渐变遮罩效果 */
        .info-value:not(:hover):after {
            content: "";
            position: absolute;
            bottom: 0;
            left: 0;
            height: 1.5em;
            width: 100%;
            background: linear-gradient(transparent, white);
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .info-value:not(:hover).text-overflow:after {
            opacity: 1;
        }

        /* 特殊样式用于区分不同类型的信息 */
        .detail-section:nth-child(2) .info-item {
            border-left: 4px solid #28a745;
        }

        .detail-section:nth-child(2) .info-label:before {
            content: "";
        }

        .detail-section:nth-child(3) .info-item {
            border-left: 4px solid #17a2b8;
        }

        .detail-section:nth-child(3) .info-label:before {
            content: "";
        }

        /* 硬件信息显示样式 */
        .hardware-category {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #28a745;
        }

        .hardware-category h4 {
            margin: 0 0 0.5rem 0;
            color: #28a745;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
        }

        .hardware-category-desc {
            color: #666;
            font-style: italic;
            margin-bottom: 1.5rem;
        }

        .hardware-device {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid #e9ecef;
        }

        .hardware-device h5 {
            margin: 0 0 1rem 0;
            color: #495057;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
        }

        .device-properties {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 0.8rem;
        }

        .property-item {
            background: white;
            padding: 0.8rem;
            border-radius: 6px;
            border: 1px solid #dee2e6;
            display: flex;
            align-items: center;
        }

        .property-label {
            font-weight: bold;
            color: #495057;
            margin-right: 0.8rem;
            min-width: 120px;
        }

        .property-value {
            color: #6c757d;
            flex: 1;
            word-break: break-all;
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            .skipped-header {
                flex-direction: column;
                text-align: center;
            }

            .skipped-icon {
                margin-right: 0;
                margin-bottom: 1rem;
            }

            .info-row {
                flex-direction: column;
                gap: 1rem;
            }

            /* 移动端信息网格优化 */
            .info-grid {
                grid-template-columns: 1fr;
                gap: 0.8rem;
            }

            .info-item {
                padding: 1rem;
                min-height: 60px;
            }

            .info-label {
                font-size: 0.8rem;
                /* 移动端更宽松的截断处理 */
                max-width: calc(100% - 2rem);
            }

            .info-value {
                font-size: 0.9rem;
                -webkit-line-clamp: 2;
            }

            .device-properties {
                grid-template-columns: 1fr;
            }

            .property-item {
                flex-direction: column;
                align-items: flex-start;
            }

            .property-label {
                min-width: auto;
                margin-bottom: 0.3rem;
            }
        }

        @media (max-width: 480px) {
            .info-grid {
                gap: 0.5rem;
            }

            .info-item {
                padding: 0.8rem;
            }

            .info-label {
                font-size: 0.75rem;
                /* 小屏幕端更严格的截断处理 */
                max-width: calc(100% - 1.5rem);
            }

            .info-value {
                font-size: 0.85rem;
            }
        }
        
        /* 全局样式统一 - 确保所有区域风格一致 */
        
        /* 统一卡片样式 */
        .card, .info-card, .hardware-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            border: 1px solid #e9ecef;
        }
        
        .card:hover, .info-card:hover, .hardware-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }
        
        /* 统一按钮样式 */
        .btn, .filter-btn, .step-filter-btn {
            padding: 0.5rem 1rem;
            border: 1px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9rem;
            font-weight: 500;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        
        .btn:hover, .filter-btn:hover, .step-filter-btn:hover {
            background: #667eea;
            color: white;
            transform: translateY(-1px);
        }
        
        .btn.active, .filter-btn.active, .step-filter-btn.active {
            background: #667eea;
            color: white;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }
        
        /* 统一表格样式 */
        .table, .test-steps-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .table th, .table td,
        .test-steps-table th, .test-steps-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
            vertical-align: top;
        }
        
        .table th, .test-steps-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }
        
        .table tr:hover, .test-steps-table tr:hover {
            background: #f8f9fa;
        }
        
        /* 统一输入框样式 */
        .input, .step-search-input, .page-jump-input {
            padding: 0.5rem 0.75rem;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            font-size: 0.9rem;
            transition: all 0.3s;
            background: white;
        }
        
        .input:focus, .step-search-input:focus, .page-jump-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* 统一标题样式 */
        .section-title {
            color: #495057;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #667eea;
        }
        
        /* 统一状态颜色 */
        .status-success, .result-pass {
            color: #28a745;
            background: #d4edda;
        }
        
        .status-danger, .result-fail {
            color: #dc3545;
            background: #f8d7da;
        }
        
        .status-warning, .result-warn {
            color: #ffc107;
            background: #fff3cd;
        }
        
        .status-info, .result-na {
            color: #6c757d;
            background: #f8f9fa;
        }
        
        /* 统一间距 */
        .mb-1 { margin-bottom: 0.25rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mb-3 { margin-bottom: 1rem; }
        .mb-4 { margin-bottom: 1.5rem; }
        .mb-5 { margin-bottom: 3rem; }
        
        .mt-1 { margin-top: 0.25rem; }
        .mt-2 { margin-top: 0.5rem; }
        .mt-3 { margin-top: 1rem; }
        .mt-4 { margin-top: 1.5rem; }
        .mt-5 { margin-top: 3rem; }
        
        .p-1 { padding: 0.25rem; }
        .p-2 { padding: 0.5rem; }
        .p-3 { padding: 1rem; }
        .p-4 { padding: 1.5rem; }
        .p-5 { padding: 3rem; }
        
        /* 统一文本样式 */
        .text-muted { color: #6c757d; }
        .text-primary { color: #667eea; }
        .text-success { color: #28a745; }
        .text-danger { color: #dc3545; }
        .text-warning { color: #ffc107; }
        .text-info { color: #17a2b8; }
        
        .font-weight-bold { font-weight: 600; }
        .font-weight-normal { font-weight: 400; }
        
        /* 统一边框样式 */
        .border { border: 1px solid #dee2e6; }
        .border-top { border-top: 1px solid #dee2e6; }
        .border-bottom { border-bottom: 1px solid #dee2e6; }
        .border-left { border-left: 1px solid #dee2e6; }
        .border-right { border-right: 1px solid #dee2e6; }
        
        .rounded { border-radius: 6px; }
        .rounded-lg { border-radius: 8px; }
        .rounded-xl { border-radius: 12px; }
        .rounded-full { border-radius: 50%; }
        
        /* 统一阴影样式 */
        .shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .shadow { box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .shadow-lg { box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
        
        /* 统一动画 */
        .fade-in {
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .slide-up {
            animation: slideUp 0.3s ease-out;
        }
        
        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        /* NT用例专用样式 */
        .nt-reason-container {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #dee2e6;
        }

        .nt-reason-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            padding: 0.8rem;
            background: white;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        }

        .nt-reason-item:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            border-color: #6c757d;
        }

        .nt-reason-item:last-child {
            margin-bottom: 0;
        }

        .nt-reason-icon {
            font-size: 1.2rem;
            margin-right: 0.8rem;
            min-width: 2rem;
            text-align: center;
        }

        .nt-reason-item span:last-child {
            color: #495057;
            font-weight: 500;
        }

        /* 主布局响应式优化 */
        @media (max-width: 768px) {
            .main-content {
                flex-direction: column;
            }
            
            .left-panel, .right-panel {
                width: 100%;
                max-height: none;
            }
            
            .summary-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
            
            .filter-buttons {
                justify-content: center;
            }
            
            .filter-btn {
                padding: 0.4rem 0.8rem;
                font-size: 0.8rem;
            }
            
            .test-case-title {
                font-size: 0.9rem;
            }
            
            .test-case-meta {
                font-size: 0.7rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .header p {
                font-size: 1rem;
            }
        }
        
        @media (max-width: 480px) {
            .header h1 {
                font-size: 1.5rem;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .stat-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        """
    
    def _generate_header(self):
        """生成头部"""
        return f"""
        <div class="header">
            <h1>🔬 {self.report_data.title or '测试报告'}</h1>
            <p>开始时间: {self.report_data.start_time} | 测试判决: {self.report_data.verdicts}</p>
        </div>
        """
    
    def _generate_summary(self):
        """生成摘要"""
        total_tests = len([item for item in self.report_data.test_items if item.item_type == 'testcase'])
        passed_tests = len([item for item in self.report_data.test_items if item.item_type == 'testcase' and item.verdict == 'pass'])
        failed_tests = len([item for item in self.report_data.test_items if item.item_type == 'testcase' and item.verdict == 'fail'])
        warn_tests = len([item for item in self.report_data.test_items if item.item_type == 'testcase' and item.verdict == 'warn'])
        skipped_tests = len([item for item in self.report_data.test_items if item.item_type == 'skipped'])
        
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return f"""
        <div class="summary">
            <div class="summary-grid">
                <div class="summary-card" onclick="showSystemInfo()">
                    <h3>总测试数</h3>
                    <div class="value">{total_tests}</div>
                </div>
                <div class="summary-card" onclick="filterTests('pass')">
                    <h3>通过 (PASS)</h3>
                    <div class="value" style="color: #28a745;">{passed_tests}</div>
                </div>
                <div class="summary-card" onclick="filterTests('fail')">
                    <h3>失败 (NG)</h3>
                    <div class="value" style="color: #dc3545;">{failed_tests}</div>
                </div>
                <div class="summary-card" onclick="filterTests('warn')">
                    <h3>警告 (WARN)</h3>
                    <div class="value" style="color: #ffc107;">{warn_tests}</div>
                </div>
                <div class="summary-card" onclick="filterTests('skipped')">
                    <h3>跳过 (NT)</h3>
                    <div class="value" style="color: #6c757d;">{skipped_tests}</div>
                </div>
                <div class="summary-card" onclick="showSystemInfo()">
                    <h3>通过率</h3>
                    <div class="value" style="color: #17a2b8;">{pass_rate:.1f}%</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_test_list(self):
        """生成测试用例列表"""
        filter_html = """
        <div class="filter-container">
            <div class="filter-buttons">
                <button class="filter-btn active" data-filter="all" onclick="filterTests('all')">全部</button>
                <button class="filter-btn" data-filter="pass" onclick="filterTests('pass')">PASS</button>
                <button class="filter-btn" data-filter="fail" onclick="filterTests('fail')">NG</button>
                <button class="filter-btn" data-filter="skipped" onclick="filterTests('skipped')">NT</button>
            </div>
            <div class="filter-stats">显示 0 项</div>
        </div>
        """
        
        test_items_html = ""
        
        for i, test_item in enumerate(self.report_data.test_items):
            if test_item.item_type == "skipped":
                test_items_html += f"""
                <div class="test-item" data-type="skipped" data-result="skipped" onclick="showTestCaseDetails(this, {i})">
                    <div class="test-case-header">
                        <div class="test-case-title">
                            <span class="result-badge result-nt">NT</span>
                            {test_item.title}
                        </div>
                    </div>
                </div>
                """
            
            elif test_item.item_type == "testcase":
                result_class = f"result-{test_item.verdict}" if test_item.verdict else "result-na"
                result_text = test_item.verdict or 'N/A';
                
                test_items_html += f"""
                <div class="test-item" data-type="testcase" data-result="{test_item.verdict or ''}" onclick="showTestCaseDetails(this, {i})">
                    <div class="test-case-header">
                        <div class="test-case-title">
                            <span class="result-badge {result_class}">{result_text.upper()}</span>
                            {test_item.title or f'测试用例 {i+1}'}
                        </div>
                    </div>
                </div>
                """
        
        return f"""
        {filter_html}
        <div class="test-items-container">
            {test_items_html}
        </div>
        """
    
    def _generate_system_info(self):
        """生成系统信息（默认右侧面板内容）"""
        # 计算测试统计信息
        total_tests = len([item for item in self.report_data.test_items if item.item_type == 'testcase'])
        passed_tests = len([item for item in self.report_data.test_items if item.item_type == 'testcase' and item.verdict == 'pass'])
        failed_tests = len([item for item in self.report_data.test_items if item.item_type == 'testcase' and item.verdict == 'fail'])
        warn_tests = len([item for item in self.report_data.test_items if item.item_type == 'testcase' and item.verdict == 'warn'])
        skipped_tests = len([item for item in self.report_data.test_items if item.item_type == 'skipped'])
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        engineer_html = ""
        for key, value in self.report_data.engineer_info.items():
            # 处理超长文本，检测是否需要截断提示
            display_value = str(value) if value else "未指定"
            is_long_text = len(display_value) > 100
            css_class = "text-overflow" if is_long_text else ""
            
            engineer_html += f"""
                <div class="info-item">
                    <div class="info-label">{key}</div>
                    <div class="info-value {css_class}" title="{display_value}">{display_value}</div>
                </div>
            """
        
        testsetup_html = ""
        for key, value in self.report_data.testsetup_info.items():
            # 处理超长文本，检测是否需要截断提示
            display_value = str(value) if value else "未指定"
            is_long_text = len(display_value) > 100
            css_class = "text-overflow" if is_long_text else ""
            
            testsetup_html += f"""
                <div class="info-item">
                    <div class="info-label">{key}</div>
                    <div class="info-value {css_class}" title="{display_value}">{display_value}</div>
                </div>
            """
        
        hardware_html = ""
        for key, hardware in self.report_data.hardware_info.items():
            hardware_html += f"""
                <div class="hardware-category">
                    <h4>{hardware['name']}</h4>
                    <p class="hardware-category-desc">类别: {hardware['category'] or '未指定'}</p>
            """
            
            # 显示每个设备的信息
            for i, device in enumerate(hardware['devices']):
                device_title = f"设备 {i + 1}" if device['type'] == 'general' else f"{device['type'].title()} 设备 {i + 1}"
                hardware_html += f"""
                    <div class="hardware-device">
                        <h5>{device_title}</h5>
                        <div class="device-properties">
                """
                
                # 显示设备属性
                for prop_key, prop_info in device['properties'].items():
                    hardware_html += f"""
                            <div class="property-item">
                                <span class="property-label">{prop_info['name']}:</span>
                                <span class="property-value">{prop_info['description']}</span>
                            </div>
                    """
                
                hardware_html += """
                        </div>
                    </div>
                """
            
            hardware_html += """
                </div>
            """
        
        return f"""
        <div class="detail-section">
            <h2>测试报告概览</h2>
            <div class="report-header">
                <h3>{self.report_data.title or '测试报告'}</h3>
                <p><strong>开始时间:</strong> {self.report_data.start_time}</p>
                <p><strong>结束时间:</strong> {self.report_data.end_time}</p>
            </div>
            
            <div class="summary-stats">
                <div class="stat-grid">
                    <div class="stat-card" onclick="filterTests('all')">
                        <div class="stat-value">{total_tests}</div>
                        <div class="stat-label">总测试数</div>
                    </div>
                    <div class="stat-card pass" onclick="filterTests('pass')">
                        <div class="stat-value">{passed_tests}</div>
                        <div class="stat-label">通过 (PASS)</div>
                    </div>
                    <div class="stat-card fail" onclick="filterTests('fail')">
                        <div class="stat-value">{failed_tests}</div>
                        <div class="stat-label">失败 (NG)</div>
                    </div>
                    <div class="stat-card skip" onclick="filterTests('skipped')">
                        <div class="stat-value">{skipped_tests}</div>
                        <div class="stat-label">跳过 (NT)</div>
                    </div>
                    <div class="stat-card rate" onclick="showSystemInfo()">
                        <div class="stat-value">{pass_rate:.1f}%</div>
                        <div class="stat-label">通过率</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>工程师信息</h3>
            <div class="info-grid">
                {engineer_html}
            </div>
        </div>
        <div class="detail-section">
            <h3>测试设置</h3>
            <div class="info-grid">
                {testsetup_html}
            </div>
        </div>
        <div class="detail-section">
            <h3>硬件信息</h3>
            <div class="hardware-info">
                {hardware_html}
            </div>
        </div>
        """
    
    def _get_javascript(self):
        """获取JavaScript代码"""
        return """
        // 面板拖动调整功能
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;
        const MIN_PANEL_WIDTH = 250; // 最小宽度 250px
        const MAX_PANEL_WIDTH_PERCENT = 70; // 最大宽度占比 70%
        
        document.addEventListener('DOMContentLoaded', function() {
            initializePanelResizer();
            filterTests('all');
        });
        
        function initializePanelResizer() {
            const resizer = document.getElementById('resizer');
            const leftPanel = document.getElementById('leftPanel');
            const mainContent = document.querySelector('.main-content');
            
            if (!resizer || !leftPanel || !mainContent) return;
            
            resizer.addEventListener('mousedown', initResize);
            
            function initResize(e) {
                isResizing = true;
                startX = e.clientX;
                startWidth = parseInt(window.getComputedStyle(leftPanel).width, 10);
                
                resizer.classList.add('resizing');
                document.body.style.cursor = 'col-resize';
                document.body.style.userSelect = 'none';
                
                document.addEventListener('mousemove', doResize);
                document.addEventListener('mouseup', stopResize);
                
                e.preventDefault();
            }
            
            function doResize(e) {
                if (!isResizing) return;
                
                const deltaX = e.clientX - startX;
                const newWidth = startWidth + deltaX;
                const mainContentWidth = mainContent.clientWidth;
                const maxWidth = (mainContentWidth * MAX_PANEL_WIDTH_PERCENT) / 100;
                
                // 限制宽度在最小值和最大值之间
                const clampedWidth = Math.max(MIN_PANEL_WIDTH, Math.min(newWidth, maxWidth));
                const widthPercent = (clampedWidth / mainContentWidth) * 100;
                
                leftPanel.style.width = widthPercent + '%';
                
                // 储存用户偏好到localStorage
                try {
                    localStorage.setItem('testReportLeftPanelWidth', widthPercent.toString());
                } catch (e) {
                    // 忽略localStorage错误
                }
            }
            
            function stopResize() {
                isResizing = false;
                resizer.classList.remove('resizing');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                
                document.removeEventListener('mousemove', doResize);
                document.removeEventListener('mouseup', stopResize);
            }
            
            // 加载用户之前保存的宽度偏好
            try {
                const savedWidth = localStorage.getItem('testReportLeftPanelWidth');
                if (savedWidth) {
                    const width = parseFloat(savedWidth);
                    if (width >= (MIN_PANEL_WIDTH / mainContent.clientWidth) * 100 && 
                        width <= MAX_PANEL_WIDTH_PERCENT) {
                        leftPanel.style.width = width + '%';
                    }
                }
            } catch (e) {
                // 忽略localStorage错误
            }
            
            // 窗口大小变化时重新验证面板宽度
            window.addEventListener('resize', function() {
                const currentWidth = leftPanel.clientWidth;
                const mainContentWidth = mainContent.clientWidth;
                const currentPercent = (currentWidth / mainContentWidth) * 100;
                const maxPercent = MAX_PANEL_WIDTH_PERCENT;
                
                if (currentPercent > maxPercent) {
                    leftPanel.style.width = maxPercent + '%';
                }
                
                const minPercent = (MIN_PANEL_WIDTH / mainContentWidth) * 100;
                if (currentPercent < minPercent) {
                    leftPanel.style.width = minPercent + '%';
                }
            });
        }

        function escapeHTML(str) {
            if (typeof str !== 'string') {
                return str;
            }
            return str.replace(/[&<>"']/g, function(match) {
                return {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#39;'
                }[match];
            });
        }

        function showTestCaseDetails(element, index) {
            // 移除之前的激活状态
            const activeItem = document.querySelector('.test-item.active');
            if (activeItem) {
                activeItem.classList.remove('active');
            }
            element.classList.add('active');
            
            // 在当前测试项上显示加载状态
            const originalContent = element.innerHTML;
            const loadingIndicator = document.createElement('div');
            loadingIndicator.style.cssText = 'position: absolute; top: 0; right: 0; background: rgba(102, 126, 234, 0.8); color: white; padding: 0.2rem 0.5rem; border-radius: 0 0 0 8px; font-size: 0.8rem;';
            loadingIndicator.textContent = '加载中...';
            element.style.position = 'relative';
            element.appendChild(loadingIndicator);
            
            const testItem = window.testData[index];
            
            // 异步显示详情，避免阻塞UI
            setTimeout(() => {
                showDetails(testItem).finally(() => {
                    // 移除加载指示器
                    if (element.contains(loadingIndicator)) {
                        element.removeChild(loadingIndicator);
                    }
                });
            }, 10);
        }

        function showDetails(item) {
            return new Promise((resolve, reject) => {
                const rightPanel = document.getElementById('rightPanel');
                rightPanel.innerHTML = ''; // Clear previous content

                if (item.item_type === 'skipped') {
                    // 使用与普通测试用例相同的风格显示NT用例
                    const headerDiv = document.createElement('div');
                    headerDiv.className = 'report-header';
                    headerDiv.innerHTML = `
                        <h3>${escapeHTML(item.title)}</h3>
                        <p><strong>开始时间:</strong> ${item.start_time} | <strong>结束时间:</strong> --</p>
                        <p><strong>最终判决:</strong> <span class="result-badge result-nt">NT (跳过)</span></p>
                        <p><strong>测试状态:</strong> 未执行</p>
                    `;
                    rightPanel.appendChild(headerDiv);

                    const descriptionSection = document.createElement('div');
                    descriptionSection.className = 'detail-section';
                    descriptionSection.innerHTML = `
                        <h3>测试描述</h3>
                        <p>此测试用例被跳过，未执行具体的测试步骤。</p>
                    `;
                    rightPanel.appendChild(descriptionSection);

                    // 添加跳过原因说明
                    const reasonSection = document.createElement('div');
                    reasonSection.className = 'detail-section';
                    reasonSection.innerHTML = `
                        <h3>跳过原因</h3>
                        <div class="nt-reason-container">
                            <div class="nt-reason-item">
                                <span>1、测试环境不满足执行条件</span>
                            </div>
                            <div class="nt-reason-item">
                                <span>2、依赖的前置条件未满足</span>
                            </div>
                            <div class="nt-reason-item">
                                <span>3、测试配置中明确标记为跳过</span>
                            </div>
                            <div class="nt-reason-item">
                                <span>4、当前测试轮次不需要执行</span>
                            </div>
                        </div>
                    `;
                    rightPanel.appendChild(reasonSection);

                    resolve();
                    return;
                }

                // For testcase
                const headerDiv = document.createElement('div');
                headerDiv.className = 'report-header';
                headerDiv.innerHTML = `
                    <h3>${escapeHTML(item.title)}</h3>
                    <p><strong>开始时间:</strong> ${item.start_time} | <strong>结束时间:</strong> ${item.end_time}</p>
                    <p><strong>最终判决:</strong> <span class="result-badge result-${item.verdict}">${item.verdict.toUpperCase()}</span></p>
                    <p><strong>步骤数量:</strong> ${item.steps_count || 0}</p>
                `;
                rightPanel.appendChild(headerDiv);

                const descriptionSection = document.createElement('div');
                descriptionSection.className = 'detail-section';
                descriptionSection.innerHTML = `
                    <h3>测试描述</h3>
                    <p>${escapeHTML(item.description)}</p>
                `;
                rightPanel.appendChild(descriptionSection);

                // 只有当有步骤时才显示步骤区域
                if (!item.has_steps) {
                    const noStepsDiv = document.createElement('div');
                    noStepsDiv.className = 'detail-section';
                    noStepsDiv.innerHTML = '<h3>测试步骤</h3><p>此测试用例没有详细步骤数据。</p>';
                    rightPanel.appendChild(noStepsDiv);
                    resolve();
                    return;
                }

                const stepsSection = document.createElement('div');
                stepsSection.className = 'detail-section';
                stepsSection.innerHTML = '<h3>测试步骤</h3>';
                
                // 显示加载指示器和进度条
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'loading-indicator';
                loadingDiv.innerHTML = `
                    <p><span class="loading-spinner"></span>正在加载测试步骤...</p>
                    <div class="progress-container">
                        <div class="progress-bar" id="loadingProgress"></div>
                    </div>
                    <div class="progress-text" id="progressText">准备加载...</div>
                `;
                stepsSection.appendChild(loadingDiv);
                rightPanel.appendChild(stepsSection);

                // 延迟加载步骤数据
                loadTestStepsAsync(item.index).then(steps => {
                    // 移除加载指示器
                    loadingDiv.remove();
                    
                    // 添加控制区域
                    const controlsContainer = document.createElement('div');
                    controlsContainer.className = 'steps-controls';
                    controlsContainer.innerHTML = `
                        <input type="text" id="stepSearchInput" placeholder="搜索步骤内容、标识..." class="step-search-input">
                        <button class="step-filter-btn active" data-filter="all">全部</button>
                        <button class="step-filter-btn" data-filter="pass">PASS</button>
                        <button class="step-filter-btn" data-filter="fail">NG</button>
                        <button class="step-filter-btn" data-filter="warn">WARN</button>
                    `;
                    stepsSection.appendChild(controlsContainer);

                    // 分页控件容器
                    const paginationContainer = document.createElement('div');
                    paginationContainer.className = 'pagination-controls';
                    paginationContainer.style.marginBottom = '1rem';
                    paginationContainer.style.textAlign = 'center';
                    stepsSection.appendChild(paginationContainer);

                    const stepsTable = document.createElement('table');
                    stepsTable.className = 'test-steps-table';
                    stepsTable.innerHTML = `
                        <thead>
                            <tr>
                                <th class="TableHeadingCell">时间戳</th>
                                <th class="TableHeadingCell">标识</th>
                                <th class="TableHeadingCell">结果</th>
                                <th class="TableHeadingCell">内容</th>
                            </tr>
                        </thead>
                    `;
                    
                    const tbody = document.createElement('tbody');
                    stepsTable.appendChild(tbody);
                    stepsSection.appendChild(stepsTable);

                    // 初始化筛选和分页逻辑
                    initializeStepsControls(steps, tbody, paginationContainer);
                    resolve();
                }).catch(error => {
                    loadingDiv.innerHTML = '<p style="color: red;">加载测试步骤失败</p>';
                    console.error('Failed to load test steps:', error);
                    reject(error);
                });
            });
        }

        // 异步加载测试步骤数据
        function loadTestStepsAsync(testIndex) {
            return new Promise((resolve, reject) => {
                // 检查缓存
                if (window.stepsCache.has(testIndex)) {
                    updateProgress(100, '从缓存加载完成');
                    setTimeout(() => resolve(window.stepsCache.get(testIndex)), 100);
                    return;
                }

                // 检查是否正在加载
                if (window.loadingSteps.has(testIndex)) {
                    // 等待正在进行的加载完成
                    const checkInterval = setInterval(() => {
                        if (!window.loadingSteps.has(testIndex)) {
                            clearInterval(checkInterval);
                            if (window.stepsCache.has(testIndex)) {
                                resolve(window.stepsCache.get(testIndex));
                            } else {
                                reject(new Error('Loading failed'));
                            }
                        }
                    }, 100);
                    return;
                }

                // 开始加载
                window.loadingSteps.add(testIndex);
                updateProgress(10, '开始下载步骤数据...');

                const testItem = window.testData[testIndex];
                if (!testItem || !testItem.steps_file) {
                    window.loadingSteps.delete(testIndex);
                    updateProgress(100, '没有步骤数据');
                    resolve([]);
                    return;
                }

                // 动态加载步骤文件
                const script = document.createElement('script');
                script.src = testItem.steps_file;
                
                console.log('Loading steps file:', testItem.steps_file);
                
                // 设置超时机制
                const timeoutId = setTimeout(() => {
                    window.loadingSteps.delete(testIndex);
                    delete window[`onStepsLoaded_${testIndex}`];
                    document.head.removeChild(script);
                    updateProgress(0, '加载超时');
                    console.error('Loading timeout for:', testItem.steps_file);
                    reject(new Error('Loading timeout'));
                }, 30000); // 30秒超时
                
                // 设置加载完成回调
                window[`onStepsLoaded_${testIndex}`] = function(steps) {
                    clearTimeout(timeoutId);
                    updateProgress(80, '处理步骤数据...');
                    
                    setTimeout(() => {
                        try {
                            // 转换压缩格式回正常格式
                            const normalizedSteps = steps.map(step => ({
                                timestamp: step.t,
                                ident: step.i,
                                result: step.r,
                                content: step.c,
                                tabular_info: step.tab ? {
                                    description: step.tab.d,
                                    headings: step.tab.h,
                                    rows: step.tab.r
                                } : null
                            }));

                            // 管理缓存大小
                            if (window.stepsCache.size >= window.maxCacheSize) {
                                const firstKey = window.stepsCache.keys().next().value;
                                window.stepsCache.delete(firstKey);
                            }

                            // 缓存数据
                            window.stepsCache.set(testIndex, normalizedSteps);
                            window.loadingSteps.delete(testIndex);
                            
                            updateProgress(100, '加载完成');
                            
                            // 清理回调函数
                            delete window[`onStepsLoaded_${testIndex}`];
                            delete window[`stepsData_${testIndex}`];
                            
                            resolve(normalizedSteps);
                        } catch (error) {
                            window.loadingSteps.delete(testIndex);
                            reject(error);
                        }
                    }, 200); // 给用户一点时间看到进度条到100%
                };
                
                script.onload = function() {
                    updateProgress(60, '步骤文件加载完成...');
                };
                
                script.onerror = function(event) {
                    clearTimeout(timeoutId);
                    window.loadingSteps.delete(testIndex);
                    delete window[`onStepsLoaded_${testIndex}`];
                    updateProgress(0, '文件加载失败');
                    console.error('Failed to load steps file:', testItem.steps_file, event);
                    reject(new Error('Failed to load steps file: ' + testItem.steps_file));
                };
                
                updateProgress(30, '下载步骤文件...');
                document.head.appendChild(script);
            });
        }

        // 更新进度条
        function updateProgress(percentage, text) {
            const progressBar = document.getElementById('loadingProgress');
            const progressText = document.getElementById('progressText');
            
            if (progressBar) {
                progressBar.style.width = percentage + '%';
            }
            if (progressText) {
                progressText.textContent = text;
            }
        }

        // 初始化步骤控制逻辑
        function initializeStepsControls(allSteps, tbody, paginationContainer) {
            let currentFilteredSteps = [];
            let currentPage = 0;
            const STEPS_PER_PAGE = 200;

            function updateAndRender() {
                const searchTerm = document.getElementById('stepSearchInput').value.toLowerCase();
                const activeFilter = document.querySelector('.step-filter-btn.active').dataset.filter;

                currentFilteredSteps = allSteps.filter(step => {
                    let searchMatch = (step.content && step.content.toLowerCase().includes(searchTerm)) || 
                                     (step.ident && step.ident.toLowerCase().includes(searchTerm));
                    
                    // 搜索表格数据
                    if (!searchMatch && step.tabular_info && searchTerm) {
                        // 搜索表格描述
                        if (step.tabular_info.description && step.tabular_info.description.toLowerCase().includes(searchTerm)) {
                            searchMatch = true;
                        }
                        
                        // 搜索表头
                        if (!searchMatch && step.tabular_info.headings) {
                            searchMatch = step.tabular_info.headings.some(heading => 
                                heading && heading.toLowerCase().includes(searchTerm)
                            );
                        }
                        
                        // 搜索表格行数据
                        if (!searchMatch && step.tabular_info.rows) {
                            searchMatch = step.tabular_info.rows.some(row => 
                                row.some(cell => cell && cell.toLowerCase().includes(searchTerm))
                            );
                        }
                    }
                    
                    if (activeFilter === 'all') {
                        return searchMatch;
                    }
                    const resultLower = step.result.toLowerCase();
                    if (activeFilter === 'pass') {
                        return searchMatch && resultLower === 'pass';
                    }
                    if (activeFilter === 'fail') {
                        return searchMatch && (resultLower === 'fail' || resultLower === 'ng');
                    }
                    if (activeFilter === 'warn') {
                        return searchMatch && resultLower === 'warn';
                    }
                    return false;
                });
                
                currentPage = 0;
                renderCurrentPage();
                updatePaginationControls();
            }

            function renderCurrentPage() {
                const start = currentPage * STEPS_PER_PAGE;
                const end = start + STEPS_PER_PAGE;
                const stepsForPage = currentFilteredSteps.slice(start, end);
                renderSteps(stepsForPage, tbody);
            }

            function updatePaginationControls() {
                const totalPages = Math.ceil(currentFilteredSteps.length / STEPS_PER_PAGE);

                // 如果只有一页或无数据，隐藏分页控件
                if (totalPages <= 1) {
                    paginationContainer.style.display = 'none';
                    return;
                }

                // 显示分页控件
                paginationContainer.style.display = 'flex';
                paginationContainer.innerHTML = '';

                const prevButton = document.createElement('button');
                prevButton.textContent = '上一页';
                prevButton.disabled = currentPage === 0;
                prevButton.onclick = () => {
                    if (currentPage > 0) {
                        currentPage--;
                        renderCurrentPage();
                        updatePaginationControls();
                    }
                };

                const nextButton = document.createElement('button');
                nextButton.textContent = '下一页';
                nextButton.disabled = currentPage >= totalPages - 1;
                nextButton.onclick = () => {
                    if (currentPage < totalPages - 1) {
                        currentPage++;
                        renderCurrentPage();
                        updatePaginationControls();
                    }
                };

                const pageInfo = document.createElement('span');
                pageInfo.textContent = `第 ${currentPage + 1} / ${totalPages} 页 (共 ${currentFilteredSteps.length} 条)`;
                pageInfo.style.margin = '0 1rem';

                // 添加页面跳转功能
                const jumpContainer = document.createElement('div');
                jumpContainer.className = 'page-jump-container';
                jumpContainer.style.marginLeft = '1rem';

                const jumpLabel = document.createElement('span');
                jumpLabel.textContent = '跳至';
                jumpLabel.style.marginRight = '0.5rem';

                const jumpInput = document.createElement('input');
                jumpInput.type = 'number';
                jumpInput.min = '1';
                jumpInput.max = totalPages.toString();
                jumpInput.value = (currentPage + 1).toString();
                jumpInput.className = 'page-jump-input';
                jumpInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        jumpToPage();
                    }
                });

                const jumpButton = document.createElement('button');
                jumpButton.textContent = '跳转';
                jumpButton.className = 'page-jump-btn';
                jumpButton.onclick = jumpToPage;

                const jumpPageLabel = document.createElement('span');
                jumpPageLabel.textContent = '页';
                jumpPageLabel.style.marginLeft = '0.5rem';

                function jumpToPage() {
                    const targetPage = parseInt(jumpInput.value, 10);
                    if (isNaN(targetPage) || targetPage < 1 || targetPage > totalPages) {
                        alert(`请输入有效的页码 (1-${totalPages})`);
                        jumpInput.value = (currentPage + 1).toString();
                        return;
                    }
                    currentPage = targetPage - 1;
                    renderCurrentPage();
                    updatePaginationControls();
                }

                jumpContainer.appendChild(jumpLabel);
                jumpContainer.appendChild(jumpInput);
                jumpContainer.appendChild(jumpPageLabel);
                jumpContainer.appendChild(jumpButton);

                paginationContainer.appendChild(prevButton);
                paginationContainer.appendChild(pageInfo);
                paginationContainer.appendChild(nextButton);
                paginationContainer.appendChild(jumpContainer);
            }

            // 添加事件监听器
            document.getElementById('stepSearchInput').addEventListener('keyup', updateAndRender);
            document.querySelectorAll('.step-filter-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    document.querySelector('.step-filter-btn.active').classList.remove('active');
                    e.target.classList.add('active');
                    updateAndRender();
                });
            });

            // 初始加载
            updateAndRender();
        }

        function renderSteps(steps, tbody) {
            tbody.innerHTML = ''; // Clear previous steps
            if (!Array.isArray(steps)) {
                return; // 如果steps不是数组，直接返回
            }
            steps.forEach((step, index) => {
                const row = tbody.insertRow();
                
                // 为行添加右键菜单事件
                row.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    showStepContextMenu(e, step, index, steps);
                });
                
                row.insertCell().textContent = step.timestamp;
                row.insertCell().textContent = step.ident;
                
                const resultCell = row.insertCell();
                // 当结果为NA时显示为"-"
                resultCell.textContent = step.result.toLowerCase() === 'na' ? '-' : step.result;
                resultCell.className = `result-${step.result.toLowerCase()}`;

                const contentCell = row.insertCell();
                contentCell.textContent = step.content; // Use textContent for safety

                if (step.tabular_info && (step.tabular_info.headings || step.tabular_info.rows)) {
                    const tabularContainer = document.createElement('div');
                    let tableHtml = `<table class="InfoTableExpand">`;
                    if(step.tabular_info.description) {
                        tableHtml += `<caption>${escapeHTML(step.tabular_info.description)}</caption>`;
                    }
                    if (step.tabular_info.headings && step.tabular_info.headings.length > 0) {
                        tableHtml += '<thead><tr>';
                        step.tabular_info.headings.forEach(h => {
                            tableHtml += `<th>${escapeHTML(h)}</th>`;
                        });
                        tableHtml += '</tr></thead>';
                    }
                    tableHtml += '<tbody>';
                    if (step.tabular_info.rows && step.tabular_info.rows.length > 0) {
                        step.tabular_info.rows.forEach(r => {
                            tableHtml += '<tr>';
                            r.forEach(c => {
                                tableHtml += `<td>${escapeHTML(c)}</td>`;
                            });
                            tableHtml += '</tr>';
                        });
                    }
                    tableHtml += '</tbody></table>';
                    contentCell.innerHTML = ''; // Clear the text content
                    contentCell.appendChild(document.createTextNode(step.content));
                    contentCell.insertAdjacentHTML('beforeend', tableHtml);
                }
            });
        }

        function renderStepsPage(item, pageIndex, tbody) {
            const steps = item.steps_pages[pageIndex];
            renderSteps(steps, tbody);
            // Update pagination controls state if needed
            const paginationDiv = document.querySelector('.pagination-controls');
            if (paginationDiv) {
                const pageInfo = paginationDiv.querySelector('.page-info');
                pageInfo.textContent = `第 ${pageIndex + 1} / ${item.steps_pages.length} 页`;
                
                const prevButton = paginationDiv.querySelector('.prev-page');
                const nextButton = paginationDiv.querySelector('.next-page');
                prevButton.disabled = pageIndex === 0;
                nextButton.disabled = pageIndex === item.steps_pages.length - 1;
                paginationDiv.dataset.currentPage = pageIndex;
            }
        }

        function createPaginationControls(item) {
            const paginationDiv = document.createElement('div');
            paginationDiv.className = 'pagination-controls';
            paginationDiv.style.marginTop = '1rem';
            paginationDiv.style.textAlign = 'center';
            paginationDiv.dataset.currentPage = 0;

            // 如果只有一页，隐藏分页控件
            if (item.steps_pages.length <= 1) {
                paginationDiv.style.display = 'none';
                return paginationDiv;
            }

            const prevButton = document.createElement('button');
            prevButton.textContent = '上一页';
            prevButton.className = 'prev-page';
            prevButton.disabled = true;
            prevButton.onclick = () => {
                let currentPage = parseInt(paginationDiv.dataset.currentPage, 10);
                if (currentPage > 0) {
                    currentPage--;
                    const tbody = paginationDiv.previousElementSibling.querySelector('tbody');
                    renderStepsPage(item, currentPage, tbody);
                }
            };

            const nextButton = document.createElement('button');
            nextButton.textContent = '下一页';
            nextButton.className = 'next-page';
            nextButton.disabled = item.steps_pages.length <= 1;
            nextButton.onclick = () => {
                let currentPage = parseInt(paginationDiv.dataset.currentPage, 10);
                if (currentPage < item.steps_pages.length - 1) {
                    currentPage++;
                    const tbody = paginationDiv.previousElementSibling.querySelector('tbody');
                    renderStepsPage(item, currentPage, tbody);
                }
            };

            const pageInfo = document.createElement('span');
            pageInfo.className = 'page-info';
            pageInfo.textContent = `第 1 / ${item.steps_pages.length} 页`;
            pageInfo.style.margin = '0 1rem';

            paginationDiv.appendChild(prevButton);
            paginationDiv.appendChild(pageInfo);
            paginationDiv.appendChild(nextButton);

            return paginationDiv;
        }

        function showSystemInfo() {
            const rightPanel = document.getElementById('rightPanel');
            const engineerInfo = window.systemInfo.engineer;
            const testsetupInfo = window.systemInfo.testsetup;
            const hardwareInfo = window.systemInfo.hardware;
            
            // 移除当前激活状态
            if (currentActiveItem) {
                currentActiveItem.classList.remove('active');
                currentActiveItem = null;
            }
            
            let engineerHtml = '';
            Object.entries(engineerInfo).forEach(([key, value]) => {
                const displayValue = value || "未指定";
                const isLongText = displayValue.length > 100;
                const cssClass = isLongText ? "text-overflow" : "";
                
                engineerHtml += `
                    <div class="info-item">
                        <div class="info-label">${key}</div>
                        <div class="info-value ${cssClass}" title="${displayValue}">${displayValue}</div>
                    </div>
                `;
            });
            
            let testsetupHtml = '';
            Object.entries(testsetupInfo).forEach(([key, value]) => {
                const displayValue = value || "未指定";
                const isLongText = displayValue.length > 100;
                const cssClass = isLongText ? "text-overflow" : "";
                
                testsetupHtml += `
                    <div class="info-item">
                        <div class="info-label">${key}</div>
                        <div class="info-value ${cssClass}" title="${displayValue}">${displayValue}</div>
                    </div>
                `;
            });
            
            let hardwareHtml = '';
            Object.entries(hardwareInfo).forEach(([key, hardware]) => {
                hardwareHtml += `
                    <div class="hardware-category">
                        <h4>${hardware.name}</h4>
                        <p class="hardware-category-desc">类别: ${hardware.category || '未指定'}</p>
                `;
                
                // 显示每个设备的信息
                hardware.devices.forEach((device, i) => {
                    const deviceTitle = device.type === 'general' ? `设备 ${i + 1}` : `${device.type} 设备 ${i + 1}`;
                    hardwareHtml += `
                        <div class="hardware-device">
                            <h5>${deviceTitle}</h5>
                            <div class="device-properties">
                    `;
                    
                    // 显示设备属性
                    Object.entries(device.properties).forEach(([propKey, propInfo]) => {
                        hardwareHtml += `
                            <div class="property-item">
                                <span class="property-label">${propInfo.name}:</span>
                                <span class="property-value">${propInfo.description}</span>
                            </div>
                        `;
                    });
                    
                    hardwareHtml += `
                            </div>
                        </div>
                    `;
                });
                
                hardwareHtml += `
                    </div>
                `;
            });
            
            rightPanel.innerHTML = `
                <div class="detail-section">
                    <h3>工程师信息</h3>
                    <div class="info-grid">
                        ${engineerHtml}
                    </div>
                </div>
                <div class="detail-section">
                    <h3>测试设置</h3>
                    <div class="info-grid">
                        ${testsetupHtml}
                    </div>
                </div>
                <div class="detail-section">
                    <h3>硬件信息</h3>
                    <div class="hardware-info">
                        ${hardwareHtml}
                    </div>
                </div>
            `;
        }
        
        function filterTests(filter) {
            const testItems = document.querySelectorAll('.test-item');
            const filterButtons = document.querySelectorAll('.filter-btn');
            
            // 更新按钮状态
            filterButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelector(`[data-filter="${filter}"]`).classList.add('active');
            
            testItems.forEach(item => {
                const itemType = item.getAttribute('data-type');
                const itemResult = item.getAttribute('data-result');
                
                if (filter === 'all') {
                    item.style.display = 'block';
                } else if (filter === 'pass') {
                    item.style.display = itemResult === 'pass' ? 'block' : 'none';
                } else if (filter === 'fail') {
                    item.style.display = itemResult === 'fail' ? 'block' : 'none';
                } else if (filter === 'skipped') {
                    item.style.display = itemType === 'skipped' ? 'block' : 'none';
                }
            });
            
            // 更新统计信息
            updateFilterStats();
        }
        
        function updateFilterStats() {
            const testItems = document.querySelectorAll('.test-item');
            let visibleCount = 0;
            
            testItems.forEach(item => {
                if (item.style.display !== 'none') {
                    visibleCount++;
                }
            });
            
            const statsElement = document.querySelector('.filter-stats');
            if (statsElement) {
                statsElement.textContent = `显示 ${visibleCount} 项`;
            }
        }
        
        // 表格展开/折叠功能
        function switchTable(tableId) {
            const table = document.getElementById(tableId);
            if (table) {
                const isVisible = table.style.display !== 'none';
                table.style.display = isVisible ? 'none' : 'table';
                
                // 更新展开/折叠图标
                const linkId = tableId.replace('_expand', '');
                const link = document.getElementById(linkId);
                if (link) {
                    link.textContent = isVisible ? '[+]' : '[−]';
                }
            }
        }

        // 检测文本溢出并应用相应样式
        function checkTextOverflow() {
            // 检测info-value的溢出
            const infoValues = document.querySelectorAll('.info-value');
            infoValues.forEach(element => {
                if (element.scrollHeight > element.clientHeight) {
                    element.classList.add('text-overflow');
                }
            });
            
            // 检测info-label的溢出并添加title提示
            const infoLabels = document.querySelectorAll('.info-label');
            infoLabels.forEach(element => {
                if (element.scrollWidth > element.clientWidth) {
                    element.title = element.textContent;
                    element.style.cursor = 'help';
                }
            });
        }

        // 页面加载完成后检测文本溢出
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(checkTextOverflow, 100);
        });

        // 当显示系统信息时重新检测文本溢出
        const originalShowSystemInfo = showSystemInfo;
        showSystemInfo = function() {
            originalShowSystemInfo();
            setTimeout(checkTextOverflow, 100);
        };

        // 右键菜单功能
        let contextMenu = null;
        let allStepsData = []; // 存储当前测试用例的所有步骤数据

        function showStepContextMenu(event, step, stepIndex, filteredSteps) {
            // 移除已存在的菜单
            if (contextMenu) {
                contextMenu.remove();
            }

            // 创建菜单
            contextMenu = document.createElement('div');
            contextMenu.className = 'context-menu';
            contextMenu.style.left = event.pageX + 'px';
            contextMenu.style.top = event.pageY + 'px';

            // 菜单项
            const menuItems = [
                { text: '查看前后 10 步', count: 10 },
                { text: '查看前后 30 步', count: 30 },
                { text: '查看前后 50 步', count: 50 }
            ];

            menuItems.forEach(item => {
                const menuItem = document.createElement('div');
                menuItem.className = 'context-menu-item';
                menuItem.textContent = item.text;
                menuItem.onclick = () => {
                    showStepContext(step, stepIndex, filteredSteps, item.count);
                    contextMenu.remove();
                };
                contextMenu.appendChild(menuItem);
            });

            // 添加分隔线
            const separator = document.createElement('div');
            separator.style.height = '1px';
            separator.style.background = '#dee2e6';
            separator.style.margin = '0.5rem 0';
            contextMenu.appendChild(separator);

            // 添加取消选项
            const cancelItem = document.createElement('div');
            cancelItem.className = 'context-menu-item';
            cancelItem.textContent = '取消';
            cancelItem.onclick = () => {
                contextMenu.remove();
            };
            contextMenu.appendChild(cancelItem);

            document.body.appendChild(contextMenu);
            contextMenu.style.display = 'block';

            // 确保菜单不会超出屏幕边界
            const rect = contextMenu.getBoundingClientRect();
            if (rect.right > window.innerWidth) {
                contextMenu.style.left = (event.pageX - rect.width) + 'px';
            }
            if (rect.bottom > window.innerHeight) {
                contextMenu.style.top = (event.pageY - rect.height) + 'px';
            }
        }

        function showStepContext(currentStep, currentIndex, filteredSteps, contextCount) {
            // 需要从完整的步骤数据中查找上下文
            // 首先找到当前步骤在完整数据中的位置
            const currentStepOriginalIndex = findStepInOriginalData(currentStep);
            
            if (currentStepOriginalIndex === -1) {
                alert('无法找到当前步骤的位置信息');
                return;
            }

            // 计算上下文范围
            const startIndex = Math.max(0, currentStepOriginalIndex - contextCount);
            const endIndex = Math.min(allStepsData.length - 1, currentStepOriginalIndex + contextCount);
            
            // 提取上下文步骤
            const contextSteps = allStepsData.slice(startIndex, endIndex + 1);

            // 创建弹窗
            createStepContextModal(contextSteps, currentStepOriginalIndex - startIndex, contextCount);
        }

        function findStepInOriginalData(targetStep) {
            // 通过时间戳和标识符匹配来找到步骤在原始数据中的位置
            for (let i = 0; i < allStepsData.length; i++) {
                const step = allStepsData[i];
                if (step.timestamp === targetStep.timestamp && 
                    step.ident === targetStep.ident && 
                    step.content === targetStep.content) {
                    return i;
                }
            }
            return -1;
        }

        function createStepContextModal(contextSteps, currentStepIndex, contextCount) {
            // 创建模态框
            const modal = document.createElement('div');
            modal.className = 'step-context-modal';

            const modalContent = document.createElement('div');
            modalContent.className = 'step-context-content';

            // 头部
            const header = document.createElement('div');
            header.className = 'step-context-header';
            
            const title = document.createElement('h3');
            title.textContent = `步骤上下文 (前后 ${contextCount} 步)`;
            
            const closeBtn = document.createElement('button');
            closeBtn.className = 'step-context-close';
            closeBtn.innerHTML = '&times;';
            closeBtn.onclick = () => modal.remove();

            header.appendChild(title);
            header.appendChild(closeBtn);

            // 内容区域
            const body = document.createElement('div');
            body.className = 'step-context-body';

            // 创建表格
            const table = document.createElement('table');
            table.className = 'step-context-table';

            // 表头
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th class="step-index">#</th>
                    <th class="step-timestamp">时间戳</th>
                    <th class="step-ident">标识</th>
                    <th class="step-result">结果</th>
                    <th class="step-content">内容</th>
                </tr>
            `;

            // 表体
            const tbody = document.createElement('tbody');
            contextSteps.forEach((step, index) => {
                const row = document.createElement('tr');
                
                // 标记当前步骤
                if (index === currentStepIndex) {
                    row.className = 'current-step';
                }

                // 创建各个单元格
                const indexCell = document.createElement('td');
                indexCell.className = 'step-index';
                indexCell.textContent = index + 1;

                const timestampCell = document.createElement('td');
                timestampCell.className = 'step-timestamp';
                timestampCell.textContent = step.timestamp;

                const identCell = document.createElement('td');
                identCell.className = 'step-ident';
                identCell.textContent = step.ident;

                const resultCell = document.createElement('td');
                resultCell.className = 'step-result';
                const resultSpan = document.createElement('span');
                resultSpan.className = `result-badge result-${step.result.toLowerCase()}`;
                resultSpan.textContent = step.result.toLowerCase() === 'na' ? '-' : step.result;
                resultCell.appendChild(resultSpan);

                const contentCell = document.createElement('td');
                contentCell.className = 'step-content';
                contentCell.textContent = step.content || '';

                // 处理表格信息 - 使用与主页面相同的逻辑
                if (step.tabular_info && (step.tabular_info.headings || step.tabular_info.rows)) {
                    let tableHtml = `<table class="InfoTableExpand">`;
                    if(step.tabular_info.description) {
                        tableHtml += `<caption>${escapeHTML(step.tabular_info.description)}</caption>`;
                    }
                    if (step.tabular_info.headings && step.tabular_info.headings.length > 0) {
                        tableHtml += '<thead><tr>';
                        step.tabular_info.headings.forEach(h => {
                            tableHtml += `<th>${escapeHTML(h)}</th>`;
                        });
                        tableHtml += '</tr></thead>';
                    }
                    tableHtml += '<tbody>';
                    if (step.tabular_info.rows && step.tabular_info.rows.length > 0) {
                        step.tabular_info.rows.forEach(r => {
                            tableHtml += '<tr>';
                            r.forEach(c => {
                                tableHtml += `<td>${escapeHTML(c)}</td>`;
                            });
                            tableHtml += '</tr>';
                        });
                    }
                    tableHtml += '</tbody></table>';
                    
                    // 清空内容并添加文本和表格
                    contentCell.innerHTML = '';
                    contentCell.appendChild(document.createTextNode(step.content || ''));
                    contentCell.insertAdjacentHTML('beforeend', tableHtml);
                }

                // 添加所有单元格到行
                row.appendChild(indexCell);
                row.appendChild(timestampCell);
                row.appendChild(identCell);
                row.appendChild(resultCell);
                row.appendChild(contentCell);

                tbody.appendChild(row);
            });

            table.appendChild(thead);
            table.appendChild(tbody);
            body.appendChild(table);

            modalContent.appendChild(header);
            modalContent.appendChild(body);
            modal.appendChild(modalContent);

            // 添加到页面
            document.body.appendChild(modal);

            // 点击模态框背景关闭
            modal.onclick = (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            };

            // ESC键关闭
            const handleEscape = (e) => {
                if (e.key === 'Escape') {
                    modal.remove();
                    document.removeEventListener('keydown', handleEscape);
                }
            };
            document.addEventListener('keydown', handleEscape);

            // 滚动到当前步骤
            setTimeout(() => {
                const currentRow = tbody.children[currentStepIndex];
                if (currentRow) {
                    currentRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 100);
        }

        // 点击其他地方时隐藏右键菜单
        document.addEventListener('click', () => {
            if (contextMenu) {
                contextMenu.remove();
                contextMenu = null;
            }
        });

        // 修改initializeStepsControls函数，保存完整的步骤数据
        const originalInitializeStepsControls = initializeStepsControls;
        initializeStepsControls = function(allSteps, tbody, paginationContainer) {
            // 保存完整的步骤数据供右键菜单使用
            allStepsData = allSteps;
            // 调用原始函数
            originalInitializeStepsControls(allSteps, tbody, paginationContainer);
        };
        """

def parse_test_report(xml_file_path):
    """解析测试报告"""
    parser = TestReportParser(xml_file_path)
    return parser.parse()

def generate_html_report(report_data, output_file_path):
    """生成HTML报告"""
    generator = HTMLReportGenerator(report_data)
    generator.generate(output_file_path)

def main():
    print("=" * 60)
    print("测试报告生成器启动")
    print("=" * 60)
    
    try:
        # 输入和输出文件路径
        input_file = 'TestReport0002.xml'
        output_file = 'test_report.html'
        
        print(f"正在解析XML文件: {input_file}")
        
        # 解析XML
        report_data = parse_test_report(input_file)
        
        if not report_data:
            print("❌ 解析失败: 无法读取XML文件")
            return
        
        print(f"✅ XML解析完成")
        print(f"   - 测试组数量: {len(report_data.test_groups)}")
        print(f"   - 总测试项数量: {len(report_data.test_items)}")
        
        # 统计测试用例数量
        total_test_cases = 0
        skipped_count = 0
        for item in report_data.test_items:
            if hasattr(item, 'verdict'):  # TestCase
                total_test_cases += 1
            else:  # SkippedTest
                skipped_count += 1
        
        print(f"   - 执行的测试用例: {total_test_cases}")
        print(f"   - 跳过的测试: {skipped_count}")
        
        print(f"\n正在生成HTML报告: {output_file}")
        
        # 生成HTML报告
        generate_html_report(report_data, output_file)
        
        print(f"✅ HTML报告生成完成!")
        print(f"   报告文件: {output_file}")
        print(f"   请在浏览器中打开查看")
        
    except Exception as e:
        print(f"❌ 生成报告时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    print("脚本执行完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
