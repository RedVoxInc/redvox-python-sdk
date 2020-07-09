from typing import Optional, List, Any

from PySide2.QtCharts import QtCharts
from PySide2.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem


class ValuesWidget(QTableWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(["value"])

    def update_from_values(self, values: List[Any]) -> None:
        self.clear()
        self.setRowCount(len(values))
        self.setHorizontalHeaderLabels(["value"])
        for i, v in enumerate(values):
            self.setItem(i, 0, QTableWidgetItem(str(v)))


class PlotWidget(QtCharts.QChartView):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

    def update_from_values(self, values: List[float]) -> None:
        chart = QtCharts.QChart()
        series = QtCharts.QLineSeries()
        for i, v in enumerate(values):
            series.append(i, v)
        chart.addSeries(series)
        self.setChart(chart)


class PlotAndDetailsColumn(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.values_widget = ValuesWidget(self)
        self.plot_widget = PlotWidget(self)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.plot_widget)
        self.layout().addWidget(self.values_widget)
