try:
    import datetime
    from multiprocessing import Manager, Process, Queue
    import os.path
    import sys
    from typing import List, Optional

    # noinspection Mypy
    from redvox.cloud.client import cloud_client, CloudClient

    # noinspection Mypy
    from redvox.cloud.config import RedVoxConfig

    # noinspection Mypy
    from redvox.cloud.data_api import DataRangeReqType

    # noinspection PyPackageRequirements
    import PySide6.QtCore

    # noinspection PyPackageRequirements
    from PySide6.QtGui import QIntValidator

    # noinspection PyPackageRequirements
    from PySide6 import QtWidgets

    # noinspection PyPackageRequirements
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QDateTimeEdit,
        QDialog,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QRadioButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    class WindowSelectionWidget(QWidget):
        def __init__(self, parent=None):
            super(WindowSelectionWidget, self).__init__(parent)

            self.start_dt: QDateTimeEdit = QDateTimeEdit()
            self.end_dt: QDateTimeEdit = QDateTimeEdit()

            now: datetime.datetime = datetime.datetime.now()
            fifteen_minutes_ago: datetime.datetime = now - datetime.timedelta(
                minutes=15
            )
            date_fmt: str = "yyyy-MM-dd HH:mm UTC"

            self.start_dt.setDisplayFormat(date_fmt)
            self.start_dt.setTimeSpec(PySide6.QtCore.Qt.UTC)
            self.end_dt.setDisplayFormat(date_fmt)
            self.end_dt.setTimeSpec(PySide6.QtCore.Qt.UTC)
            self.start_dt.setCalendarPopup(True)
            self.end_dt.setCalendarPopup(True)
            self.start_dt.setDateTime(fifteen_minutes_ago)
            self.end_dt.setDateTime(now)

            layout: QHBoxLayout = QHBoxLayout()

            layout.addWidget(QLabel("Start"))
            layout.addWidget(self.start_dt)
            layout.addWidget(QLabel("End"))
            layout.addWidget(self.end_dt)

            self.setLayout(layout)

        def validate(self) -> List[str]:
            errors: List[str] = []
            if self.start_dt.dateTime() >= self.end_dt.dateTime():
                errors.append(
                    "Start of time window must be strictly less than end of time window"
                )
            return errors

    def empty_text(s: str) -> bool:
        return s.strip() == ""

    class ServerSelectionWidget(QWidget):
        def __init__(self, redvox_config: Optional[RedVoxConfig], parent=None):
            super(ServerSelectionWidget, self).__init__(parent)

            int_validator = QIntValidator()

            self.https: QRadioButton = QRadioButton()
            self.https.setText("HTTPS")
            self.http: QRadioButton = QRadioButton()
            self.http.setText("HTTP")

            self.host: QLineEdit = QLineEdit()
            self.port: QLineEdit = QLineEdit()
            self.port.setValidator(int_validator)

            self.timeout: QLineEdit = QLineEdit()
            self.retries: QLineEdit = QLineEdit()

            self.timeout.setValidator(int_validator)
            self.retries.setValidator(int_validator)

            self.disable_timing_correction: QCheckBox = QCheckBox()

            if redvox_config is not None:
                self.host.setText(redvox_config.host)
                self.port.setText(str(redvox_config.port))
                if redvox_config.protocol == "http":
                    self.http.setChecked(True)
                else:
                    self.https.setChecked(True)
            else:
                self.https.setChecked(True)
                self.host.setText("redvox.io")
                self.port.setText("8080")

            self.timeout.setText("120")
            self.retries.setText("3")

            self.disable_timing_correction.setText("Disable Timing Correction")
            self.disable_timing_correction.setChecked(False)

            layout: QVBoxLayout = QVBoxLayout()
            server_widget: QWidget = QWidget()
            server_options_widget: QWidget = QWidget()
            server_layout: QHBoxLayout = QHBoxLayout()
            server_options_layout: QHBoxLayout = QHBoxLayout()
            server_widget.setLayout(server_layout)
            server_options_widget.setLayout(server_options_layout)

            server_layout.addWidget(QLabel("Protocol"))
            server_layout.addWidget(self.https)
            server_layout.addWidget(self.http)
            server_layout.addWidget(QLabel("Host"))
            server_layout.addWidget(self.host)
            server_layout.addWidget(QLabel("Port"))
            server_layout.addWidget(self.port)

            server_options_layout.addWidget(QLabel("Timeout"))
            server_options_layout.addWidget(self.timeout)
            server_options_layout.addWidget(QLabel("Retries"))
            server_options_layout.addWidget(self.retries)
            server_options_layout.addWidget(self.disable_timing_correction)

            layout.addWidget(server_widget)
            layout.addWidget(server_options_widget)

            self.setLayout(layout)

        def validate(self) -> List[str]:
            errors: List[str] = []
            if empty_text(self.host.text()):
                errors.append("Host must be provided")
            if empty_text(self.port.text()):
                errors.append("Port must be provided")
            if empty_text(self.timeout.text()):
                errors.append("Timeout must be provided")
            if empty_text(self.retries.text()):
                errors.append("Retries must be provided")
            return errors

    class AuthenticationWidget(QWidget):
        def __init__(self, redvox_config: Optional[RedVoxConfig], parent=None):
            super(AuthenticationWidget, self).__init__(parent)

            self.username: QLineEdit = QLineEdit()
            self.password: QLineEdit = QLineEdit()
            self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

            if redvox_config is not None:
                self.username.setText(redvox_config.username)
                self.password.setText(redvox_config.password)

            layout: QHBoxLayout = QHBoxLayout()

            layout.addWidget(QLabel("Username"))
            layout.addWidget(self.username)

            layout.addWidget(QLabel("Password"))
            layout.addWidget(self.password)

            self.setLayout(layout)

        def validate(self) -> List[str]:
            errors: List[str] = []
            if empty_text(self.username.text()):
                errors.append("Username must be provided")
            if empty_text(self.password.text()):
                errors.append("Password must be provided")
            return errors

    class ApiSelectionWidget(QWidget):
        def __init__(self, parent=None):
            super(ApiSelectionWidget, self).__init__(parent)

            self.api_900_1000: QRadioButton = QRadioButton()
            self.api_900_1000.setText("API 900 and 1000")
            self.api_900: QRadioButton = QRadioButton()
            self.api_900.setText("API 900")
            self.api_1000: QRadioButton = QRadioButton()
            self.api_1000.setText("API 1000")

            self.api_900_1000.setChecked(True)

            layout: QHBoxLayout = QHBoxLayout()
            layout.addWidget(self.api_900_1000)
            layout.addWidget(self.api_900)
            layout.addWidget(self.api_1000)

            self.setLayout(layout)

    class OutputDirectoryWidget(QWidget):
        def __init__(self, parent=None):
            super(OutputDirectoryWidget, self).__init__(parent)

            self.output_dir: QLineEdit = QLineEdit()
            self.open_file: QPushButton = QPushButton("Select")

            # noinspection PyUnresolvedReferences
            self.open_file.clicked.connect(self.open_dialog)

            self.output_dir.setText(".")

            layout: QHBoxLayout = QHBoxLayout()
            layout.addWidget(self.output_dir)
            layout.addWidget(self.open_file)

            self.setLayout(layout)

        def open_dialog(self):
            self.output_dir.setText(
                QFileDialog.getExistingDirectory(options=QFileDialog.ShowDirsOnly)
            )

        def validate(self) -> List[str]:
            errors: List[str] = []

            if empty_text(self.output_dir.text()):
                errors.append("Output directory must be set")

            if not os.path.isdir(self.output_dir.text()):
                errors.append("Output directory does not exist")

            return errors

    def download_process(
        redvox_config: RedVoxConfig,
        timeout: int,
        req_start: int,
        req_end: int,
        station_ids: List[str],
        api_type: DataRangeReqType,
        correct_query_timing: bool,
        out_dir: str,
        retries: int,
        out_queue: Queue,
    ):

        try:
            client: CloudClient
            with cloud_client(redvox_config, timeout=float(timeout)) as client:
                resp = client.request_data_range(
                    req_start,
                    req_end,
                    station_ids,
                    api_type,
                    correct_query_timing,
                    out_queue=out_queue,
                )
                resp.download_fs(out_dir, retries, out_queue=out_queue)
        except Exception as e:
            out_queue.put(f"Encountered an error: {e}")
            out_queue.put("done")

    class DataDownloadGui(QDialog):
        def __init__(self, parent=None):
            super(DataDownloadGui, self).__init__(parent)
            self.setWindowTitle("RedVox Cloud Data Downloader")
            self.setMinimumWidth(1600)
            self.setMinimumHeight(900)

            redvox_config: Optional[RedVoxConfig] = RedVoxConfig.find()

            self.authentication_widget: AuthenticationWidget = AuthenticationWidget(
                redvox_config
            )
            self.server_selection_widget: ServerSelectionWidget = ServerSelectionWidget(
                redvox_config
            )
            self.window_selection_widget: WindowSelectionWidget = (
                WindowSelectionWidget()
            )
            self.station_ids_widget: QTextEdit = QTextEdit()
            self.api_selection_widget: ApiSelectionWidget = ApiSelectionWidget()
            self.output_directory_widget: OutputDirectoryWidget = (
                OutputDirectoryWidget()
            )
            self.download_data_btn: QPushButton = QPushButton("Download Data")
            # noinspection PyUnresolvedReferences
            self.download_data_btn.clicked.connect(self.download_data)

            self.log: QTextEdit = QTextEdit()
            self.log.setReadOnly(True)
            self.info = lambda msg: self.log.append(
                f"{datetime.datetime.utcnow()}: {msg}"
            )

            layout: QVBoxLayout = QVBoxLayout()

            layout.addWidget(QLabel("RedVox Authentication"))
            layout.addWidget(self.authentication_widget)

            layout.addWidget(QLabel("Server Selection"))
            layout.addWidget(self.server_selection_widget)

            layout.addWidget(QLabel("Data Window Selection"))
            layout.addWidget(self.window_selection_widget)

            layout.addWidget(QLabel("Station IDs (one per line)"))
            layout.addWidget(self.station_ids_widget)

            layout.addWidget(QLabel("API Selection"))
            layout.addWidget(self.api_selection_widget)

            layout.addWidget(QLabel("Output Directory"))
            layout.addWidget(self.output_directory_widget)

            layout.addWidget(self.download_data_btn)

            layout.addWidget(QLabel("Log"))
            layout.addWidget(self.log)

            self.setLayout(layout)

        def download_data(self):
            validation_errors: List[str] = self.validate()
            if len(validation_errors) > 0:
                self.info("Errors encountered")
                for error in validation_errors:
                    self.info(error)
                return

            username: str = self.authentication_widget.username.text()
            password: str = self.authentication_widget.password.text()
            protocol: str
            if self.server_selection_widget.https.isChecked():
                protocol = "https"
            else:
                protocol = "http"
            host: str = self.server_selection_widget.host.text()
            port: int = int(self.server_selection_widget.port.text())
            out_dir: str = self.output_directory_widget.output_dir.text()
            redvox_config: RedVoxConfig = RedVoxConfig(
                username, password, protocol, host, port
            )
            req_start: int = int(
                self.window_selection_widget.start_dt.dateTime().toSecsSinceEpoch()
            )
            req_end: int = int(
                self.window_selection_widget.end_dt.dateTime().toSecsSinceEpoch()
            )
            station_ids: List[str] = list(map(str.strip, self.station_ids_widget.toPlainText().splitlines(
                False
            )))
            api_type: DataRangeReqType
            if self.api_selection_widget.api_900_1000.isChecked():
                # noinspection PyTypeChecker
                api_type = DataRangeReqType.API_900_1000
            elif self.api_selection_widget.api_1000.isChecked():
                # noinspection PyTypeChecker
                api_type = DataRangeReqType.API_1000
            else:
                # noinspection PyTypeChecker
                api_type = DataRangeReqType.API_900

            retries: int = int(self.server_selection_widget.retries.text())
            timeout: int = int(self.server_selection_widget.timeout.text())
            correct_query_timing: bool = (
                not self.server_selection_widget.disable_timing_correction.isChecked()
            )

            manager = Manager()
            out_queue = manager.Queue(1024)

            self.info("Starting data query")

            process = Process(
                target=download_process,
                args=(
                    redvox_config,
                    timeout,
                    req_start,
                    req_end,
                    station_ids,
                    api_type,
                    correct_query_timing,
                    out_dir,
                    retries,
                    out_queue,
                ),
            )

            process.start()

            result: str = ""
            while result != "done":
                # noinspection PyBroadException
                try:
                    result = out_queue.get(block=True, timeout=0.1)
                    self.info(result)
                    QApplication.processEvents()
                except:
                    pass

        def validate(self) -> List[str]:
            errors: List[str] = []

            station_ids: List[str] = self.station_ids_widget.toPlainText().splitlines()
            if len(station_ids) == 0:
                errors.append("At least one station ID must be provided")

            for station_id in station_ids:
                try:
                    int(station_id)
                except ValueError:
                    errors.append(f"{station_id} does not appear to be a valid station")

            for widget in [
                self.window_selection_widget,
                self.authentication_widget,
                self.server_selection_widget,
                self.output_directory_widget,
            ]:
                # noinspection Mypy
                errors.extend(widget.validate())

            return errors

    def run_gui() -> None:
        app = QApplication(sys.argv)
        form = DataDownloadGui()
        form.show()
        sys.exit(app.exec_())

    if __name__ == "__main__":
        run_gui()

except ImportError:
    import warnings

    warnings.warn(
        "GUI dependencies are not installed. Install the 'GUI' extra to enable this functionality."
    )
