# Copyright (C) 2025 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pyqtgraph as pg  # type: ignore
from qtpy import QtCore, QtWidgets  # type: ignore

from robot_log_visualizer.utils.utils import ColorPalette
from robot_log_visualizer.signal_provider.signal_provider import ProviderType

# ------------------------------------------------------------------------
# Type aliases
# ------------------------------------------------------------------------
Path = Sequence[str]
Legend = Sequence[str]
Point = Tuple[float, float]


class PyQtGraphViewerCanvas(QtWidgets.QWidget):
    """Interactive time‑series viewer built on *pyqtgraph*."""

    #: Default click radius as a fraction of the current view‑range.
    DEFAULT_RADIUS: float = 0.01  # 1 % of the axes extent
    #: Default diameter of the marker drawn on a selected point.
    DEFAULT_MARKER_SIZE: int = 8

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        period: float,
        *,
        click_radius: float | None = None,
        marker_size: int | None = None,
    ) -> None:
        """Create the widget.

        Args:
            parent: Parent widget or *None*.
            period: Update period for the vertical line (seconds).
            click_radius: Override :pyattr:`DEFAULT_RADIUS`.
            marker_size: Override :pyattr:`DEFAULT_MARKER_SIZE`.
        """
        super().__init__(parent)

        # injected dependencies
        self._signal_provider = None
        self._period_ms: int = int(period * 1000)
        self._click_radius: float = click_radius or self.DEFAULT_RADIUS
        self._marker_size: int = marker_size or self.DEFAULT_MARKER_SIZE

        # data structures
        self._curves: Dict[str, pg.PlotDataItem] = {}
        self._annotations: Dict[Point, pg.TextItem] = {}
        self._markers: Dict[Point, pg.ScatterPlotItem] = {}
        self._annotation_sources: Dict[Point, str] = {}
        self._palette: Iterable = ColorPalette()

        # UI set‑up
        self._init_ui()
        self._connect_signals()

    # -------------------------------------------------------------#
    # Public API (called from the outside)                         #
    # -------------------------------------------------------------#

    def set_signal_provider(self, signal_provider) -> None:
        """Set the signal provider to fetch data from.

        Args:
            signal_provider: An instance of `SignalProvider`.
        """

        if signal_provider is None:
            return

        self._signal_provider = signal_provider

        # Connect to real-time updates for real-time provider
        if self._signal_provider.provider_type == ProviderType.REALTIME:
            self._signal_provider.update_index_signal.connect(
                self._update_realtime_curves
            )

    def update_plots(
        self, paths: Sequence[Path], legends: Sequence[Legend]
    ) -> List[str]:
        """Synchronise plots with the *paths* list.

        New items are added, disappeared items removed. Existing ones are
        left untouched to avoid flicker.
        """
        if self._signal_provider is None:
            return []

        # For real-time provider, update the set of selected signals to buffer
        if self._signal_provider.provider_type == ProviderType.REALTIME:
            selected_keys = ["::".join(path) for path in paths]
            self._signal_provider.add_signals_to_buffer(selected_keys)

        missing_paths = self._add_missing_curves(paths, legends)
        self._remove_obsolete_curves(paths)

        # Set the X axis range based on the provider type
        if self._signal_provider.provider_type == ProviderType.REALTIME:
            # For real-time data, show a fixed window with 0 set at the right edge for the latest data
            self._plot.setXRange(-self._signal_provider.realtime_fixed_plot_window, 0.0)
            # Disable mouse panning on x axis
            self._plot.plotItem.vb.setMouseEnabled(x=False, y=True)
            # For real-time data enable autoscaling of Y axis
            self._plot.plotItem.vb.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
        else:
            # Default behavior
            self._plot.setXRange(
                0.0,
                self._signal_provider.end_time - self._signal_provider.initial_time,
            )

        return missing_paths

    # The following trio is wired to whoever controls the replay/stream
    def pause_animation(self) -> None:  # noqa: D401
        """Pause the vertical‑line animation."""
        self._timer.stop()

    def resume_animation(self) -> None:  # noqa: D401
        """Resume the vertical‑line animation."""
        self._timer.start(self._period_ms)

    def quit_animation(self) -> None:  # noqa: D401
        """Permanently stop the animation (e.g. when closing the tab)."""
        self._timer.stop()

    # -------------------------------------------------------------#
    # Qt event handlers                                            #
    # -------------------------------------------------------------#
    def closeEvent(self, event):  # type: ignore[override]
        """Ensure timers are stopped before Qt destroys the object."""
        self._timer.stop()
        super().closeEvent(event)

    # -------------------------------------------------------------#
    # Internal helpers                                            #
    # -------------------------------------------------------------#
    def _init_ui(self) -> None:
        """Create all Qt widgets and lay them out."""
        self._layout = QtWidgets.QVBoxLayout(self)
        self._plot: pg.PlotWidget = pg.PlotWidget(background="w")
        self._layout.addWidget(self._plot)

        label_style = {"color": "#000000", "font-size": "12pt"}
        self._plot.setLabel("bottom", "Time [s]", **label_style)
        self._plot.setLabel("left", "Value", **label_style)
        self._plot.showGrid(x=True, y=True)

        self._plot.addLegend(
            offset=(10, 10), labelTextSize="12pt", brush=(255, 255, 255, 150)
        )
        self._plot.plotItem.legend.setParentItem(self._plot.plotItem)
        self._plot.plotItem.legend.anchor((0, 0), (0, 0))

        # Vertical line that follows *current_time*
        self._vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#555555"))
        self._plot.addItem(self._vline)

        # Timer that updates the vertical line
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._update_vline)
        self._timer.start(self._period_ms)

    def _connect_signals(self) -> None:
        """Wire Qt / pyqtgraph signals to slots."""
        self._plot.scene().sigMouseClicked.connect(self._on_mouse_click)

    def _add_missing_curves(
        self, paths: Sequence[Path], legends: Sequence[Legend]
    ) -> List[str]:
        """Plot curves that are present in *paths* but not yet on screen."""

        missing: List[str] = []
        for path, legend in zip(paths, legends):
            key = "/".join(path)
            if key in self._curves:
                continue

            # Drill down to the data array
            try:
                data = self._signal_provider.data
                for subkey in path[:-1]:
                    data = data[subkey]

                data_array = data["data"]
                timestamps = data["timestamps"]
            except (KeyError, TypeError):
                missing.append(key)
                continue

            try:
                y = data_array[:, int(path[-1])]
            except (
                IndexError,
                ValueError,
                TypeError,
            ):  # scalar variable or invalid index
                try:
                    y = data_array[:]
                except Exception:
                    missing.append(key)
                    continue

            try:
                x = timestamps - self._signal_provider.initial_time
            except Exception:
                missing.append(key)
                continue

            palette_color = next(self._palette)
            pen = pg.mkPen(palette_color.as_hex(), width=2)

            self._curves[key] = self._plot.plot(
                x,
                y,
                pen=pen,
                name="/".join(legend[1:]),
                symbol=None,
            )

        return missing

    def _remove_obsolete_curves(self, paths: Sequence[Path]) -> None:
        """Delete curves that disappeared from *paths*."""
        valid = {"/".join(p) for p in paths}
        for key in [k for k in self._curves if k not in valid]:
            self._plot.removeItem(self._curves.pop(key))

            # Remove annotations associated to the deleted curve
            orphan_points = [
                pt for pt, src in self._annotation_sources.items() if src == key
            ]
            for point in orphan_points:
                self._deselect(point)

    def _update_vline(self) -> None:
        """Move the vertical line to ``current_time``."""
        if self._signal_provider is None:
            return

        self._vline.setValue(self._signal_provider.current_time)

    def _update_realtime_curves(self):
        """Update all curves with the latest data from the signal provider."""

        if self._signal_provider is None:
            return
        for key, curve in self._curves.items():
            # Drill down to the data array using the path
            path = key.split("/")
            data = self._signal_provider.data
            for subkey in path[:-1]:
                data = data[subkey]
            try:
                y = data["data"][:, int(path[-1])]
            except (IndexError, ValueError):
                y = data["data"][:]

            # Set the 0 of the x axis to the latest timestamp
            latest_time = data["timestamps"][-1] if len(data["timestamps"]) > 0 else 0
            x = data["timestamps"] - latest_time
            curve.setData(x, y)

    def _on_mouse_click(self, event) -> None:  # noqa: N802
        """Handle a left‑click: select or unselect the nearest data point."""
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return  # ignore other buttons

        # Scene → data coordinates
        scene_pos = event.scenePos()
        if not self._plot.sceneBoundingRect().contains(scene_pos):
            return

        mouse_pt = self._plot.plotItem.vb.mapSceneToView(scene_pos)
        mx, my = float(mouse_pt.x()), float(mouse_pt.y())

        # Locate the closest (curve, index)
        candidate: Point | None = None
        min_dist_sq = np.inf
        nearest_curve: pg.PlotDataItem | None = None

        for curve in self._curves.values():
            xs, ys = curve.getData()
            d2 = (xs - mx) ** 2 + (ys - my) ** 2  # squared distance
            idx = int(np.argmin(d2))
            if (cur_d2 := float(d2[idx])) < min_dist_sq:
                min_dist_sq = cur_d2
                candidate = (float(xs[idx]), float(ys[idx]))
                nearest_curve = curve

        if candidate is None:
            return

        # Check click radius (fraction of axis span)
        x_span = np.diff(self._plot.viewRange()[0])[0]
        y_span = np.diff(self._plot.viewRange()[1])[0]
        thresh_sq = (self._click_radius * x_span) ** 2 + (
            self._click_radius * y_span
        ) ** 2
        if min_dist_sq > thresh_sq:
            return  # click too far away -> ignore

        # Toggle selection state
        if candidate in self._annotations:
            self._deselect(candidate)
        else:
            assert nearest_curve is not None  # mypy‑friendly
            self._select(candidate, nearest_curve)

    def _select(self, pt: Point, curve: pg.PlotDataItem) -> None:
        """Add label + circle marker on *pt*."""
        pen = curve.opts["pen"]
        x_span = np.diff(self._plot.viewRange()[0])[0]
        y_span = np.diff(self._plot.viewRange()[1])[0]
        x_prec = max(0, int(-np.log10(max(x_span, 1e-12))) + 2)
        y_prec = max(0, int(-np.log10(max(y_span, 1e-12))) + 2)
        label = f"{pt[0]:.{x_prec}f}, {pt[1]:.{y_prec}f}"

        txt = pg.TextItem(
            text=label,
            anchor=(0, 1),
            color="#000000",
            fill=pg.mkBrush(255, 255, 255, 200),
            border=pg.mkPen("#000000"),
        )
        txt.setPos(*pt)
        self._plot.addItem(txt)
        self._annotations[pt] = txt

        # Convert QColor → RGBA tuple for the marker fill
        qcol = pen.color()
        marker = pg.ScatterPlotItem(
            [pt[0]],
            [pt[1]],
            symbol="o",
            size=self._marker_size,
            pen=pg.mkPen("#000000"),
            brush=pg.mkBrush(qcol.red(), qcol.green(), qcol.blue(), 255),
        )
        self._plot.addItem(marker)
        self._markers[pt] = marker

        curve_key = self._curve_key(curve)
        if curve_key is not None:
            self._annotation_sources[pt] = curve_key

    def _deselect(self, pt: Point) -> None:
        """Remove annotation + marker on *pt*."""
        self._plot.removeItem(self._annotations.pop(pt))
        self._plot.removeItem(self._markers.pop(pt))
        self._annotation_sources.pop(pt, None)

    def clear_selections(self) -> None:  # noqa: D401
        """Remove **all** annotations and markers."""
        for item in (*self._annotations.values(), *self._markers.values()):
            self._plot.removeItem(item)
        self._annotations.clear()
        self._markers.clear()
        self._annotation_sources.clear()

    def clear_curves(self) -> None:
        """Remove every plotted curve and related markers."""
        for key in list(self._curves.keys()):
            self._plot.removeItem(self._curves.pop(key))
        self.clear_selections()

    def capture_state(self) -> Dict[str, Any]:
        """Return a snapshot of the current canvas configuration."""

        annotations: List[Dict[str, Any]] = []
        for pt, label in self._annotations.items():
            source = self._annotation_sources.get(pt)
            if source is None:
                continue
            annotations.append(
                {
                    "path": source,
                    "point": [float(pt[0]), float(pt[1])],
                    "label": label.toPlainText(),
                }
            )

        curve_meta: Dict[str, Dict[str, Any]] = {}
        for key, curve in self._curves.items():
            pen_info: Dict[str, Any] = {}
            pen = curve.opts.get("pen")
            if pen is not None:
                qcol = pen.color()
                pen_info["color"] = (
                    f"#{qcol.red():02x}{qcol.green():02x}{qcol.blue():02x}"
                )
                pen_info["width"] = pen.width()
            curve_meta[key] = {
                "label": curve.opts.get("name", ""),
                "pen": pen_info,
            }

        return {
            "curves": curve_meta,
            "view_range": self._plot.viewRange(),
            "legend_visible": bool(self._plot.plotItem.legend.isVisible()),
            "annotations": annotations,
        }

    def apply_view_range(self, view_range: Sequence[Sequence[float]]) -> None:
        """Restore the axes limits from a snapshot."""

        if len(view_range) != 2:
            return

        x_range, y_range = view_range
        if len(x_range) == 2:
            self._plot.setXRange(float(x_range[0]), float(x_range[1]), padding=0)
        if len(y_range) == 2:
            self._plot.setYRange(float(y_range[0]), float(y_range[1]), padding=0)

    def set_legend_visible(self, visible: bool) -> None:
        """Toggle legend visibility."""

        legend = getattr(self._plot.plotItem, "legend", None)
        if legend is not None:
            legend.setVisible(bool(visible))

    def restore_annotations(self, annotations: Sequence[Dict[str, Any]]) -> List[str]:
        """Re-create selection markers from saved data.

        Returns:
            List of curve identifiers that could not be restored.
        """

        missing: List[str] = []
        for ann in annotations:
            key = ann.get("path")
            point = ann.get("point")
            if key is None or point is None:
                continue
            curve = self._curves.get(str(key))
            if curve is None:
                missing.append(str(key))
                continue
            try:
                pt_tuple: Point = (float(point[0]), float(point[1]))
            except (TypeError, ValueError, IndexError):
                missing.append(str(key))
                continue
            self._select(pt_tuple, curve)
        return missing

    def _curve_key(self, curve: pg.PlotDataItem) -> str | None:
        for key, item in self._curves.items():
            if item is curve:
                return key
        return None

    def apply_curve_metadata(self, metadata: Dict[str, Dict[str, Any]]) -> None:
        for key, info in metadata.items():
            curve = self._curves.get(key)
            if curve is None:
                continue

            label = info.get("label")
            if label is not None:
                label_text = str(label)
                if hasattr(curve, "setName"):
                    curve.setName(label_text)
                else:
                    curve.opts["name"] = label_text
                    legend = getattr(self._plot.plotItem, "legend", None)
                    if legend is not None:
                        if hasattr(legend, "itemChanged"):
                            legend.itemChanged(curve)
                        else:  # compatibility fallback for older pyqtgraph releases
                            try:
                                legend.removeItem(curve)
                            except Exception:
                                pass
                            legend.addItem(curve, label_text)

            pen_info = info.get("pen", {})
            color = pen_info.get("color")
            width = pen_info.get("width")
            if color is not None or width is not None:
                kwargs: Dict[str, Any] = {}
                if color is not None:
                    kwargs["color"] = color
                if width is not None:
                    try:
                        kwargs["width"] = float(width)
                    except (TypeError, ValueError):
                        pass
                if kwargs:
                    curve.setPen(pg.mkPen(**kwargs))
