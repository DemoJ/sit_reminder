# 久坐提醒器 (Sit Reminder)

一个简单的久坐提醒工具，帮助你保持健康的工作节奏。

## 快速开始

### 方式1：直接使用（推荐）
1. 从目录中下载 `sit_reminder.exe`
2. 双击运行即可，无需安装任何依赖

### 方式2：从源码运行

## 功能特点

- 自定义工作和休息时间
- 桌面悬浮显示倒计时（可拖动位置）
- 系统托盘运行
- 自动保存设置
- 状态实时显示

## 使用说明

1. 设置工作和休息时间
   - 工作时间：1-120分钟（默认45分钟）
   - 休息时间：1-30分钟（默认5分钟）

2. 桌面显示
   - 勾选"在桌面显示倒计时"可以在桌面显示悬浮窗口
   - 可以用鼠标拖动悬浮窗口到任意位置
   - 显示当前状态和剩余时间
   - 单击桌面计时器可切换开始/暂停
   - 双击桌面计时器可显示主窗口

3. 托盘功能
   - 点击右上角关闭按钮只会隐藏窗口，程序继续在后台运行
   - 右键点击托盘图标可以：
     * 显示主窗口
     * 完全退出程序

4. 状态提示
   - ⌛ 工作中
   - ☕ 休息时间
   - ⏹️ 已停止
   - ✅ 准备就绪

## 运行环境

### 打包版本
- Windows 10/11
- 无需安装任何依赖

### 源码版本
- Python 3.6+
- PySide6

#### 安装依赖

    pip install PySide6

#### 启动程序

    python sit_reminder.py

### 配置文件

程序会自动创建 sit_reminder_settings.json 保存你的设置，包括：
- 工作时间
- 休息时间
- 桌面显示开关状态

