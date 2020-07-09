import argparse

import sys
from typing import Optional

from PySide2.QtWidgets import QApplication, QMainWindow, QWidget

import redvox
from redvox.api1000.gui.data_explorer.data_explorer import DataExplorer


class RedvoxGui(QMainWindow):
    def __init__(self, base_dir: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.data_explorer: DataExplorer = DataExplorer(base_dir, self)
        self.setWindowTitle(f"RedVox GUI v{redvox.version()}")
        self.setCentralWidget(self.data_explorer)


def start_gui(base_dir: str) -> None:
    app: QApplication = QApplication(sys.argv)
    window: RedvoxGui = RedvoxGui(base_dir)
    window.showMaximized()
    app.exec_()


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("base_dir")
    args = parser.parse_args()
    start_gui(args.base_dir)


if __name__ == "__main__":
    main()
