# Copyright (C) 2025 Istituto Italiano di Tecnologia (IIT).
# This software may be modified and distributed under the terms of the
# BSD 3-Clause License.

"""Data structures for serialising view snapshots to/from JSON."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


SNAPSHOT_VERSION = 1


def _copy_path_list(value: Any) -> List[str]:
    return [str(v) for v in (value or [])]


@dataclass
class DatasetSnapshot:
    path: Optional[str] = None
    robot_name: Optional[str] = None
    provider: str = "offline"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "robot_name": self.robot_name,
            "provider": self.provider,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "DatasetSnapshot":
        return cls(
            path=raw.get("path"),
            robot_name=raw.get("robot_name"),
            provider=raw.get("provider", "offline"),
        )


@dataclass
class WindowSnapshot:
    geometry: Optional[str] = None
    state: Optional[str] = None
    plot_tab_index: int = 0
    main_tab_index: int = 0
    meshcat_tab_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "geometry": self.geometry,
            "state": self.state,
            "plot_tab_index": self.plot_tab_index,
            "main_tab_index": self.main_tab_index,
            "meshcat_tab_index": self.meshcat_tab_index,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "WindowSnapshot":
        return cls(
            geometry=raw.get("geometry"),
            state=raw.get("state"),
            plot_tab_index=int(raw.get("plot_tab_index", 0)),
            main_tab_index=int(raw.get("main_tab_index", 0)),
            meshcat_tab_index=int(raw.get("meshcat_tab_index", 0)),
        )


@dataclass
class TimelineSnapshot:
    index: int = 0
    slider_value: int = 0
    slider_max: int = 0
    is_running: bool = False
    current_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "slider_value": self.slider_value,
            "slider_max": self.slider_max,
            "is_running": self.is_running,
            "current_time": self.current_time,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "TimelineSnapshot":
        return cls(
            index=int(raw.get("index", 0)),
            slider_value=int(raw.get("slider_value", 0)),
            slider_max=int(raw.get("slider_max", 0)),
            is_running=bool(raw.get("is_running", False)),
            current_time=float(raw.get("current_time", 0.0)),
        )


@dataclass
class PlotSnapshot:
    title: str = "Plot"
    paths: List[List[str]] = field(default_factory=list)
    legends: List[List[str]] = field(default_factory=list)
    canvas: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "paths": self.paths,
            "legends": self.legends,
            "canvas": self.canvas,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "PlotSnapshot":
        return cls(
            title=raw.get("title", "Plot"),
            paths=[_copy_path_list(p) for p in raw.get("paths", [])],
            legends=[_copy_path_list(l) for l in raw.get("legends", [])],
            canvas=dict(raw.get("canvas", {})),
        )


@dataclass
class TreeSnapshot:
    selected_variables: List[List[str]] = field(default_factory=list)
    selected_text_logs: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_variables": self.selected_variables,
            "selected_text_logs": self.selected_text_logs,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "TreeSnapshot":
        return cls(
            selected_variables=[
                _copy_path_list(path) for path in raw.get("selected_variables", [])
            ],
            selected_text_logs=[
                _copy_path_list(path) for path in raw.get("selected_text_logs", [])
            ],
        )


@dataclass
class VisualizationSnapshot:
    points: List[Dict[str, Any]] = field(default_factory=list)
    trajectories: List[Dict[str, Any]] = field(default_factory=list)
    arrows: List[Dict[str, Any]] = field(default_factory=list)
    robot_state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "points": self.points,
            "trajectories": self.trajectories,
            "arrows": self.arrows,
            "robot_state": self.robot_state,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "VisualizationSnapshot":
        return cls(
            points=[dict(entry) for entry in raw.get("points", [])],
            trajectories=[dict(entry) for entry in raw.get("trajectories", [])],
            arrows=[dict(entry) for entry in raw.get("arrows", [])],
            robot_state=dict(raw.get("robot_state", {})),
        )


@dataclass
class ViewSnapshot:
    """Container for all serialised UI state."""

    version: int = SNAPSHOT_VERSION
    metadata: Dict[str, Any] = field(default_factory=dict)
    dataset: DatasetSnapshot = field(default_factory=DatasetSnapshot)
    window: WindowSnapshot = field(default_factory=WindowSnapshot)
    timeline: TimelineSnapshot = field(default_factory=TimelineSnapshot)
    plots: List[PlotSnapshot] = field(default_factory=list)
    tree: TreeSnapshot = field(default_factory=TreeSnapshot)
    visualization: VisualizationSnapshot = field(default_factory=VisualizationSnapshot)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "metadata": self.metadata,
            "dataset": self.dataset.to_dict(),
            "window": self.window.to_dict(),
            "timeline": self.timeline.to_dict(),
            "plots": [plot.to_dict() for plot in self.plots],
            "tree": self.tree.to_dict(),
            "visualization": self.visualization.to_dict(),
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "ViewSnapshot":
        version = int(raw.get("version", SNAPSHOT_VERSION))
        return cls(
            version=version,
            metadata=dict(raw.get("metadata", {})),
            dataset=DatasetSnapshot.from_dict(dict(raw.get("dataset", {}))),
            window=WindowSnapshot.from_dict(dict(raw.get("window", {}))),
            timeline=TimelineSnapshot.from_dict(dict(raw.get("timeline", {}))),
            plots=[PlotSnapshot.from_dict(entry) for entry in raw.get("plots", [])],
            tree=TreeSnapshot.from_dict(dict(raw.get("tree", {}))),
            visualization=VisualizationSnapshot.from_dict(
                dict(raw.get("visualization", {}))
            ),
        )
