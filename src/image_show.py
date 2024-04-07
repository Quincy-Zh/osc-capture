from math import fabs
from PySide6.QtWidgets import QWidget, QScrollBar
from PySide6.QtGui import (
    QMouseEvent,
    QPaintEvent,
    QPixmap,
    QImage,
    QResizeEvent,
    QPainter,
    QShowEvent,
    QWheelEvent,
    QColor,
)
from PySide6.QtCore import Qt, QPointF, QSize, QRectF


class ImageWidget(QWidget):
    def __init__(self):
        super().__init__(None)

        self.scrollBarHorizontal = QScrollBar(Qt.Orientation.Horizontal, self)
        self.scrollBarHorizontal.setMinimum(0)
        self.scrollBarHorizontal.setMaximum(100)
        self.scrollBarHorizontal.setValue(30)

        self.scrollBarVertical = QScrollBar(Qt.Orientation.Vertical, self)
        self.scrollBarVertical.setMinimum(0)
        self.scrollBarVertical.setMaximum(100)
        self.scrollBarVertical.setValue(30)

        self.pixmapOrg = QPixmap()
        # self.pixmapOrg.load('res\\a1.png')

        self.scaleValue = 1

        self.pixmapDraw = QPixmap(self.pixmapOrg)

        self.mousePressed = False
        self.mousePos = QPointF()

        # 图像实际绘制
        self.rectShown = QRectF(self.pixmapDraw.rect())

        # 平移图像时的偏移量
        self.deltaX = 0
        self.deltaY = 0

        self.resize(800, 600)

    def fixBound(self, val, picVal, canvasVal):
        # 修正实际绘图区域

        padding = 10

        if val < -padding:
            val = padding
        else:
            if (canvasVal - (picVal - val)) > 10:
                val = picVal + 10 - canvasVal

        return val

    def moveTo(self, pos):
        if not self.mousePressed:
            return

        d = self.mousePos - pos
        self.mousePos = pos

        flag = 0
        dx = int(d.x())
        dy = int(d.y())

        if fabs(dx) > 20:
            self.deltaX = dx
            flag += 1

        if fabs(dy) > 20:
            self.deltaY = int(dy)
            flag += 1

        if flag != 0:
            self.update()
        #

    def showEvent(self, event: QShowEvent) -> None:
        image = QImage(800, 600, QImage.Format_ARGB32)
        image.fill(QColor(200, 200, 200))

        self.pixmapOrg = QPixmap.fromImage(image)

        self.__showPixmap()

        return super().showEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        sz = self.size() - QSize(1, 41)

        xCanvas, yCanvas, wCanvas, hCanvas = 0, 0, sz.width(), sz.height()  # 画布
        xPic, yPic, wPic, hPic = (
            0,
            0,
            self.pixmapDraw.width(),
            self.pixmapDraw.height(),
        )  # 显示的图像区域

        if wCanvas >= wPic:
            # 画布宽度 大于 图像宽度
            xCanvas = (wCanvas - wPic) / 2
            wCanvas = wPic
            self.deltaX = 0
            self.scrollBarHorizontal.setEnabled(False)
        else:
            self.scrollBarHorizontal.setEnabled(True)
            xPic = (wPic - wCanvas) / 2 + self.deltaX
            xPic = self.fixBound(xPic, wPic, wCanvas)

            wPic = wCanvas

        if hCanvas >= hPic:
            # 画布高度 大于 图像高度
            yCanvas = (hCanvas - hPic) / 2
            hCanvas = hPic
            self.deltaY = 0
            self.scrollBarVertical.setEnabled(False)
        else:
            self.scrollBarVertical.setEnabled(True)
            yPic = (hPic - hCanvas) / 2 + self.deltaY
            yPic = self.fixBound(yPic, hPic, hCanvas)

            hPic = hCanvas

        target = QRectF(xCanvas, yCanvas, wCanvas, hCanvas)
        source = QRectF(xPic, yPic, wPic, hPic)

        painter.drawPixmap(target, self.pixmapDraw, source)

        painter.drawText(8, 16, "Scale: {:0.1f}".format(self.scaleValue))

        self.scrollBarVertical.setGeometry(self.width() - 20, 0, 20, self.height() - 20)
        self.scrollBarHorizontal.setGeometry(
            0, self.height() - 20, self.width() - 20, 20
        )

        return super().paintEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        old = event.oldSize()
        curr = event.size()
        r1 = curr.width() / curr.width()
        r2 = curr.height() / old.height()

        if fabs(r1) > fabs(r2):
            r1 = r2

        s = self.scaleValue * (1 + r1)

        self.update()

        return super().resizeEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:

        val = event.angleDelta().y()

        if val > 0:
            self.scaleValue += 0.1

            if self.scaleValue > 10:
                self.scaleValue = 10
        elif val < 0:
            self.scaleValue -= 0.1

            if self.scaleValue < 0.1:
                self.scaleValue = 0.1
        else:
            return

        sz = self.pixmapOrg.size() * self.scaleValue

        self.pixmapDraw = self.pixmapOrg.scaled(sz, Qt.AspectRatioMode.KeepAspectRatio)
        self.rectShown = QRectF(self.pixmapDraw.rect())

        self.update()

        return super().wheelEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.mousePressed:
            self.moveTo(event.position())
            self.mousePressed = False
        return super().mouseReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.mousePressed = True
        self.mousePos = event.position()

        return super().mousePressEvent(event)

    def showImage(self, filepath):
        # 显示图像

        self.pixmapOrg.load(filepath)

        self.__showPixmap()

    def __showPixmap(self):

        # 按当前窗口尺寸，缩放图像
        padding = 30
        sz = self.size()
        w = sz.width() - padding
        h = sz.height() - padding

        rw = w / self.pixmapOrg.width()
        rh = h / self.pixmapOrg.height()

        if rw > rh:
            rw = rh

        self.scaleValue = int(rw * 100) / 100

        self.pixmapDraw = self.pixmapOrg.scaled(
            rw * self.pixmapOrg.width(),
            rw * self.pixmapOrg.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        self.rectShown = self.pixmapDraw.rect()

        self.update()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = ImageWidget()
    w.show()

    app.exec()
