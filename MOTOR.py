"""
上位机程序（Windows）- 修正版
功能：通过串口发送阻力指令（0-100），接收并显示电机角度
修复内容：统一使用pack布局管理器，解决布局冲突
"""

import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox

class MotorControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("电机阻力控制与角度监测")
        self.root.geometry("400x300")

        # 串口初始化
        self.ser = None
        self.is_connected = False

        # 创建UI组件
        self.create_widgets()

        # 角度数据缓存
        self.current_angle = 0.0

    def create_widgets(self):
        # 串口选择区域
        port_frame = ttk.LabelFrame(self.root, text="串口设置")
        port_frame.pack(padx=10, pady=5, fill=tk.X)

        # 串口框架内部使用frame+pack避免grid冲突
        port_inner = ttk.Frame(port_frame)
        port_inner.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(port_inner, text="串口号：").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_inner, textvariable=self.port_var, width=10)
        self.port_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(port_inner, text="刷新", command=self.refresh_ports).pack(side=tk.LEFT, padx=5)
        self.connect_btn = ttk.Button(port_inner, text="连接", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        # 阻力控制区域
        control_frame = ttk.LabelFrame(self.root, text="阻力控制")
        control_frame.pack(padx=10, pady=5, fill=tk.X)

        control_inner = ttk.Frame(control_frame)
        control_inner.pack(fill=tk.X, padx=5, pady=10)

        ttk.Label(control_inner, text="阻力值（0-100）：").pack(side=tk.LEFT, padx=5)
        self.resistance_var = tk.StringVar(value="0")
        self.resistance_entry = ttk.Entry(control_inner, textvariable=self.resistance_var, width=10)
        self.resistance_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_inner, text="设置阻力", command=self.send_resistance).pack(side=tk.LEFT, padx=5)

        # 角度显示区域
        angle_frame = ttk.LabelFrame(self.root, text="角度反馈")
        angle_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        ttk.Label(angle_frame, text="当前角度（度）：").pack(pady=10)
        self.angle_var = tk.StringVar(value="0.00")
        ttk.Label(angle_frame, textvariable=self.angle_var, font=("Arial", 24)).pack(pady=20)

        # 初始刷新端口
        self.refresh_ports()

    def refresh_ports(self):
        """刷新可用串口号"""
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def toggle_connection(self):
        """连接/断开串口"""
        if self.is_connected:
            # 断开连接
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.is_connected = False
            self.connect_btn.config(text="连接")
            messagebox.showinfo("提示", "串口已断开")
        else:
            # 建立连接
            try:
                port = self.port_var.get()
                self.ser = serial.Serial(
                    port=port,
                    baudrate=115200,
                    timeout=0.1
                )
                self.is_connected = True
                self.connect_btn.config(text="断开")
                messagebox.showinfo("提示", f"已连接到 {port}")
                # 启动接收线程
                self.root.after(100, self.receive_data)
            except Exception as e:
                messagebox.showerror("错误", f"连接失败：{str(e)}")

    def send_resistance(self):
        """发送阻力指令到ESP32"""
        if not self.is_connected:
            messagebox.showwarning("警告", "请先连接串口")
            return

        try:
            resistance = float(self.resistance_var.get())
            if 0 <= resistance <= 100:
                # 发送格式："R:XXX\n"
                cmd = f"R:{resistance:.1f}\n"
                self.ser.write(cmd.encode('utf-8'))
            else:
                messagebox.showwarning("警告", "阻力值必须在0-100之间")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def receive_data(self):
        """接收ESP32发送的角度数据"""
        if self.is_connected and self.ser and self.ser.is_open:
            try:
                data = self.ser.readline().decode('utf-8').strip()
                if data.startswith("A:"):
                    # 解析角度（格式："A:XXX.XX"）
                    angle_str = data[2:]
                    self.current_angle = float(angle_str)
                    self.angle_var.set(f"{self.current_angle:.2f}")
            except Exception as e:
                pass

        # 循环调用（每100ms接收一次）
        self.root.after(100, self.receive_data)

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorControlGUI(root)
    root.mainloop()