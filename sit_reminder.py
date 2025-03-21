import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QCheckBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QIcon,
    QAction,
    QPixmap,
    QPainter,
    QLinearGradient,
    QColor,
    QBrush,
)

class DesktopTimer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(5, 5, 5, 5)

        self.status_text = QLabel("准备就绪")
        self.status_text.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #2196f3;
                background-color: rgba(255, 255, 255, 180);
                padding: 3px;
                border-radius: 3px;
            }
        """)
        self.time_text = QLabel("00:00")
        self.time_text.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2196f3;
                background-color: rgba(255, 255, 255, 180);
                padding: 5px;
                border-radius: 5px;
            }
        """)

        layout.addWidget(self.status_text, alignment=Qt.AlignCenter)
        layout.addWidget(self.time_text, alignment=Qt.AlignCenter)

        # 初始位置：屏幕右上角
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 150, 10)

        # 用于跟踪鼠标拖动
        self.dragging = False
        self.offset = None
        self.position = None
        
        # 用于检测单击和双击
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.handle_single_click)

    def save_position(self):
        self.position = self.pos()
        return {"x": self.position.x(), "y": self.position.y()}

    def restore_position(self, position):
        if position:
            self.move(position["x"], position["y"])
        else:
            # 默认位置：屏幕右上角
            screen = QApplication.primaryScreen().geometry()
            self.move(screen.width() - 150, 10)

    def update_time(self, time_text):
        self.time_text.setText(time_text)

    def update_status(self, status):
        status_map = {
            "工作中": "⌛ 工作中...",
            "休息中": "☕ 休息时间",
            "已停止": "⏹️ 已停止",
            "准备就绪": "✅ 准备就绪",
            "已暂停": "⏸️ 已暂停",
        }
        self.status_text.setText(status_map.get(status, status))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 如果正在拖动，则不处理点击事件
            if self.dragging:
                return
                
            # 启动点击计时器，用于区分单击和双击
            if self.click_timer.isActive():
                # 如果计时器已经在运行，说明是双击
                self.click_timer.stop()
                self.handle_double_click()
            else:
                # 否则启动计时器，等待可能的第二次点击
                self.click_timer.start(250)  # 250毫秒内的第二次点击被视为双击
            
            # 记录拖动起始位置
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            # 如果移动了一定距离，则取消点击计时器
            if (event.globalPos() - self.mapToGlobal(self.offset)).manhattanLength() > 3:
                self.click_timer.stop()
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        # 保存新位置
        if hasattr(self, "parent_window"):
            self.parent_window.save_settings()

    def handle_single_click(self):
        # 单击切换开始/暂停
        if hasattr(self, "parent_window"):
            self.parent_window.toggle_pause()

    def handle_double_click(self):
        # 双击显示设置面板
        if hasattr(self, "parent_window"):
            self.parent_window.show()
            self.parent_window.activateWindow()


