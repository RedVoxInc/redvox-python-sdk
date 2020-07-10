from datetime import datetime
from typing import Optional, List, Any, Union

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView


class DateTimes:
    def __init__(self, ts_us: List[float]) -> None:
        self.ts_us: List[float] = ts_us

    @staticmethod
    def from_sr(start_ts_us: float, sample_rate: float, cnt: int) -> 'DateTimes':
        sample_interval: float = 1_000_000.0 / sample_rate
        return DateTimes([start_ts_us + sample_interval * i for i in range(cnt)])

    @staticmethod
    def from_ts_ms(ts_ms: List[float]) -> 'DateTimes':
        return DateTimes(list(map(lambda v: v * 1_000.0, ts_ms)))

    @staticmethod
    def from_ts_s(ts_s: List[float]) -> 'DateTimes':
        return DateTimes(list(map(lambda v: v * 1_000_000.0, ts_s)))

    @staticmethod
    def from_dts(dts: List[datetime]) -> 'DateTimes':
        return DateTimes(list(map(lambda dt: dt.timestamp() * 1_000_000.0, dts)))

    def ts_ms(self) -> List[float]:
        return list(map(lambda v: v / 1_000.0, self.ts_us))

    def ts_s(self) -> List[float]:
        return list(map(lambda v: v / 1_000_000.0, self.ts_us))

    def dts(self) -> List[datetime]:
        return list(map(datetime.utcfromtimestamp, self.ts_s()))


class ValuesWidget(QTableWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(["value"])

    def update_from_values(self, values: List[Any], date_times: Optional[DateTimes] = None) -> None:
        self.clear()
        if date_times is None:
            self.setColumnCount(1)
            self.setHorizontalHeaderLabels(["values"])
        else:
            self.setColumnCount(2)
            self.setHorizontalHeaderLabels(["values", "date/time"])
            dts = date_times.dts()
        self.setRowCount(len(values))

        for i, v in enumerate(values):
            self.setItem(i, 0, QTableWidgetItem(str(v)))
            if date_times is not None:
                self.setItem(i, 1, QTableWidgetItem(str(dts[i])))

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)


class PlotWidget(QtCharts.QChartView):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)

    def update_from_values(self, values: List[float], date_times: DateTimes) -> None:
        start_dt: datetime = datetime.utcfromtimestamp(date_times.ts_us[0] / 1_000_000.0)
        chart: QtCharts.QChart = QtCharts.QChart()
        chart.legend().hide()
        chart.setTitle(f"Audio Samples @ {start_dt}")

        axis_x: QtCharts.QDateTimeAxis = QtCharts.QDateTimeAxis()
        axis_x.setFormat("hh:mm:ss")
        axis_x.setTitleText("Date/Time")
        axis_x.setTickCount(5)
        chart.addAxis(axis_x, Qt.AlignBottom)

        series: QtCharts.QLineSeries = QtCharts.QLineSeries()
        ts_s: List[float] = date_times.ts_ms()
        for i, v in enumerate(values):
            series.append(ts_s[i], v)
        chart.addSeries(series)

        axis_y: QtCharts.QValueAxis = QtCharts.QValueAxis()
        axis_y.setTickCount(5)
        axis_y.setTitleText("PCM F32")
        chart.addAxis(axis_y, Qt.AlignLeft)

        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        self.setChart(chart)


class PlotAndDetailsColumn(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.values_widget = ValuesWidget(self)
        self.plot_widget = PlotWidget(self)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.plot_widget)
        self.layout().addWidget(self.values_widget)
