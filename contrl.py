import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, Canvas, messagebox, StringVar, Frame
import time
import threading
import ctypes
from ctypes import wintypes
import os
from tkinter import font


class MotorGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RickyTech™️ 力反馈控制系统")
        self.root.geometry("900x700")
        self.root.configure(bg="#f5f5f5")

        # 确保中文显示正常
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="SimHei", size=10)
        self.root.option_add("*Font", self.default_font)

        # 颜色方案
        self.bg_color = "#f5f5f5"
        self.card_color = "#ffffff"
        self.primary_color = "#4a6cf7"  # 主色调：蓝色
        self.secondary_color = "#2ecc71"  # 辅助色：绿色
        self.warning_color = "#e74c3c"  # 警告色：红色
        self.text_color = "#000000"  # 文本颜色：黑色
        self.accent_color = "#6c5ce7"  # 强调色：紫色

        # 串口/游戏控制变量
        self.ser = None
        self.is_connected = False
        self.vjoy_device = None
        self.current_angle = 0.0
        self.target_resistance = 0.0
        self.force_feedback = 0.0
        self.mode = "manual"

        # 力反馈配置参数
        self.ff_gain = 1.0  # 力反馈增益
        self.ff_deadzone = 5  # 死区范围

        # 角度/阻力历史数据
        self.angle_history = []
        self.resistance_history = []
        self.max_history = 200

        # 配置ttk样式
        self.setup_styles()

        # 创建UI
        self.create_navigation()
        self.create_pages()

        # 默认显示设备连接页面
        self.show_page("device")

        # 启动数据接收
        self.root.after(100, self.receive_data)
        self.root.after(500, self.update_plots)

        # 力反馈监听线程
        self.ff_thread = threading.Thread(target=self.listen_for_force_feedback, daemon=True)
        self.ff_thread.start()

    def setup_styles(self):
        """配置ttk样式"""
        style = ttk.Style()

        # 基础样式
        style.configure("TButton", font=("SimHei", 10), padding=5, relief="flat")
        style.configure("TLabel", font=("SimHei", 10), foreground=self.text_color)
        style.configure("TCombobox", font=("SimHei", 10))
        style.configure("TCheckbutton", font=("SimHei", 10))
        style.configure("TRadiobutton", font=("SimHei", 10))

        # 按钮样式
        style.configure("Primary.TButton", foreground=self.text_color, background=self.primary_color, borderwidth=0,
                        focusthickness=0)
        style.configure("Secondary.TButton", foreground=self.text_color, background=self.secondary_color, borderwidth=0,
                        focusthickness=0)
        style.configure("Warning.TButton", foreground=self.text_color, background=self.warning_color, borderwidth=0,
                        focusthickness=0)

        # 标签框架样式
        style.configure("Card.TLabelframe", background=self.card_color, borderwidth=0, relief="flat")
        style.configure("Card.TLabelframe.Label", background=self.primary_color, foreground="white",
                        font=("SimHei", 12, "bold"), padding=(5, 2))

        # 导航按钮样式
        style.configure("NavButton.TButton", background=self.bg_color, foreground=self.text_color,
                        font=("SimHei", 11), padding=(10, 5), anchor="w")
        style.configure("NavButtonSelected.TButton", background=self.primary_color, foreground=self.text_color,
                        font=("SimHei", 11, "bold"), padding=(10, 5), anchor="w")

        # 滑块样式
        style.configure("TScale", background=self.bg_color)

        # 开关按钮样式
        style.configure("Switch.TCheckbutton", background=self.bg_color, indicatoron=False,
                        focuscolor="none", borderwidth=0, padding=0)

        # 确保所有选项和设置的字体为黑色
        style.configure("TRadiobutton", foreground=self.text_color)
        style.configure("TCheckbutton", foreground=self.text_color)
        style.configure("TCombobox", foreground=self.text_color)

    def create_navigation(self):
        """创建导航栏"""
        nav_frame = tk.Frame(self.root, bg=self.bg_color, width=200)
        nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        nav_frame.pack_propagate(False)

        # 品牌标识
        brand_frame = tk.Frame(nav_frame, bg=self.primary_color, height=60)
        brand_frame.pack(fill=tk.X, pady=(0, 20))

        brand_label = tk.Label(
            brand_frame,
            text="RickyTech™️",
            font=("SimHei", 16, "bold"),
            bg=self.primary_color,
            fg="white"
        )
        brand_label.place(relx=0.5, rely=0.5, anchor="center")

        # 导航按钮
        self.nav_buttons = {}
        pages = [
            ("device", "设备连接"),
            ("data", "实时数据"),
            ("ff_config", "力反馈配置"),
            ("game_config", "游戏配置"),
            ("about", "联系我们")
        ]

        for page_id, page_name in pages:
            btn = ttk.Button(
                nav_frame,
                text=page_name,
                command=lambda p=page_id: self.show_page(p),
                style="NavButton.TButton"
            )
            btn.pack(fill=tk.X, pady=2)
            self.nav_buttons[page_id] = btn

        # 状态指示器
        status_frame = tk.Frame(nav_frame, bg=self.card_color, pady=10)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Label(status_frame, text="连接状态：").pack(anchor="w", padx=10)

        self.status_var = StringVar(value="未连接")
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("SimHei", 10, "bold"),
            foreground=self.warning_color
        )
        self.status_label.pack(anchor="w", padx=10)

    def create_pages(self):
        """创建所有页面"""
        self.pages = {}

        # 设备连接页面
        device_frame = tk.Frame(self.root, bg=self.bg_color)
        device_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        self.pages["device"] = device_frame

        # 实时数据页面
        data_frame = tk.Frame(self.root, bg=self.bg_color)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        data_frame.pack_forget()
        self.pages["data"] = data_frame

        # 力反馈配置页面
        ff_config_frame = tk.Frame(self.root, bg=self.bg_color)
        ff_config_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        ff_config_frame.pack_forget()
        self.pages["ff_config"] = ff_config_frame

        # 游戏配置页面
        game_config_frame = tk.Frame(self.root, bg=self.bg_color)
        game_config_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        game_config_frame.pack_forget()
        self.pages["game_config"] = game_config_frame

        # 联系我们页面
        about_frame = tk.Frame(self.root, bg=self.bg_color)
        about_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        about_frame.pack_forget()
        self.pages["about"] = about_frame

        # 填充各页面内容
        self.create_device_page()
        self.create_data_page()
        self.create_ff_config_page()
        self.create_game_config_page()
        self.create_about_page()

    def show_page(self, page_id):
        """显示指定页面"""
        # 隐藏所有页面
        for page in self.pages.values():
            page.pack_forget()

        # 显示选中的页面
        self.pages[page_id].pack(fill=tk.BOTH, expand=True)

        # 更新导航按钮状态
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(style="NavButtonSelected.TButton")
            else:
                btn.configure(style="NavButton.TButton")

    def create_device_page(self):
        """创建设备连接页面"""
        # 模式选择器
        mode_frame = self.create_card_frame(self.pages["device"], "控制模式")
        mode_frame.pack(padx=10, pady=10, fill=tk.X)

        self.mode_var = tk.StringVar(value="manual")

        manual_btn = ttk.Radiobutton(
            mode_frame,
            text="手动控制",
            variable=self.mode_var,
            value="manual",
            command=self.change_mode
        )
        manual_btn.pack(side=tk.LEFT, padx=20, pady=10)

        auto_btn = ttk.Radiobutton(
            mode_frame,
            text="游戏力反馈自动控制",
            variable=self.mode_var,
            value="auto",
            command=self.change_mode
        )
        auto_btn.pack(side=tk.LEFT, padx=20, pady=10)

        # 串口设置
        serial_frame = self.create_card_frame(self.pages["device"], "串口配置")
        serial_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(serial_frame, text="串口号：").grid(row=0, column=0, padx=10, pady=10)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(serial_frame, textvariable=self.port_var, width=10)
        self.port_combo.grid(row=0, column=1, padx=10, pady=10)

        self.refresh_btn = ttk.Button(
            serial_frame,
            text="刷新",
            command=self.refresh_ports,
            style="Primary.TButton"
        )
        self.refresh_btn.grid(row=0, column=2, padx=10, pady=10)

        self.connect_btn = ttk.Button(
            serial_frame,
            text="连接",
            command=self.toggle_connection,
            style="Primary.TButton"
        )
        self.connect_btn.grid(row=0, column=3, padx=10, pady=10)

        # 阻力控制（手动模式）
        self.resistance_frame = self.create_card_frame(self.pages["device"], "阻力设置（0-100）")
        self.resistance_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(self.resistance_frame, text="阻力值：").grid(row=0, column=0, padx=10, pady=10)
        self.resistance_var = tk.StringVar(value="0")
        self.resistance_entry = ttk.Entry(self.resistance_frame, textvariable=self.resistance_var, width=10)
        self.resistance_entry.grid(row=0, column=1, padx=10, pady=10)

        self.send_btn = ttk.Button(
            self.resistance_frame,
            text="发送",
            command=self.send_resistance,
            style="Primary.TButton"
        )
        self.send_btn.grid(row=0, column=2, padx=10, pady=10)

        # 力反馈状态（自动模式）
        self.ff_frame = self.create_card_frame(self.pages["device"], "力反馈状态")
        self.ff_frame.pack(padx=10, pady=10, fill=tk.X)

        self.ff_var = tk.StringVar(value="0.0")
        ttk.Label(self.ff_frame, text="力反馈值：").grid(row=0, column=0, padx=10, pady=10)

        self.ff_label = ttk.Label(
            self.ff_frame,
            textvariable=self.ff_var,
            font=("SimHei", 14, "bold"),
            foreground=self.primary_color
        )
        self.ff_label.grid(row=0, column=1, padx=10, pady=10)

        # 初始化UI状态
        self.change_mode()

    def create_data_page(self):
        """创建实时数据页面"""
        # 角度显示
        angle_frame = self.create_card_frame(self.pages["data"], "实时角度")
        angle_frame.pack(padx=10, pady=10, fill=tk.X)

        self.angle_var = tk.StringVar(value="0.00 度")
        angle_value_label = ttk.Label(
            angle_frame,
            textvariable=self.angle_var,
            font=("SimHei", 24, "bold"),
            foreground=self.primary_color
        )
        angle_value_label.pack(pady=15)

        # 图表区域
        chart_frame = self.create_card_frame(self.pages["data"], "实时数据")
        chart_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 角度曲线图
        self.angle_canvas = Canvas(chart_frame, bg="white", highlightthickness=0)
        self.angle_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 阻力曲线图
        self.resistance_canvas = Canvas(chart_frame, bg="white", highlightthickness=0)
        self.resistance_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_ff_config_page(self):
        """创建力反馈配置页面"""
        config_frame = self.create_card_frame(self.pages["ff_config"], "力反馈参数配置")
        config_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 增益调节
        gain_frame = tk.Frame(config_frame, bg=self.card_color)
        gain_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(gain_frame, text="力反馈增益：").pack(side=tk.LEFT, padx=10, pady=5)

        self.gain_var = tk.DoubleVar(value=self.ff_gain)
        gain_scale = ttk.Scale(
            gain_frame,
            variable=self.gain_var,
            from_=0.1,
            to=2.0,
            orient="horizontal",
            length=300,
            command=lambda s: self.gain_var.set(round(float(s), 1))
        )
        gain_scale.pack(side=tk.LEFT, padx=10, pady=5)

        self.gain_value_label = ttk.Label(gain_frame, text=f"{self.ff_gain:.1f}")
        self.gain_value_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 死区调节
        deadzone_frame = tk.Frame(config_frame, bg=self.card_color)
        deadzone_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(deadzone_frame, text="死区范围：").pack(side=tk.LEFT, padx=10, pady=5)

        self.deadzone_var = tk.IntVar(value=self.ff_deadzone)
        deadzone_scale = ttk.Scale(
            deadzone_frame,
            variable=self.deadzone_var,
            from_=0,
            to=20,
            orient="horizontal",
            length=300,
            command=lambda s: self.deadzone_var.set(round(float(s)))
        )
        deadzone_scale.pack(side=tk.LEFT, padx=10, pady=5)

        self.deadzone_value_label = ttk.Label(deadzone_frame, text=f"{self.ff_deadzone}")
        self.deadzone_value_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 保存配置按钮
        save_frame = tk.Frame(config_frame, bg=self.card_color)
        save_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(
            save_frame,
            text="保存配置",
            command=self.save_ff_config,
            style="Primary.TButton"
        ).pack(side=tk.RIGHT, padx=10, pady=5)

    def create_game_config_page(self):
        """创建游戏配置页面"""
        game_frame = self.create_card_frame(self.pages["game_config"], "游戏配置")
        game_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 游戏列表
        ttk.Label(game_frame, text="支持的游戏：").pack(anchor="w", padx=20, pady=10)

        games = ["赛车游戏", "飞行模拟", "驾驶模拟", "其他游戏"]
        self.game_var = tk.StringVar(value=games[0])

        for game in games:
            ttk.Radiobutton(
                game_frame,
                text=game,
                variable=self.game_var,
                value=game
            ).pack(anchor="w", padx=30, pady=5)

        # 配置选项
        options_frame = tk.Frame(game_frame, bg=self.card_color)
        options_frame.pack(fill=tk.X, padx=20, pady=20)

        # 开关动效实现
        self.enable_ff_var = tk.BooleanVar(value=True)

        enable_ff_frame = tk.Frame(options_frame, bg=self.card_color)
        enable_ff_frame.pack(fill=tk.X, pady=5)

        ttk.Label(enable_ff_frame, text="启用力反馈：").pack(side=tk.LEFT, padx=10)

        # 创建开关按钮
        switch_frame = tk.Frame(enable_ff_frame, bg=self.bg_color, width=50, height=24)
        switch_frame.pack(side=tk.LEFT, padx=10)
        switch_frame.pack_propagate(False)

        self.switch_circle = Canvas(switch_frame, bg=self.bg_color, highlightthickness=0, width=24, height=24)
        self.switch_circle.pack(side=tk.LEFT)

        # 初始状态
        self.update_switch_state()

        switch_frame.bind("<Button-1>", self.toggle_switch)
        self.switch_circle.bind("<Button-1>", self.toggle_switch)

        # 保存配置按钮
        save_frame = tk.Frame(game_frame, bg=self.card_color)
        save_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(
            save_frame,
            text="保存配置",
            command=self.save_game_config,
            style="Primary.TButton"
        ).pack(side=tk.RIGHT, padx=10, pady=5)

    def toggle_switch(self, event=None):
        """切换开关状态"""
        self.enable_ff_var.set(not self.enable_ff_var.get())
        self.update_switch_state()

    def update_switch_state(self):
        """更新开关UI状态"""
        if self.enable_ff_var.get():
            # 开启状态
            self.switch_circle.delete("all")
            self.switch_circle.create_oval(2, 2, 22, 22, fill=self.secondary_color, outline="")
        else:
            # 关闭状态
            self.switch_circle.delete("all")
            self.switch_circle.create_oval(2, 2, 22, 22, fill="#dddddd", outline="")

    def create_about_page(self):
        """创建联系我们页面"""
        about_frame = self.create_card_frame(self.pages["about"], "关于我们")
        about_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Logo区域
        logo_frame = tk.Frame(about_frame, bg=self.card_color)
        logo_frame.pack(fill=tk.X, pady=20)

        ttk.Label(
            logo_frame,
            text="RickyTech™️",
            font=("SimHei", 24, "bold"),
            foreground=self.primary_color
        ).pack(pady=10)

        ttk.Label(
            logo_frame,
            text="力反馈控制系统",
            font=("SimHei", 16)
        ).pack()

        # 联系信息
        contact_frame = tk.Frame(about_frame, bg=self.card_color)
        contact_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(
            contact_frame,
            text="电子邮箱：buding0401@126.com",
            font=("SimHei", 12)
        ).pack(anchor="w", pady=5)

        ttk.Label(
            contact_frame,
            text="技术支持：400-123-4567",
            font=("SimHei", 12)
        ).pack(anchor="w", pady=5)

        # 版权信息
        copyright_frame = tk.Frame(about_frame, bg=self.card_color)
        copyright_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(
            copyright_frame,
            text="© 2025 RickyTech™️ 保留所有权利",
            font=("SimHei", 10)
        ).pack(anchor="center")

        ttk.Label(
            copyright_frame,
            text="RickyTech™️ 保留最终解释权",
            font=("SimHei", 10)
        ).pack(anchor="center", pady=5)

    def create_card_frame(self, parent, title):
        """创建带有圆角的卡片式框架"""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.configure(style="Card.TLabelframe")

        # 创建圆角效果
        style = ttk.Style()
        style.configure("Card.TLabelframe", borderwidth=1, relief="solid",
                        background=self.card_color, bordercolor="#dddddd",
                        darkcolor=self.card_color, lightcolor=self.card_color)

        return frame

    def change_mode(self):
        """切换控制模式（手动/自动）"""
        self.mode = self.mode_var.get()
        if self.mode == "manual":
            self.resistance_frame.configure(text="阻力设置（手动模式）")
            self.resistance_entry.config(state="normal")
            self.send_btn.config(state="normal")
            for child in self.ff_frame.winfo_children():
                child.config(state="disabled")
        else:  # auto
            self.resistance_frame.configure(text="阻力设置（自动模式，值由游戏力反馈控制）")
            self.resistance_entry.config(state="disabled")
            self.send_btn.config(state="disabled")
            for child in self.ff_frame.winfo_children():
                child.config(state="normal")

    def refresh_ports(self):
        """刷新可用串口列表"""
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def toggle_connection(self):
        """切换串口连接状态"""
        if self.is_connected:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.is_connected = False
            self.connect_btn.config(text="连接")
            self.status_var.set("未连接")
            self.status_label.configure(foreground=self.warning_color)
            messagebox.showinfo("提示", "串口已断开")
        else:
            try:
                port = self.port_var.get()
                self.ser = serial.Serial(port, 115200, timeout=0.1)
                self.is_connected = True
                self.connect_btn.config(text="断开")
                self.status_var.set("已连接")
                self.status_label.configure(foreground=self.secondary_color)
                messagebox.showinfo("提示", f"已连接到 {port}")
            except Exception as e:
                messagebox.showerror("错误", f"连接失败：{str(e)}")

    def send_resistance(self):
        """发送阻力值到设备"""
        if not self.is_connected:
            messagebox.showwarning("警告", "请先连接串口")
            return
        try:
            resistance = float(self.resistance_var.get())
            if 0 <= resistance <= 100:
                cmd = f"R:{resistance:.1f}\n"
                self.ser.write(cmd.encode('utf-8'))
                self.target_resistance = resistance
                self.resistance_history.append(resistance)
                if len(self.resistance_history) > self.max_history:
                    self.resistance_history.pop(0)
                # 添加按钮动画
                self.send_btn.configure(style="Success.TButton")
                self.root.after(200, lambda: self.send_btn.configure(style="Primary.TButton"))
            else:
                messagebox.showwarning("警告", "阻力值需在0-100之间")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def receive_data(self):
        """接收来自设备的数据"""
        if self.is_connected and self.ser:
            try:
                data = self.ser.readline().decode('utf-8').strip()
                if data.startswith("A:"):
                    self.current_angle = float(data[2:])
                    self.angle_var.set(f"{self.current_angle:.2f} 度")
                    self.angle_history.append(self.current_angle)
                    if len(self.angle_history) > self.max_history:
                        self.angle_history.pop(0)
            except Exception as e:
                pass
        self.root.after(100, self.receive_data)

    def listen_for_force_feedback(self):
        """监听游戏力反馈数据"""
        try:
            # 加载vJoyInterface.dll
            dll_path = os.path.join(os.getcwd(), "vJoyInterface.dll")
            if not os.path.exists(dll_path):
                print("警告：未找到vJoyInterface.dll，力反馈功能将无法使用")
                return

            vjoy_dll = ctypes.windll.LoadLibrary(dll_path)

            # 定义函数原型
            GetVJFFBState = vjoy_dll.GetVJFFBState
            GetVJFFBState.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            GetVJFFBState.restype = ctypes.c_bool

            # 力反馈状态结构体
            class FFState(ctypes.Structure):
                _fields_ = [
                    ("Device", ctypes.c_int),
                    ("Enabled", ctypes.c_bool),
                    ("MasterGain", ctypes.c_int),
                    ("ConditionCount", ctypes.c_int),
                    ("Conditions", ctypes.c_int * 8),  # 简化版本，实际有更多字段
                    ("PeriodicCount", ctypes.c_int),
                    ("Periodics", ctypes.c_int * 8),
                    ("ConstantCount", ctypes.c_int),
                    ("Constants", ctypes.c_int * 8),
                    ("RampCount", ctypes.c_int),
                    ("Ramps", ctypes.c_int * 8),
                    ("EffectCount", ctypes.c_int),
                    ("Effects", ctypes.c_int * 8)
                ]

            ff_state = FFState()
            device_id = 1  # vJoy设备ID

            while True:
                if self.is_connected and self.mode == "auto" and self.enable_ff_var.get():
                    if GetVJFFBState(device_id, ctypes.byref(ff_state)):
                        # 提取力反馈数据（简化版，仅使用主增益）
                        self.force_feedback = ff_state.MasterGain / 100.0  # 转换为0-100

                        # 应用增益和死区
                        adjusted_force = self.force_feedback * self.ff_gain
                        if abs(adjusted_force) < self.ff_deadzone / 100.0:
                            adjusted_force = 0

                        self.ff_var.set(f"{adjusted_force:.2f}")

                        # 计算阻力值
                        resistance = min(100, max(0, adjusted_force * 100))  # 转换为0-100
                        self.target_resistance = resistance
                        self.resistance_history.append(resistance)
                        if len(self.resistance_history) > self.max_history:
                            self.resistance_history.pop(0)

                        # 发送到ESP32
                        cmd = f"R:{resistance:.1f}\n"
                        self.ser.write(cmd.encode('utf-8'))
                time.sleep(0.05)  # 20Hz采样率
        except Exception as e:
            print(f"力反馈监听错误：{e}")

    def update_plots(self):
        """更新角度和阻力变化曲线"""
        # 角度曲线
        self.angle_canvas.delete("all")
        if len(self.angle_history) >= 2:
            min_angle = min(self.angle_history)
            max_angle = max(self.angle_history)
            range_angle = max_angle - min_angle if max_angle != min_angle else 1

            width = self.angle_canvas.winfo_width() or 850
            height = self.angle_canvas.winfo_height() or 180
            x_step = width / (len(self.angle_history) - 1)

            # 绘制背景网格
            for i in range(5):
                y = i * height / 4
                self.angle_canvas.create_line(0, y, width, y, fill="#e0e0e0", dash=(2, 2))

            # 绘制曲线
            points = []
            for i in range(len(self.angle_history)):
                x = i * x_step
                y = height - ((self.angle_history[i] - min_angle) / range_angle) * (height - 20)
                points.extend([x, y])

            # 创建平滑曲线
            if len(points) >= 4:
                self.angle_canvas.create_line(points, fill=self.primary_color, width=2, smooth=True)

            # 添加标题和坐标轴
            self.angle_canvas.create_text(width / 2, 15, text="角度变化曲线", font=("SimHei", 10, "bold"))
            self.angle_canvas.create_text(30, height / 2, text=f"{max_angle:.1f}°", font=("SimHei", 8))
            self.angle_canvas.create_text(30, height - 20, text=f"{min_angle:.1f}°", font=("SimHei", 8))

        # 阻力曲线
        self.resistance_canvas.delete("all")
        if len(self.resistance_history) >= 2:
            min_resistance = min(self.resistance_history)
            max_resistance = max(self.resistance_history)
            range_resistance = max_resistance - min_resistance if max_resistance != min_resistance else 1

            width = self.resistance_canvas.winfo_width() or 850
            height = self.resistance_canvas.winfo_height() or 180
            x_step = width / (len(self.resistance_history) - 1)

            # 绘制背景网格
            for i in range(5):
                y = i * height / 4
                self.resistance_canvas.create_line(0, y, width, y, fill="#e0e0e0", dash=(2, 2))

            # 绘制曲线
            points = []
            for i in range(len(self.resistance_history)):
                x = i * x_step
                y = height - ((self.resistance_history[i] - min_resistance) / range_resistance) * (height - 20)
                points.extend([x, y])

            # 创建平滑曲线
            if len(points) >= 4:
                self.resistance_canvas.create_line(points, fill=self.secondary_color, width=2, smooth=True)

            # 添加标题和坐标轴
            self.resistance_canvas.create_text(width / 2, 15, text="阻力变化曲线", font=("SimHei", 10, "bold"))
            self.resistance_canvas.create_text(30, height / 2, text=f"{max_resistance:.1f}", font=("SimHei", 8))
            self.resistance_canvas.create_text(30, height - 20, text=f"{min_resistance:.1f}", font=("SimHei", 8))

        self.root.after(500, self.update_plots)

    def save_ff_config(self):
        """保存力反馈配置"""
        self.ff_gain = self.gain_var.get()
        self.ff_deadzone = self.deadzone_var.get()
        self.gain_value_label.config(text=f"{self.ff_gain:.1f}")
        self.deadzone_value_label.config(text=f"{self.ff_deadzone}")
        messagebox.showinfo("提示", "力反馈配置已保存")

    def save_game_config(self):
        """保存游戏配置"""
        selected_game = self.game_var.get()
        enable_ff = self.enable_ff_var.get()

        # 这里可以添加实际保存配置的代码
        print(f"保存游戏配置: {selected_game}, 力反馈: {'启用' if enable_ff else '禁用'}")

        messagebox.showinfo("提示", f"游戏配置已保存\n游戏: {selected_game}\n力反馈: {'启用' if enable_ff else '禁用'}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MotorGameGUI(root)
    root.mainloop()