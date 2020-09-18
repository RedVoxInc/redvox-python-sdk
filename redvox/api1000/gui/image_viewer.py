"""
Provides a basic image gallery for API M image sensors.
"""

import sys
import datetime
from typing import Optional, TYPE_CHECKING

import numpy as np
from PySide2.QtCore import Qt, QByteArray
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, \
    QHeaderView, QSizePolicy, QAbstractItemView

import redvox

if TYPE_CHECKING:
    from redvox.api1000.wrapped_redvox_packet.sensors.image import Image


class ImageSelectionWidget(QTableWidget):
    """
    This widget provides a table view of available images in the packet.
    """

    def __init__(self,
                 image_sensor: 'Image',
                 image_view_widget: 'ImageViewWidget',
                 parent: Optional[QWidget] = None) -> None:
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

        def __update_image_at_row(row: int) -> None:
            buf: bytes = image_sensor.get_samples()[row]
            image_view_widget.set_image(buf)

        self.currentCellChanged.connect(lambda r: __update_image_at_row(r))


class ImageViewWidget(QLabel):
    """
    This widget displays and scales the image
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=None)
        self.setAlignment(Qt.AlignCenter)

    def set_image(self, buf: bytes) -> None:
        """
        Sets the image.
        :param buf: Image bytes to set
        """
        pix: QPixmap = QPixmap()
        pix.loadFromData(QByteArray(buf))
        self.setPixmap(pix.scaled(self.width(),
                                  self.height(),
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation))


class ImageViewer(QWidget):
    """
    Widget that acts as the "main" widget into the application
    """

    def __init__(self, image_sensor: 'Image', parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setLayout(QHBoxLayout(self))

        image_view_widget: ImageViewWidget = ImageViewWidget()
        image_selection_widget: ImageSelectionWidget = ImageSelectionWidget(image_sensor, image_view_widget)
        size_policy: QSizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
        image_selection_widget.setSizePolicy(size_policy)
        self.layout().addWidget(image_selection_widget)

        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(2)
        image_view_widget.setSizePolicy(size_policy)
        self.layout().addWidget(image_view_widget)


class MainWindow(QMainWindow):
    """
    Main window of the application
    """

    def __init__(self, image_sensor: 'Image', parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"RedVox Image Viewer v{redvox.VERSION}")
        self.setCentralWidget(ImageViewer(image_sensor, self))


def start_gui(image_sensor: 'Image') -> None:
    """
    Starts the GUI from the provided image sensor.
    :param image_sensor: Image sensor
    """
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow(image_sensor)
    window.showMaximized()
    app.exec_()
