# 查找设备

import logging
from typing import Optional
from threading import Thread
import pyvisa
from PySide6.QtWidgets import (
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Signal

from instruments.zds1000 import ZDS

logger = logging.getLogger("OscCapture")


class DialogFindDevice(QDialog):
    modelMap = {"MDO32": "示波器", "MXR208A": "示波器"}
    tableLabels = ("类型", "型号", "厂商", "地址")
    itemFound = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        #
        self.tableWidgetResult = QTableWidget()
        self.pushbuttonFind = QPushButton("搜索(&S)")

        layout_1 = QHBoxLayout()
        layout_1.addStretch()
        layout_1.addWidget(self.pushbuttonFind)

        layout_0 = QVBoxLayout(self)
        layout_0.addWidget(QLabel("设备列表"))
        layout_0.addWidget(self.tableWidgetResult)
        layout_0.addLayout(layout_1)

        self.tableWidgetResult.setColumnCount(len(self.tableLabels))
        self.tableWidgetResult.setHorizontalHeaderLabels(self.tableLabels)
        self.tableWidgetResult.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tableWidgetResult.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tableWidgetResult.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for i, w in enumerate((60, 150, 160, 300)):
            self.tableWidgetResult.setColumnWidth(i, w)

        self.tableWidgetResult.doubleClicked.connect(self.selected)
        self.pushbuttonFind.clicked.connect(self.search)
        self.itemFound.connect(self.item_found)

        self.resize(680, 300)
        self.setWindowTitle("查找设备")

        self.target = ""
        self.model = ""

    def search(self):
        # Clear rows
        while self.tableWidgetResult.rowCount() > 0:
            self.tableWidgetResult.removeRow(0)

        self.pushbuttonFind.setText("搜索中...")
        self.pushbuttonFind.setEnabled(False)

        th = Thread(target=self.proc)
        th.start()

    def item_found(self, txt):
        if txt == "":
            self.pushbuttonFind.setText("搜索(&S)")
            self.pushbuttonFind.setEnabled(True)
            # self.tableWidgetResult.resizeColumnsToContents()

            QMessageBox.information(
                self,
                "提示",
                "搜索完成\n设备数量：{}".format(self.tableWidgetResult.rowCount()),
            )
        else:
            labels = txt.split("|")

            r = self.tableWidgetResult.rowCount()
            self.tableWidgetResult.insertRow(r)

            item = QTableWidgetItem()
            item.setText(labels[0])

            self.tableWidgetResult.setItem(r, 0, item)
            self.tableWidgetResult.setItem(r, 1, QTableWidgetItem(labels[1]))
            self.tableWidgetResult.setItem(r, 2, QTableWidgetItem(labels[2]))
            self.tableWidgetResult.setItem(r, 3, QTableWidgetItem(labels[3]))

    def proc(self):
        try:
            z = ZDS()

            if z.is_device_ready():
                #
                id = "示波器|ZDS1000|ZHIYUAN|123456789"
                self.itemFound.emit(id)
        except Exception as ex:
            logger.warning(ex)
        
        try:
            rm = pyvisa.ResourceManager('@py')

            for res in rm.list_resources():
                err = ""
                model = "?"
                manf = "?"
                try:
                    dev = rm.open_resource(res)
                    model = dev.get_visa_attribute(pyvisa.constants.VI_ATTR_MODEL_NAME)
                    manf = dev.get_visa_attribute(pyvisa.constants.VI_ATTR_MANF_NAME)
                    dev.close()

                    logger.debug("New Entry: {}, {}, {}".format(model, manf, res))

                except pyvisa.errors.VisaIOError as ex:
                    if ex.error_code != pyvisa.constants.VI_ERROR_NSUP_ATTR:
                        err = str(ex)
                except Exception as ex:
                    err = str(ex)

                if len(err) > 0:
                    logger.warning(err)

                if model in self.modelMap:
                    title = self.modelMap[model]
                else:
                    title = "?"

                id = "{0}|{1}|{2}|{3}".format(title, model, manf, res)
                self.itemFound.emit(id)
        except Exception as ex:
            logger.warning(ex)

        self.itemFound.emit("")

    def selected(self):
        items = self.tableWidgetResult.selectedItems()
        if len(items) == 0:
            return

        r = items[0].row()
        model = self.tableWidgetResult.item(r, 0).text()

        if model == "?":
            QMessageBox.critical(self, "错误", "不支持的设备")
            return

        self.target = self.tableWidgetResult.item(r, 3).text()
        self.model = self.tableWidgetResult.item(r, 1).text()

        self.accept()

    def get_result(self):
        # 返回用户选择结果
        # (address, model)
        return (self.target, self.model)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    d = DialogFindDevice()
    rc = d.show()

    app.exec()
