import sys
import datetime
from typing import Optional

import numpy as np
from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, \
    QHeaderView, QSizePolicy, QAbstractItemView

import redvox
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api1000.wrapped_redvox_packet.sensors.image import Image


class ImageSelectionWidget(QTableWidget):
    def __init__(self,
                 image_sensor: Image,
                 image_view_widget: 'ImageViewWidget',
                 parent: Optional[QWidget] = None):
        super().__init__(image_sensor.get_num_images(), 2, parent=parent)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resizeColumnsToContents()

        extension: str = image_sensor.get_file_ext()
        timestamps: np.ndarray = image_sensor.get_timestamps().get_timestamps()

        self.setHorizontalHeaderLabels(["File Name", "Image Sampled At"])
        for (i, ts) in enumerate(timestamps):
            name: str = f"{round(ts)}.{extension}"
            dt: datetime.datetime = datetime.datetime.utcfromtimestamp(ts / 1_000_000.0)
            self.setItem(i, 0, QTableWidgetItem(name))
            self.setItem(i, 1, QTableWidgetItem(str(dt)))

        def __update_image_at_row(row: int):
            buf = image_sensor.get_samples()[row]
            image_view_widget.set_image(buf)

        self.cellClicked.connect(lambda r: __update_image_at_row(r))


class ImageViewWidget(QLabel):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent=None)

        self.setAlignment(Qt.AlignCenter)

    def set_image(self, buf: bytes):
        pix = QPixmap()
        pix.loadFromData(buf)
        self.setPixmap(pix.scaled(self.width(),
                                  self.height(),
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation))


class ImageViewer(QWidget):
    def __init__(self, image_sensor: Image, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setLayout(QHBoxLayout(self))

        image_view_widget = ImageViewWidget()
        image_selection_widget = ImageSelectionWidget(image_sensor, image_view_widget)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
        image_selection_widget.setSizePolicy(size_policy)
        self.layout().addWidget(image_selection_widget)

        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(2)
        image_view_widget.setSizePolicy(size_policy)
        self.layout().addWidget(image_view_widget)


class MainWindow(QMainWindow):
    def __init__(self, image_sensor: Image, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"RedVox Image Viewer v{redvox.VERSION}")
        self.setCentralWidget(ImageViewer(image_sensor, self))


def start_gui(image_sensor: Image) -> None:
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow(image_sensor)
    window.showMaximized()
    app.exec_()


if __name__ == "__main__":
    path = "/Users/anthony/data/api_m_image/1637680002_1600191734626184.rdvxm"
    packet = WrappedRedvoxPacketM.from_compressed_path(path)
    start_gui(packet.get_sensors().get_image())
