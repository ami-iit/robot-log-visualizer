# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

from typing import Any, Dict, List

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

    def clear_canvas(self) -> None:
        self.canvas.clear_curves()

    def capture_canvas_state(self) -> Dict[str, Any]:
        return self.canvas.capture_state()

    def apply_canvas_state(self, state: Dict[str, Any]) -> List[str]:
        if not state:
            return []

        self.canvas.apply_view_range(state.get("view_range", []))
        self.canvas.set_legend_visible(state.get("legend_visible", True))
        self.canvas.apply_curve_metadata(state.get("curves", {}))
        return self.canvas.restore_annotations(state.get("annotations", []))
