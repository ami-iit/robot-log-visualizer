from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
from robot_log_visualizer.plotter.color_palette import ColorPalette

class PyQtGraphViewerCanvas(QtWidgets.QWidget):
    def __init__(self, parent, signal_provider, period):
        """
        Initialize the PyQtGraphViewerCanvas.
        Parameters:
            parent (QWidget): The parent widget.
            signal_provider (SignalProvider): The signal provider for data.
            period (float): The update period in seconds.
        """
        super().__init__(parent)

        self.signal_provider = signal_provider
        self.period_in_ms = int(period * 1000)

        self.active_paths = {}  # Plotted curves
        self.annotations = []  # Text annotations

        self.layout = QtWidgets.QVBoxLayout(self)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.layout.addWidget(self.plot_widget)

        # Set minimalistic axis labels
        label_style = {"color": "#000000", "font-size": "12pt", "font-weight": "normal"}
        self.plot_widget.setLabel("bottom", "Time [s]", **label_style)
        self.plot_widget.setLabel("left", "Value", **label_style)

        self.plot_widget.showGrid(x=True, y=True)

        self.plot_widget.addLegend(
            offset=(10, 10), labelTextSize="12pt", brush=(255, 255, 255, 150)
        )
        self.plot_widget.plotItem.legend.setParentItem(self.plot_widget.plotItem)
        self.plot_widget.plotItem.legend.anchor((0.0, 0), (0.0, 0))

        # Vertical line for animation (soft gray)
        self.vertical_line = pg.InfiniteLine(
            angle=90, movable=False, pen=pg.mkPen(color="#555555", width=1)
        )
        self.plot_widget.addItem(self.vertical_line)

        # Timer for updating the vertical line
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_vertical_line)
        self.timer.start(self.period_in_ms)

        # Color palette
        self.color_palette = ColorPalette()

        # Interaction
        self.plot_widget.scene().sigMouseClicked.connect(self.on_click)

    def update_plots(self, paths, legends):
        """
        Update plots based on provided data paths and their corresponding legends.

        Parameters:
            paths (list): List of paths representing data series to plot.
            legends (list): Corresponding legend labels for the paths.
        """
        for path, legend in zip(paths, legends):
            path_string = "/".join(path)
            legend_string = "/".join(legend[1:])

            if path_string not in self.active_paths:
                data = self.signal_provider.data
                for key in path[:-1]:
                    data = data[key]
                try:
                    datapoints = data["data"][:, int(path[-1])]
                except IndexError:
                    datapoints = data["data"][:]

                timestamps = data["timestamps"] - self.signal_provider.initial_time
                color = self.color_palette(len(self.active_paths))
                curve = self.plot_widget.plot(
                    timestamps,
                    datapoints,
                    pen=pg.mkPen(color=color, width=2),
                    name=legend_string,
                    symbol=None,
                )
                self.active_paths[path_string] = curve
        active_path_strings = {"/".join(path) for path in paths}
        paths_to_remove = [p for p in self.active_paths if p not in active_path_strings]
        for path in paths_to_remove:
            self.plot_widget.removeItem(self.active_paths[path])
            del self.active_paths[path]

        # Set the x-axis range to the full time range of the data
        self.plot_widget.setXRange(
            0, self.signal_provider.end_time - self.signal_provider.initial_time
        )

    def update_vertical_line(self):
        """
        Update the position of the vertical line based on the current time.
        """
        current_time = self.signal_provider.current_time
        self.vertical_line.setValue(current_time)

    def on_click(self, event):
        """
        Handle mouse click events to add annotations to the plot.
        Clicking on a data point will display its coordinates.
        """
        pos = event.scenePos()
        if self.plot_widget.sceneBoundingRect().contains(pos):
            # Convert scene coordinates to plot coordinates
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x_click, y_click = mouse_point.x(), mouse_point.y()

            closest_curve, closest_point, min_dist = None, None, float("inf")

            for curve in self.active_paths.values():
                xdata, ydata = curve.getData()
                distances = np.sqrt((xdata - x_click) ** 2 + (ydata - y_click) ** 2)
                index = np.argmin(distances)
                distance = distances[index]
                if distance < min_dist:
                    min_dist = distance
                    closest_curve = curve
                    closest_point = (xdata[index], ydata[index])

            # If the closest point is within a certain distance, add an annotation
            if min_dist < 0.01 * (
                self.plot_widget.viewRange()[0][1] - self.plot_widget.viewRange()[0][0]
            ):
                text = f"{closest_point[0]:.3f}, {closest_point[1]:.3f}"
                annotation = pg.TextItem(
                    text,
                    anchor=(0, 1),
                    color="#000000"
                )
                annotation.setPos(*closest_point)
                self.plot_widget.addItem(annotation)
                self.annotations.append(annotation)

    def clear_annotations(self):
        """
        Clear all annotations from the plot.
        """
        for annotation in self.annotations:
            self.plot_widget.removeItem(annotation)
        self.annotations.clear()

    def quit_animation(self):
        """
        Stop the animation and clear all plots.
        """
        self.timer.stop()

    def pause_animation(self):
        """
        Pause the animation by stopping the timer.
        """
        self.timer.stop()

    def resume_animation(self):
        """
        Resume the animation by restarting the timer.
        """
        self.timer.start(self.period_in_ms)
