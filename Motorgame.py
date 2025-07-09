import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, Canvas, messagebox
import time
import pyvjoy  # 使用 pyvjoy 替代 vjoy-python


class MotorGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AT8236电机-游戏映射工具")
        self.root.geometry("800x600")

        # 串口/游戏控制变量
        self.ser = None
        self.is_connected = False
        self.vjoy_device = pyvjoy.VJoyDevice(1)  # 初始化 pyvjoy 设备
        self.current_angle = 0.0  # 当前角度（来自 ESP32）
        self.target_resistance = 0.0  # 目标阻力

        # 角度历史数据（用于曲线）
        self.angle_history = []
        self.max_history = 200

        # 创建 UI
        self.create_widgets()
        self.refresh_ports()

        # 启动数据接收
        self.root.after(100, self.receive_data)
        self.root.after(500, self.update_plot)

    def create_widgets(self):
        # 1. 串口设置区（参考文档2中D157B模块串口通信）
        port_frame = ttk.LabelFrame(self.root, text="串口配置")
        port_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Label(port_frame, text="串口号：").grid(row=0, column=0, padx=5, pady=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, width=10)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(port_frame, text="刷新", command=self.refresh_ports).grid(row=0, column=2, padx=5, pady=5)
        self.connect_btn = ttk.Button(port_frame, text="连接", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=3, padx=5, pady=5)

        # 2. 阻力控制区（对应文档3中AT8236电流控制）
        resistance_frame = ttk.LabelFrame(self.root, text="阻力设置（0-100）")
        resistance_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Label(resistance_frame, text="阻力值：").grid(row=0, column=0, padx=5, pady=10)
        self.resistance_var = tk.StringVar(value="0")
        self.resistance_entry = ttk.Entry(resistance_frame, textvariable=self.resistance_var, width=10)
        self.resistance_entry.grid(row=0, column=1, padx=5, pady=10)

        ttk.Button(resistance_frame, text="发送", command=self.send_resistance).grid(row=0, column=2, padx=5, pady=10)

        # 3. 角度显示区（基于文档1中编码器角度计算）
        angle_frame = ttk.LabelFrame(self.root, text="实时角度（相对初始化位置）")
        angle_frame.pack(padx=10, pady=5, fill=tk.X)

        self.angle_var = tk.StringVar(value="0.00 度")
        ttk.Label(angle_frame, textvariable=self.angle_var, font=("Arial", 18)).pack(pady=10)

        # 4. 角度曲线区
        curve_frame = ttk.LabelFrame(self.root, text="角度变化曲线")
        curve_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.canvas = Canvas(curve_frame, width=750, height=200, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def toggle_connection(self):
        if self.is_connected:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.is_connected = False
            self.connect_btn.config(text="连接")
            messagebox.showinfo("提示", "串口已断开")
        else:
            try:
                port = self.port_var.get()
                self.ser = serial.Serial(port, 115200, timeout=0.1)  # 波特率与ESP32一致
                self.is_connected = True
                self.connect_btn.config(text="断开")
                messagebox.showinfo("提示", f"已连接到 {port}")
            except Exception as e:
                messagebox.showerror("错误", f"连接失败：{str(e)}")

    def send_resistance(self):
        if not self.is_connected:
            messagebox.showwarning("警告", "请先连接串口")
            return
        try:
            resistance = float(self.resistance_var.get())
            if 0 <= resistance <= 100:
                cmd = f"R:{resistance:.1f}\n"  # 与ESP32约定的指令格式
                self.ser.write(cmd.encode('utf-8'))
                self.target_resistance = resistance
            else:
                messagebox.showwarning("警告", "阻力值需在0-100之间")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def receive_data(self):
        if self.is_connected and self.ser:
            try:
                data = self.ser.readline().decode('utf-8').strip()
                if data.startswith("A:"):
                    self.current_angle = float(data[2:])
                    self.angle_var.set(f"{self.current_angle:.2f} 度")
                    # 记录历史数据
                    self.angle_history.append(self.current_angle)
                    if len(self.angle_history) > self.max_history:
                        self.angle_history.pop(0)
                    # 发送到游戏（使用pyvjoy）
                    self.send_to_game(self.current_angle)
            except Exception as e:
                pass  # 忽略临时通信错误
        self.root.after(100, self.receive_data)  # 持续接收

    def send_to_game(self, angle):
        """将角度映射为vJoy设备的X轴值（游戏方向盘输入）"""
        # pyvjoy 值范围：0（最小）- 16384（中值）- 32768（最大）
        # 角度范围：-180度（左）- 0度（中）- 180度（右）
        mapped_value = 16384 + int((angle / 180.0) * 16384)
        mapped_value = max(0, min(32768, mapped_value))  # 确保在有效范围内
        self.vjoy_device.set_axis(pyvjoy.HID_USAGE_X, mapped_value)

    def update_plot(self):
        """更新角度变化曲线"""
        self.canvas.delete("all")
        if len(self.angle_history) < 2:
            self.root.after(500, self.update_plot)
            return

        # 计算坐标范围
        min_angle = min(self.angle_history)
        max_angle = max(self.angle_history)
        range_angle = max_angle - min_angle if max_angle != min_angle else 1

        # 绘制曲线
        width = self.canvas.winfo_width() or 750
        height = self.canvas.winfo_height() or 200
        x_step = width / (len(self.angle_history) - 1)

        for i in range(1, len(self.angle_history)):
            x1 = (i - 1) * x_step
            y1 = height - ((self.angle_history[i - 1] - min_angle) / range_angle) * (height - 20)
            x2 = i * x_step
            y2 = height - ((self.angle_history[i] - min_angle) / range_angle) * (height - 20)
            self.canvas.create_line(x1, y1, x2, y2, fill="blue", width=2)

        self.root.after(500, self.update_plot)


if __name__ == "__main__":
    root = tk.Tk()
    app = MotorGameGUI(root)
    root.mainloop()