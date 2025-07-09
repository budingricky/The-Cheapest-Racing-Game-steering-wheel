# The-Cheapest-Racing-Game-steering-wheel
# RickyTech™️ 力反馈控制系统

![RickyTech Logo](https://via.placeholder.com/150x50?text=RickyTech™️)

一个功能完整的力反馈控制系统，支持串口通信与ESP32设备连接，提供手动和自动两种控制模式，适用于游戏、模拟训练等场景。

## 功能特点

- **双模式控制**：支持手动控制和游戏力反馈自动控制两种模式
- **实时数据监控**：实时显示角度和阻力数据，并通过曲线图可视化数据变化
- **参数可配置**：支持力反馈增益、死区范围等参数自定义配置
- **多游戏支持**：适配赛车游戏、飞行模拟、驾驶模拟等多种游戏类型
- **完善的日志系统**：记录系统操作和状态变化，支持日志过滤、导出和清空
- **开发者模式**：提供高级调试功能，需密码验证（默认密码：admin）

## 界面预览

![界面预览](https://via.placeholder.com/800x500?text=RickyTech+力反馈控制系统界面)

## 安装与使用

### 前置条件

- Python 3.7+
- 所需依赖库：`pyserial`

### 安装步骤

1. 克隆本仓库：
   ```bash
   git clone https://github.com/yourusername/rickytech-force-feedback.git
   cd rickytech-force-feedback
   ```

2. 安装依赖：
   ```bash
   pip install pyserial
   ```

3. 运行程序：
   ```bash
   python main.py
   ```

### 使用指南

1. **设备连接**：
   - 选择串口号并点击"连接"按钮与ESP32设备建立连接
   - 可点击"刷新"按钮更新可用串口列表

2. **控制模式**：
   - 手动模式：直接输入阻力值（0-100）并点击"发送"
   - 自动模式：由游戏力反馈数据自动控制阻力值

3. **参数配置**：
   - 在"力反馈配置"页面调整增益和死区参数
   - 在"游戏配置"页面选择游戏类型和力反馈设置

4. **开发者模式**：
   - 勾选导航栏底部的"开发者模式"
   - 输入密码"admin"即可访问高级功能

## 技术架构

- **界面框架**：使用Tkinter构建图形用户界面
- **串口通信**：通过pyserial库与ESP32设备通信
- **数据可视化**：使用Canvas绘制实时数据曲线图
- **多线程**：单独线程处理力反馈数据监听，避免界面卡顿

## 协议说明

与ESP32设备的通信协议：

- 发送阻力值：`R:阻力值\n`（例如：`R:50.0\n`）
- 接收角度数据：`A:角度值\n`（例如：`A:30.5\n`）

## 开发者说明

- 日志文件默认保存为`motor_game_logs.txt`
- 数据导出格式为CSV，默认保存为`motor_data.csv`
- 力反馈功能依赖`vJoyInterface.dll`（需放置在程序目录下）

## 联系我们

- 电子邮箱：buding0401@126.com
- 技术支持：400-123-4567

## 版权信息

© 2025 RickyTech™️ 保留所有权利

---

*RickyTech™️ 保留最终解释权*



# RickyTech™️ Force Feedback Control System

![RickyTech Logo](https://via.placeholder.com/150x50?text=RickyTech™️)

A fully functional force feedback control system that supports serial communication with ESP32 devices, offering both manual and automatic control modes for gaming, simulation training, and other applications.

## Features

- ** Dual Control Modes **: Supports both manual control and automatic game force feedback control
- ** Real-time Data Monitoring **: Displays angle and resistance data in real-time with visual曲线图 visualization
- ** Configurable Parameters **: Allows customization of force feedback gain, dead zone, and other parameters
- ** Multi-game Support **: Compatible with racing games, flight simulators, driving simulations, and more
- ** Comprehensive Logging **: Records system operations and status changes with filtering, export, and clearing capabilities
- ** Developer Mode **: Provides advanced debugging features with password authentication (default password: admin)

## Interface Preview

![Interface Preview](https://via.placeholder.com/800x500?text=RickyTech+Force+Feedback+System+Interface)

## Installation & Usage

### Prerequisites

- Python 3.7+
- Required dependencies: `pyserial`

### Installation Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/rickytech-force-feedback.git
   cd rickytech-force-feedback
   ```

2. Install dependencies:
   ```bash
   pip install pyserial
   ```

3. Run the application:
   ```bash
   python main.py
   ```

### User Guide

1. **Device Connection**:
   - Select a serial port and click the "Connect" button to establish communication with the ESP32 device
   - Click the "Refresh" button to update the list of available serial ports

2. **Control Modes**:
   - Manual Mode: Enter resistance value (0-100) directly and click "Send"
   - Automatic Mode: Resistance is controlled automatically by game force feedback data

3. **Parameter Configuration**:
   - Adjust gain and dead zone parameters in the "Force Feedback Configuration" page
   - Select game type and force feedback settings in the "Game Configuration" page

4. **Developer Mode**:
   - Check "Developer Mode" at the bottom of the navigation bar
   - Enter password "admin" to access advanced features

## Technical Architecture

- **Interface Framework**: Built with Tkinter for graphical user interface
- **Serial Communication**: Uses pyserial library for communication with ESP32
- **Data Visualization**: Implements real-time data曲线图 using Canvas
- **Multi-threading**: Separate thread for force feedback data monitoring to prevent interface lag

## Protocol Specification

Communication protocol with ESP32 device:

- Sending resistance value: `R:resistance_value\n` (e.g., `R:50.0\n`)
- Receiving angle data: `A:angle_value\n` (e.g., `A:30.5\n`)

## Developer Notes

- Logs are saved to `motor_game_logs.txt` by default
- Exported data is in CSV format, saved to `motor_data.csv` by default
- Force feedback functionality depends on `vJoyInterface.dll` (must be placed in the program directory)

## Contact Us

- Email: buding0401@126.com
- Technical Support: 400-123-4567

## Copyright Information

© 2025 RickyTech™️ All Rights Reserved

---

*RickyTech™️ reserves the right of final interpretation*
