#
from datetime import datetime
from PySide6.QtGui import QImage, QPainter, QFont, QColor


def get_filepath() -> tuple[str, str]:
    """把当前时戳转换为文件名和时间字符串
    """
    n = datetime.now()
    filename = n.strftime("%Y%m%d_%H%M%S_%f")
    ts = n.strftime("%Y-%m-%dT%H:%M:%S")

    return (filename, ts)


def addWaterMark(filepath, txt, x=5, y=5, angle=90) -> bool:
    """添加水印"""
    img = QImage()

    if not img.load(filepath):
        return False

    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setFont(QFont(["Consolas", "Courier", "Arial"], 10))
    painter.setPen(QColor(255, 255, 255, 128))
    painter.translate(x, y)
    painter.rotate(angle)
    painter.drawText(0, 0, txt)

    painter.end()

    img.save(filepath)

    return True
