# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

from qtpy.QtWidgets import QFrame

from robot_log_visualizer.plotter.pyqtgraph_viewer_canvas import PyQtGraphViewerCanvas
from robot_log_visualizer.ui.ui_loader import load_ui


class PlotItem(QFrame):
    def __init__(self, period):
        super().__init__(None)
        self.ui = load_ui("plot_tab.ui", self)
        self.canvas = PyQtGraphViewerCanvas(parent=self, period=period)
        self.ui.plotLayout.addWidget(self.canvas)

    def set_signal_provider(self, signal_provider):
        self.canvas.set_signal_provider(signal_provider)
