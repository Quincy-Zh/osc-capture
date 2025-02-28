#

import os
import sys
import shutil
import logging
import tempfile
from logging.handlers import RotatingFileHandler
from typing import Optional
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QLabel,
)
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QFileDialog
from PySide6.QtWidgets import QMenu
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QTimer

from find_device import DialogFindDevice
from capture import Capture
from image_show import ImageWidget

mydir = os.path.dirname(os.path.abspath(__file__))

# 创建一个日志记录器
logger = logging.getLogger("OscCapture")
logger.setLevel(logging.DEBUG)

# 创建一个控制台处理器，并设置级别为 DEBUG
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.DEBUG)

log_filepath = os.path.join(tempfile.gettempdir(), "osc_cap.log")
rotatingFileHandler = RotatingFileHandler(
    log_filepath, maxBytes=1024 * 1024 * 50, backupCount=2, encoding="utf-8"
)
rotatingFileHandler.setLevel(logging.DEBUG)

# 创建一个格式化器并将其添加到处理程序
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

rotatingFileHandler.setFormatter(formatter)
consoleHandler.setFormatter(formatter)

# 将处理程序添加到记录器
logger.addHandler(rotatingFileHandler)
logger.addHandler(consoleHandler)


class MainWindow(QMainWindow):
    winTitle = "示波器截图助手"

    def __init__(self):
        super().__init__()

        self.output_dir = tempfile.mkdtemp(prefix="osc_cap_")
        self.savedImageIndex = 0
        self.setupUi()
        self.capture = Capture(self.output_dir)
        logger.info("output_dir: " + self.output_dir)

        QTimer.singleShot(500, self.do_connect)

    def closeEvent(self, event):
        if (
            self.listWidgetImages.count() > 0
            and self.savedImageIndex != self.listWidgetImages.count()
        ):
            res = QMessageBox.question(
                self,
                "提示",
                "有图像尚未保存，需要保存吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if res == QMessageBox.StandardButton.Yes:
                self.do_save()

        self.capture.disconnect()

        self.clearImages()

    def setupUi(self):
        # menuBar
        ## File
        menu_file = QMenu("文件(&F)")
        self.menuBar().addMenu(menu_file)
        self.actionConnect = menu_file.addAction("连接(&C)")
        menu_file.addSeparator()
        actionExit = menu_file.addAction("退出(&X)")

        ## Edit
        # menu_edit = QMenu('编辑(&E)')
        # self.menuBar().addMenu(menu_edit)

        ## Help
        menu_help = QMenu("帮助(&H)")
        self.menuBar().addMenu(menu_help)
        actionAbout = menu_help.addAction("关于(&A)")
        actionAboutQt = menu_help.addAction("关于 &Qt")

        # Pixmap
        self.imageWidget = ImageWidget()

        # Button
        self.checkBoxInkSaver = QCheckBox("Ink Save")
        self.pushbuttonCapture = QPushButton("截图(&C)")
        self.pushbuttonSave = QPushButton("保存(&S)")

        layout_buttons = QHBoxLayout()
        layout_buttons.addStretch()
        layout_buttons.addWidget(self.checkBoxInkSaver)
        layout_buttons.addWidget(self.pushbuttonCapture)
        layout_buttons.addWidget(self.pushbuttonSave)

        # ListWidget
        self.listWidgetImages = QListWidget()
        self.listWidgetImages.setMaximumHeight(150)
        self.listWidgetImages.setWrapping(False)
        self.listWidgetImages.setFlow(QListWidget.Flow.LeftToRight)
        self.listWidgetImages.setMovement(QListWidget.Movement.Static)
        self.listWidgetImages.setViewMode(QListWidget.ViewMode.IconMode)
        self.listWidgetImages.setIconSize(QSize(128, 128))

        #
        widget = QWidget()
        self.setCentralWidget(widget)

        layout_main = QVBoxLayout(widget)
        layout_main.addWidget(self.imageWidget)
        layout_main.addLayout(layout_buttons)
        layout_main.addWidget(self.listWidgetImages)

        #
        self.labelInfo = QLabel("未连接")
        self.statusBar().addPermanentWidget(self.labelInfo)

        self.listWidgetImages.doubleClicked.connect(self.do_show)
        self.checkBoxInkSaver.checkStateChanged.connect(self.ink_save_changed)
        self.pushbuttonCapture.clicked.connect(self.do_capture)
        self.pushbuttonSave.clicked.connect(self.do_save)
        self.actionConnect.triggered.connect(self.do_connect)
        actionExit.triggered.connect(self.close)
        actionAbout.triggered.connect(self.about)
        actionAboutQt.triggered.connect(self.aboutQt)

        self.setWindowTitle(self.winTitle)
        self.resize(1024, 768)
        iconpath = os.path.join(mydir, "icon.png")
        self.setWindowIcon(QIcon(iconpath))

    def about(self):
        QMessageBox.about(
            self,
            "关于本程序",
            "仪器助手\n\n方便的示波器截图助手，希望给你带来方便\n\nBy Quincy.W(wagnqyfm@foxmail.com)\n\nPower by PySide, Qt",
        )

    def aboutQt(self):
        QMessageBox.aboutQt(self)

    def setCurrentPixmap(self, path):
        self.imageWidget.showImage(path)

    def do_connect(self):
        if self.capture.is_connected():
            self.capture.disconnect()
            self.actionConnect.setText("连接(&C)")
            self.labelInfo.setText("未连接")
            self.setWindowTitle(self.winTitle)

            return

        #
        dlg = DialogFindDevice(self)
        rc = dlg.exec()

        if rc != 1:
            return

        addr, model = dlg.get_result()

        ok, err = self.capture.connect_to(addr, model)
        if not ok:
            QMessageBox.information(self, "错误", "不能连接到设备\n    {}".format(err))
            return

        self.setWindowTitle("{} - {}".format(self.winTitle, model))
        self.labelInfo.setText("已连接：{}".format(model))
        self.actionConnect.setText("断开(&C)")

    def __entry(self):
        self.setCursor(Qt.CursorShape.WaitCursor)
        self.pushbuttonCapture.setText("截图中...")
        self.pushbuttonCapture.setEnabled(False)
        self.pushbuttonSave.setEnabled(False)

    def __leave(self):
        self.pushbuttonCapture.setText("截图(&C)")
        self.pushbuttonCapture.setEnabled(True)
        self.pushbuttonSave.setEnabled(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def ink_save_changed(self):
        if not self.capture.is_connected():
            QMessageBox.information(self, "错误", "尚未连接")
            self.checkBoxInkSaver.setChecked(False)
            return

        if self.checkBoxInkSaver.isChecked():
            res = self.capture.ctrl("INKSAVE:ON")
        else:
            res = self.capture.ctrl("INKSAVE:OFF")

        if res > 0:
            QMessageBox.warning(self, "提示", "设备不支持该命令")
        elif res < 0:
            QMessageBox.critical(self, "错误", "发生错误~")
        else:
            pass

    def do_capture(self):
        if not self.capture.is_connected():
            QMessageBox.information(self, "错误", "尚未连接")
            return

        self.__entry()

        err, path = self.capture.exec()

        if err != "":
            QMessageBox.information(self, "错误", "发生错误：{}".format(err))
        else:
            item = QListWidgetItem()
            basename = os.path.basename(path)
            item.setText(basename)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setIcon(QIcon(path))

            self.setCurrentPixmap(path)
            self.listWidgetImages.addItem(item)

        self.__leave()

    def do_save(self):
        count = self.listWidgetImages.count()
        if count == 0 or count == self.savedImageIndex:
            QMessageBox.information(self, "提示", "没有图片需要保存")
            return

        path = QFileDialog.getExistingDirectory(self, "选取保存的目录", ".")

        if path == "":
            return

        path = path.replace("/", "\\")

        cnt = 0

        for i in range(self.savedImageIndex, count, 1):
            item = self.listWidgetImages.item(i)
            filename = item.text()
            dest = os.path.join(path, filename)
            src = item.data(Qt.ItemDataRole.UserRole)

            try:
                shutil.copy(src, dest)
            except Exception as ex:
                print(ex)

            cnt += 1

        self.savedImageIndex += cnt

    def do_show(self):
        item = self.listWidgetImages.currentItem()
        if item is None:
            return

        self.setCurrentPixmap(item.data(Qt.ItemDataRole.UserRole))

    def clearImages(self):
        for i in range(self.listWidgetImages.count()):
            path = self.listWidgetImages.item(i).data(Qt.ItemDataRole.UserRole)
            try:
                os.remove(path)
            except:
                pass

        os.removedirs(self.output_dir)


def app_entry():
    app = QApplication(sys.argv)
    win = MainWindow()

    win.show()
    app.exec()


if __name__ == "__main__":
    app_entry()
