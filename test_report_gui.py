#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试报告生成器 GUI版本
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path
import webbrowser
from datetime import datetime
from test_report_generator import parse_test_report, generate_html_report

class TestReportGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("测试报告生成器 v6.0")
        self.root.geometry("800x650")
        self.root.minsize(600, 500)
        
        # -- 颜色和字体定义 --
        self.colors = {
            "bg": "#f0f2f5",
            "card_bg": "#ffffff",
            "text": "#333333",
            "text_secondary": "#666666",
            "accent": "#0078d4",
            "accent_light": "#e6f2ff",
            "border": "#e0e0e0",
            "success": "#107c10",
            "error": "#d83b01"
        }
        self.fonts = {
            "title": ("Segoe UI", 18, "bold"),
            "heading": ("Segoe UI", 12, "bold"),
            "body": ("Segoe UI", 10),
            "button": ("Segoe UI", 10, "bold"),
            "small": ("Segoe UI", 8)
        }

        self.root.configure(bg=self.colors["bg"])
        
        # 设置窗口图标（如果有的话）
        try:
            # 在Windows上，打包后可能需要指定路径
            icon_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass
        
        self.setup_styles()
        self.setup_ui()
        self.xml_file_path = ""
        self.output_file_path = ""
        
    def setup_styles(self):
        """配置ttk样式"""
        style = ttk.Style(self.root)
        style.theme_use('clam')

        # -- 全局设置 --
        style.configure('.', 
            background=self.colors["bg"], 
            foreground=self.colors["text"], 
            font=self.fonts["body"])

        # -- Frame样式 --
        style.configure('TFrame', background=self.colors["bg"])
        style.configure('Card.TFrame', background=self.colors["card_bg"], borderwidth=1, relief='solid')
        style.map('Card.TFrame', bordercolor=[('!focus', self.colors["border"]), ('focus', self.colors["accent"])])

        # -- Label样式 --
        style.configure('TLabel', background=self.colors["card_bg"], foreground=self.colors["text"], font=self.fonts["body"])
        style.configure('Title.TLabel', background=self.colors["bg"], font=self.fonts["title"], foreground=self.colors["text"])
        style.configure('Heading.TLabel', background=self.colors["card_bg"], font=self.fonts["heading"], foreground=self.colors["text"])
        style.configure('Status.TLabel', background=self.colors["bg"], font=self.fonts["body"])
        style.configure('Footer.TLabel', background=self.colors["bg"], font=self.fonts["small"], foreground=self.colors["text_secondary"])

        # -- Button样式 --
        style.configure('TButton', 
            font=self.fonts["button"], 
            padding=(10, 5),
            borderwidth=1,
            relief='solid',
            background=self.colors["card_bg"],
            foreground=self.colors["accent"],
            bordercolor=self.colors["accent"])
        style.map('TButton',
            background=[('active', self.colors["accent_light"])],
            bordercolor=[('active', self.colors["accent"])])

        style.configure('Accent.TButton', 
            foreground='#ffffff', 
            background=self.colors["accent"],
            bordercolor=self.colors["accent"])
        style.map('Accent.TButton',
            background=[('active', '#005a9e')],
            bordercolor=[('active', '#005a9e')])
            
        # -- Entry样式 --
        style.configure('TEntry', 
            fieldbackground=self.colors["card_bg"], 
            foreground=self.colors["text"],
            bordercolor=self.colors["border"],
            borderwidth=1,
            padding=5)
        style.map('TEntry',
            bordercolor=[('focus', self.colors["accent"])])

        # -- Progressbar样式 --
        style.configure('TProgressbar', 
            troughcolor=self.colors["border"], 
            background=self.colors["accent"])
            
        # -- LabelFrame (用于日志) --
        style.configure('Log.TLabelframe', 
            background=self.colors["card_bg"], 
            bordercolor=self.colors["border"],
            padding=10)
        style.configure('Log.TLabelframe.Label', 
            background=self.colors["card_bg"], 
            font=self.fonts["heading"],
            foreground=self.colors["text"])

    def setup_ui(self):
        """设置用户界面"""
        main_frame = ttk.Frame(self.root, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1) # 让日志区域扩展

        # --- 标题 ---
        title_label = ttk.Label(main_frame, text="测试报告生成器", style="Title.TLabel")
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="w")

        # --- 文件选择卡片 ---
        file_card = ttk.Frame(main_frame, style='Card.TFrame', padding=20)
        file_card.grid(row=1, column=0, sticky="ew", pady=10)
        file_card.columnconfigure(1, weight=1)

        ttk.Label(file_card, text="输入与输出", style="Heading.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 15))

        # XML文件选择
        ttk.Label(file_card, text="XML报告:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.xml_file_var = tk.StringVar()
        xml_entry = ttk.Entry(file_card, textvariable=self.xml_file_var, width=60)
        xml_entry.grid(row=1, column=1, sticky="ew")
        ttk.Button(file_card, text="浏览...", command=self.select_xml_file).grid(row=1, column=2, padx=(10, 0))
        
        # 输出文件选择
        ttk.Label(file_card, text="HTML输出:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.output_file_var = tk.StringVar()
        output_entry = ttk.Entry(file_card, textvariable=self.output_file_var, width=60)
        output_entry.grid(row=2, column=1, sticky="ew", pady=(10, 0))
        ttk.Button(file_card, text="另存为...", command=self.select_output_file).grid(row=2, column=2, padx=(10, 0), pady=(10, 0))

        # --- 日志和控制区域 ---
        log_control_frame = ttk.Frame(main_frame)
        log_control_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        log_control_frame.columnconfigure(0, weight=1)
        log_control_frame.rowconfigure(0, weight=1)

        # 日志输出区域
        log_frame = ttk.LabelFrame(log_control_frame, text="运行日志", style="Log.TLabelframe")
        log_frame.grid(row=0, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
            height=10, 
            wrap=tk.WORD, 
            bg=self.colors["card_bg"], 
            fg=self.colors["text_secondary"],
            font=self.fonts["body"],
            relief="flat",
            borderwidth=0)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.log_text.tag_config("success", foreground=self.colors["success"])
        self.log_text.tag_config("error", foreground=self.colors["error"])

        # --- 底部控制栏 ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        bottom_frame.columnconfigure(1, weight=1)

        # 操作按钮
        button_frame = ttk.Frame(bottom_frame)
        button_frame.grid(row=0, column=0, sticky="w")
        
        self.generate_btn = ttk.Button(button_frame, text="生成报告", command=self.generate_report, style="Accent.TButton")
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.open_btn = ttk.Button(button_frame, text="打开报告", command=self.open_report, state="disabled")
        self.open_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT)

        # 进度条和状态
        progress_status_frame = ttk.Frame(bottom_frame)
        progress_status_frame.grid(row=0, column=1, sticky="ew", padx=(20, 0))
        progress_status_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        
        self.status_var = tk.StringVar(value="准备就绪")
        status_label = ttk.Label(progress_status_frame, textvariable=self.status_var, style="Status.TLabel", anchor="w")
        status_label.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # --- 页脚 ---
        footer_label = ttk.Label(main_frame, text="版本: v6.0  |  支持格式: XML → HTML", style="Footer.TLabel")
        footer_label.grid(row=4, column=0, sticky="e", pady=(10, 0))
    
    def log_message(self, message, level="info"):
        """添加日志消息，支持不同级别"""
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n", level)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def select_xml_file(self):
        """选择XML文件"""
        file_path = filedialog.askopenfilename(
            title="选择XML测试报告文件",
            filetypes=[("XML文件", "*.xml"), ("所有文件", "*.*")]
        )
        if file_path:
            self.xml_file_var.set(file_path)
            self.xml_file_path = file_path
            
            # 自动设置输出文件名
            xml_path = Path(file_path)
            output_path = xml_path.parent / f"{xml_path.stem}_report.html"
            self.output_file_var.set(str(output_path))
            self.output_file_path = str(output_path)
            
            self.log_message(f"已选择XML文件: {file_path}")
    
    def select_output_file(self):
        """选择输出文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存HTML报告文件",
            defaultextension=".html",
            filetypes=[("HTML文件", "*.html"), ("所有文件", "*.*")]
        )
        if file_path:
            self.output_file_var.set(file_path)
            self.output_file_path = file_path
            self.log_message(f"输出文件将保存至: {file_path}")
    
    def update_progress(self, value, status=""):
        """更新进度条和状态"""
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        self.root.update_idletasks()
    
    def generate_report(self):
        """生成报告"""
        if not self.xml_file_path:
            messagebox.showerror("错误", "请先选择XML文件")
            return
        
        if not self.output_file_path:
            messagebox.showerror("错误", "请先选择输出文件")
            return
        
        if not os.path.exists(self.xml_file_path):
            messagebox.showerror("错误", "XML文件不存在")
            return
        
        # 在单独线程中生成报告
        self.generate_btn.config(state="disabled")
        self.open_btn.config(state="disabled")
        
        thread = threading.Thread(target=self._generate_report_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_report_thread(self):
        """在线程中生成报告"""
        try:
            self.update_progress(0, "开始生成报告...")
            self.log_message("=" * 60)
            self.log_message("🚀 开始生成测试报告...")
            
            # 解析XML文件
            self.update_progress(20, "正在解析XML文件...")
            self.log_message(f"正在解析: {os.path.basename(self.xml_file_path)}")
            
            report_data = parse_test_report(self.xml_file_path)
            
            if not report_data:
                raise Exception("解析XML文件失败，请检查文件格式或内容。")
            
            self.update_progress(50, "XML解析完成")
            self.log_message("✅ XML解析完成", level="success")
            self.log_message(f"   - 测试组: {len(report_data.test_groups)}个")
            self.log_message(f"   - 总测试项: {len(report_data.test_items)}个")
            
            # 统计测试用例数量
            total_test_cases = sum(1 for item in report_data.test_items if hasattr(item, 'verdict'))
            skipped_count = len(report_data.test_items) - total_test_cases
            
            self.log_message(f"   - 执行用例: {total_test_cases}个")
            if skipped_count > 0:
                self.log_message(f"   - 跳过测试: {skipped_count}个")
            
            # 生成HTML报告
            self.update_progress(70, "正在生成HTML报告...")
            self.log_message(f"\n正在生成HTML报告: {os.path.basename(self.output_file_path)}")
            
            generate_html_report(report_data, self.output_file_path)
            
            self.update_progress(100, "报告生成成功！")
            self.log_message("🎉 HTML报告生成完成!", level="success")
            self.log_message(f"   报告已保存至: {self.output_file_path}")
            self.log_message("=" * 60)
            
            # 启用打开按钮
            self.root.after(0, lambda: self.open_btn.config(state="normal"))
            
            # 显示成功消息
            success_message = f"报告已成功生成！\n\n文件保存在:\n{self.output_file_path}"
            self.root.after(0, lambda: messagebox.showinfo("成功", success_message))
            
        except Exception as e:
            error_msg = f"生成报告时发生错误: {str(e)}"
            self.log_message(f"❌ {error_msg}", level="error")
            self.update_progress(0, "生成失败")
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        
        finally:
            # 重新启用生成按钮
            self.root.after(0, lambda: self.generate_btn.config(state="normal"))
    
    def open_report(self):
        """打开生成的报告"""
        if self.output_file_path and os.path.exists(self.output_file_path):
            try:
                webbrowser.open(f"file://{os.path.abspath(self.output_file_path)}")
                self.log_message(f"已在浏览器中打开报告: {self.output_file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开报告文件: {str(e)}")
        else:
            messagebox.showerror("错误", "报告文件不存在")

def main():
    """主函数"""
    root = tk.Tk()
    app = TestReportGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