class SitReminder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("久坐提醒")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        # 初始化变量
        self.work_time = 45  # 默认工作时间（分钟）
        self.rest_time = 5  # 默认休息时间（分钟）
        self.show_on_desktop = True
        self.remaining_time = 0
        self.is_resting = False
        self.is_paused = False  # 新增暂停状态变量

        # 初始化计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.desktop_timer = DesktopTimer()
        self.desktop_timer.parent_window = self  # 添加对父窗口的引用
        self.init_ui()
        self.init_tray()
        self.load_settings()

        # 确保在首次运行时也能正确显示桌面计时器
        if self.show_on_desktop:
            self.desktop_timer.show()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 设置区域
        settings_layout = QHBoxLayout()
        work_label = QLabel("工作时间(分钟):")
        self.work_spinbox = QSpinBox()
        self.work_spinbox.setRange(1, 120)
        self.work_spinbox.setValue(self.work_time)

        rest_label = QLabel("休息时间(分钟):")
        self.rest_spinbox = QSpinBox()
        self.rest_spinbox.setRange(1, 30)
        self.rest_spinbox.setValue(self.rest_time)

        settings_layout.addWidget(work_label)
        settings_layout.addWidget(self.work_spinbox)
        settings_layout.addWidget(rest_label)
        settings_layout.addWidget(self.rest_spinbox)

        # 桌面显示选项
        self.desktop_checkbox = QCheckBox("在桌面显示倒计时")
        self.desktop_checkbox.setChecked(self.show_on_desktop)
        self.desktop_checkbox.stateChanged.connect(self.toggle_desktop_display)

        # 控制按钮
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("开始")
        self.start_button.clicked.connect(self.toggle_pause)
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_timer)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)

        # 倒计时显示
        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.time_label.setAlignment(Qt.AlignCenter)

        # 状态显示
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)

        layout.addLayout(settings_layout)
        layout.addWidget(self.desktop_checkbox)
        layout.addLayout(control_layout)
        layout.addWidget(self.time_label)
        layout.addWidget(self.status_label)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)

        # 确保图标文件夹存在
        icons_dir = Path(__file__).parent / "icons"
        icons_dir.mkdir(exist_ok=True)

        # 优先尝试加载PNG图标
        icon_path_png = icons_dir / "clock.png"

        icon = None
        if icon_path_png.exists():
            icon = QIcon(str(icon_path_png))

        if icon and not icon.isNull():
            self.tray_icon.setIcon(icon)
            print("Icon loaded successfully")
        else:
            print("Creating fallback icon")
            self.create_fallback_icon()

        tray_menu = QMenu()
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def create_fallback_icon(self):
        """创建后备图标"""
        icon_pixmap = QPixmap(32, 32)
        icon_pixmap.fill(Qt.transparent)

        painter = QPainter(icon_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(0, 0, 32, 32)
        gradient.setColorAt(0, QColor("#2196f3"))
        gradient.setColorAt(1, QColor("#21cbf3"))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()

        self.tray_icon.setIcon(QIcon(icon_pixmap))

    def toggle_pause(self):
        # 如果计时器未运行，则启动计时器
        if not self.timer.isActive() and not self.is_paused:
            self.start_timer()
            return
            
        # 如果计时器正在运行，则暂停
        if self.timer.isActive():
            self.timer.stop()
            self.is_paused = True
            self.start_button.setText("继续")
            self.status_label.setText("已暂停")
            self.desktop_timer.update_status("已暂停")
        # 如果计时器已暂停，则继续
        else:
            self.timer.start(1000)
            self.is_paused = False
            self.start_button.setText("暂停")
            # 恢复之前的状态显示
            self.update_status()

    def start_timer(self):
        # 如果是从停止状态开始，则重置计时器
        if not self.is_paused:
            self.work_time = self.work_spinbox.value()
            self.rest_time = self.rest_spinbox.value()
            self.remaining_time = self.work_time * 60
            self.is_resting = False
            
        self.timer.start(1000)  # 每秒更新一次
        self.is_paused = False
        self.start_button.setText("暂停")
        self.save_settings()
        self.update_status()

    def stop_timer(self):
        self.timer.stop()
        self.is_paused = False
        self.start_button.setText("开始")
        self.time_label.setText("00:00")
        self.status_label.setText("已停止")
        self.desktop_timer.update_time("00:00")
        self.desktop_timer.update_status("已停止")

    def update_timer(self):
        self.remaining_time -= 1
        if self.remaining_time <= 0:
            if self.is_resting:
                self.is_resting = False
                self.remaining_time = self.work_time * 60
                self.tray_icon.showMessage("休息结束", "该开始工作了！")
            else:
                self.is_resting = True
                self.remaining_time = self.rest_time * 60
                self.tray_icon.showMessage("工作结束", "该休息了！")
            self.update_status()

        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        self.time_label.setText(time_text)
        self.desktop_timer.update_time(time_text)
        self.desktop_timer.update_status(self.status_label.text())

    def update_status(self):
        status = "休息中" if self.is_resting else "工作中"
        self.status_label.setText(status)
        self.desktop_timer.update_status(status)

    def toggle_desktop_display(self, state):
        self.show_on_desktop = bool(state)
        if self.show_on_desktop:
            self.desktop_timer.show()
        else:
            self.desktop_timer.hide()
        self.save_settings()

    def save_settings(self):
        settings = {
            "work_time": self.work_time,
            "rest_time": self.rest_time,
            "show_on_desktop": self.show_on_desktop,
            "timer_position": self.desktop_timer.save_position(),  # 保存位置
        }
        with open("sit_reminder_settings.json", "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open("sit_reminder_settings.json", "r") as f:
                settings = json.load(f)
                self.work_time = settings.get("work_time", self.work_time)
                self.rest_time = settings.get("rest_time", self.rest_time)
                self.show_on_desktop = settings.get(
                    "show_on_desktop", self.show_on_desktop
                )

                self.work_spinbox.setValue(self.work_time)
                self.rest_spinbox.setValue(self.rest_time)
                self.desktop_checkbox.setChecked(self.show_on_desktop)

                # 恢复位置
                timer_position = settings.get("timer_position", None)
                self.desktop_timer.restore_position(timer_position)

                # 非首次运行才自动启动计时器
                QTimer.singleShot(100, self.start_timer)

                # 如果勾选了桌面显示，则不显示主面板
                if self.show_on_desktop:
                    self.hide()
                else:
                    self.show()
        except FileNotFoundError:
            # 首次运行时只显示主面板，不自动开始计时
            self.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SitReminder()
    sys.exit(app.exec())
