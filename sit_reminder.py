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

        self.init_ui()
        self.init_tray()
        self.load_settings()

        # 初始化计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

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
        self.start_button.clicked.connect(self.start_timer)
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
        self.tray_icon.show()

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

    def start_timer(self):
        self.work_time = self.work_spinbox.value()
        self.rest_time = self.rest_spinbox.value()
        self.remaining_time = self.work_time * 60
        self.is_resting = False
        self.timer.start(1000)  # 每秒更新一次
        self.save_settings()
        self.update_status()

    def stop_timer(self):
        self.timer.stop()
        self.time_label.setText("00:00")
        self.status_label.setText("已停止")

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

    def update_status(self):
        status = "休息中" if self.is_resting else "工作中"
        self.status_label.setText(status)

    def toggle_desktop_display(self, state):
        self.show_on_desktop = bool(state)
        if self.show_on_desktop:
            self.show()
        else:
            self.hide()
        self.save_settings()

    def save_settings(self):
        settings = {
            "work_time": self.work_time,
            "rest_time": self.rest_time,
            "show_on_desktop": self.show_on_desktop,
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
        except FileNotFoundError:
            pass

    def closeEvent(self, event):
        if self.show_on_desktop:
            event.accept()
        else:
            event.ignore()
            self.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SitReminder()
    window.show()
    sys.exit(app.exec())
