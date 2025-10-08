# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

# QtPy abstraction
from __future__ import annotations
from qtpy import QtWidgets, QtGui, QtCore
from qtpy import QtWebEngineWidgets  # noqa: F401  # Ensure WebEngine is initialised
from qtpy.QtCore import QMutex, QMutexLocker, QSaveFile, QUrl, Qt, Slot, QIODevice
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QToolButton,
    QTreeWidgetItem,
    QVBoxLayout,
)

pyqtSlot = Slot
from robot_log_visualizer.robot_visualizer.meshcat_provider import MeshcatProvider
from robot_log_visualizer.signal_provider.realtime_signal_provider import (
    RealtimeSignalProvider,
    are_deps_installed,
)
from robot_log_visualizer.signal_provider.matfile_signal_provider import (
    MatfileSignalProvider,
)

from robot_log_visualizer.signal_provider.signal_provider import (
    ProviderType,
    SignalProvider,
)
from robot_log_visualizer.ui.plot_item import PlotItem
from robot_log_visualizer.ui.video_item import VideoItem
from robot_log_visualizer.ui.text_logging import TextLoggingItem
from robot_log_visualizer.ui.view_snapshot import (
    SNAPSHOT_VERSION,
    ViewSnapshot,
    PlotSnapshot,
    VisualizationSnapshot,
    TimelineSnapshot,
    DatasetSnapshot,
    WindowSnapshot,
    TreeSnapshot,
)

from robot_log_visualizer.utils.utils import (
    PeriodicThreadState,
    RobotStatePath,
    ColorPalette,
    Color,
)

import sys
import os
import json
import base64
import pathlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

# QtDesigner generated classes
from robot_log_visualizer.ui.ui_loader import load_ui

# for logging
from time import localtime, strftime

# Matplotlib class
from pyqtconsole.console import PythonConsole
import pyqtconsole.highlighter as hl


class SetRobotModelDialog(QtWidgets.QDialog):
    def __init__(self, meshcat_provider, parent=None, dataset_loaded=False):
        # call QMainWindow constructor
        super().__init__(parent)
        self.ui = load_ui("set_robot_model.ui", self)

        model_path = meshcat_provider.model_path
        package_dir = meshcat_provider.custom_package_dir

        if model_path:
            self.ui.robotModelLineEdit.setText(model_path)

        if package_dir:
            self.ui.packageDirLineEdit.setText(package_dir)

        self.ui.robotModelLineEdit.setEnabled(not dataset_loaded)
        self.ui.packageDirLineEdit.setEnabled(not dataset_loaded)

        self.ui.robotModelToolButton.clicked.connect(self.open_urdf_file)
        self.ui.packageDirToolButton.clicked.connect(self.open_package_directory)

        # Force the arrowScaling_lineEdit to be a positive float
        self.ui.arrowScaling_lineEdit.setValidator(QtGui.QDoubleValidator(0, 100, 2))

        # connect the arrowScaling_checkBox to the handle_arrow_scaling method
        self.ui.arrowScaling_checkBox.toggled.connect(self.handle_arrow_scaling)

        self.clicked_button = None
        self.std_button = None
        self.ui.buttonBox.clicked.connect(self.buttonBox_on_click)

        if dataset_loaded:
            frames = meshcat_provider.robot_frames()
            self.ui.frameNameComboBox.addItems(frames)
            self.ui.frameNameComboBox.setCurrentText(meshcat_provider.base_frame)

    def open_urdf_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open urdf file", ".", filter="*.urdf"
        )
        if file_name:
            self.ui.robotModelLineEdit.setText(file_name)

    def open_package_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select package directory")
        if dir_path:
            self.ui.packageDirLineEdit.setText(dir_path)

    def get_urdf_path(self):
        return self.ui.robotModelLineEdit.text()

    def get_package_directory(self):
        return self.ui.packageDirLineEdit.text()

    def buttonBox_on_click(self, button):
        self.clicked_button = button

        self.std_button = self.ui.buttonBox.standardButton(button)

    def get_clicked_button_role(self):
        if self.clicked_button is not None:
            return self.ui.buttonBox.buttonRole(self.clicked_button)
        return None

    def get_clicked_button_text(self):
        if self.clicked_button is not None:
            return self.clicked_button.text()
        return None

    def get_clicked_standard_button(self):
        return self.std_button

    def handle_arrow_scaling(self):
        # if arrowScaling_checkBox is checked the lineEdit must be disabled else it must be enabled
        if self.ui.arrowScaling_checkBox.isChecked():
            self.ui.arrowScaling_lineEdit.setText("")
            self.ui.arrowScaling_lineEdit.setEnabled(False)
        else:
            self.ui.arrowScaling_lineEdit.setText("")
            self.ui.arrowScaling_lineEdit.setEnabled(True)


class About(QtWidgets.QMainWindow):
    def __init__(self):
        # call QMainWindow constructor
        super().__init__()
        self.ui = load_ui("about.ui", self)


def build_plot_title_box_dialog():
    dlg = QDialog()
    dlg.setWindowTitle("Plot title")
    la = QVBoxLayout(dlg)
    line_edit = QLineEdit()
    la.addWidget(line_edit)
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.clicked.connect(dlg.accept)
    bb.rejected.connect(dlg.reject)
    la.addWidget(bb)
    dlg.setLayout(la)
    return dlg, line_edit


def get_icon(icon_name):
    icon = QtGui.QIcon()
    icon.addPixmap(
        QtGui.QPixmap(str(pathlib.Path(__file__).parent / "misc" / icon_name)),
        QtGui.QIcon.Normal,
        QtGui.QIcon.Off,
    )
    return icon


class RobotViewerMainWindow(QtWidgets.QMainWindow):
    def __init__(self, signal_provider_period, meshcat_provider, animation_period):
        # call QMainWindow constructor
        super().__init__()

        self.signal_provider_period = signal_provider_period

        # for realtime logging
        self.realtimePlotUpdaterThreadActive = False
        self.plotData = {}
        self.realtime_connection_enabled = False
        self.timeoutAttempts = 20

        self.animation_period = animation_period

        # set up the user interface
        self.ui = load_ui("visualizer.ui", self)

        # Set all the icons
        self.ui.startButton.setIcon(get_icon("play-outline.svg"))
        self.ui.pauseButton.setIcon(get_icon("pause-outline.svg"))
        self.ui.pauseButton.setIcon(get_icon("pause-outline.svg"))
        self.ui.meshcatAndVideoTab.setTabIcon(
            0, get_icon("game-controller-outline.svg")
        )
        self.ui.tabWidget.setTabIcon(0, get_icon("calendar-outline.svg"))
        self.ui.tabWidget.setTabIcon(1, get_icon("terminal-outline.svg"))
        self.ui.tabWidget.setTabIcon(2, get_icon("document-text-outline.svg"))

        self.ui.actionQuit.setIcon(get_icon("close-circle-outline.svg"))
        self.ui.actionQuit.setIcon(get_icon("close-circle-outline.svg"))
        self.ui.actionOpen.setIcon(get_icon("folder-open-outline.svg"))
        self.ui.actionSet_Robot_Model.setIcon(get_icon("body-outline.svg"))
        self.setWindowIcon(get_icon("icon.png"))

        self.about = About()

        self.signal_provider: SignalProvider = None

        self.meshcat_provider: MeshcatProvider = meshcat_provider

        self.tool_button = QToolButton()
        self.tool_button.setText("+")
        self.ui.tabPlotWidget.setCornerWidget(self.tool_button)
        self.tool_button.clicked.connect(self.toolButton_on_click)

        self.plot_items = []
        self.video_items = []
        self.visualized_3d_points = set()
        self.visualized_3d_trajectories = set()
        self.visualized_3d_arrows = set()
        self.visualized_3d_points_colors = {}
        self.visualized_3d_trajectories_colors = {}
        self.visualized_3d_arrows_colors = {}
        self.visualized_3d_points_colors_palette = ColorPalette()

        self.toolButton_on_click()

        # instantiate the Logger
        self.logger = Logger(self.ui.logLabel, self.ui.logScrollArea)
        # print welcome message
        self.logger.write_to_log("Robot Viewer started.")

        self.text_logger = TextLoggingItem(self.ui.yarpTextLogTableWidget)

        self._slider_pressed_mutex = QMutex()
        self._slider_pressed = False

        self.dataset_loaded = False

        self.loaded_mat_path = None
        self._settings = QtCore.QSettings("ami-iit", "robot-log-visualizer")
        self._snapshot_dir_key = "snapshot/lastDirectory"
        self._snapshot_last_dir = pathlib.Path(
            self._settings.value(self._snapshot_dir_key, pathlib.Path.home())
        )

        self.ui.actionSave_View.setEnabled(False)
        self.ui.actionSave_View.triggered.connect(self.save_view_snapshot)
        self.ui.actionLoad_View.triggered.connect(self.load_view_snapshot)

        # connect action
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionOpen.triggered.connect(self.open_mat_file)

        if are_deps_installed():
            self.ui.actionRealtime_Connect.triggered.connect(
                self.connect_realtime_logger
            )
        else:
            self.ui.actionRealtime_Connect.setEnabled(False)

        self.ui.actionAbout.triggered.connect(self.open_about)
        self.ui.actionSet_Robot_Model.triggered.connect(self.open_set_robot_model)

        self.ui.meshcatView.setUrl(
            QUrl(meshcat_provider._meshcat_visualizer.viewer.url())
        )

        self.ui.pauseButton.clicked.connect(self.pauseButton_on_click)
        self.ui.startButton.clicked.connect(self.startButton_on_click)
        self.ui.timeSlider.sliderReleased.connect(self.timeSlider_on_release)
        self.ui.timeSlider.sliderPressed.connect(self.timeSlider_on_pressed)
        self.ui.timeSlider.sliderMoved.connect(self.timeSlider_on_sliderMoved)

        self.ui.variableTreeWidget.itemClicked.connect(self.variableTreeWidget_on_click)
        self.ui.yarpTextLogTreeWidget.itemClicked.connect(
            self.textLogTreeWidget_on_click
        )

        self.ui.tabPlotWidget.tabCloseRequested.connect(
            self.plotTabCloseButton_on_click
        )
        self.ui.tabPlotWidget.tabBarDoubleClicked.connect(
            self.plotTabBar_on_doubleClick
        )
        self.ui.tabPlotWidget.currentChanged.connect(self.plotTabBar_currentChanged)

        # add a custom context menu to the variable tree widget
        self.ui.variableTreeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.variableTreeWidget.customContextMenuRequested.connect(
            self.variableTreeWidget_on_right_click
        )

        self.robot_state_path = RobotStatePath()

        self.pyconsole = PythonConsole(
            parent=self.ui.pythonWidget,
            formats={
                "keyword": hl.format("#204a87", "bold"),
                "operator": hl.format("#ce5c00"),
                # 'brace':      hl.format('#eeeeec'),
                "defclass": hl.format("#000000", "bold"),
                "string": hl.format("#8f5902"),
                "string2": hl.format("#8f5902"),
                "comment": hl.format("#8f5902", "italic"),
                "self": hl.format("#000000", "italic"),
                "numbers": hl.format("#0000cf"),
                "inprompt": hl.format("#8f5902", "bold"),
                "outprompt": hl.format("#8f5902", "bold"),
            },
        )
        self.pyconsole.edit.setStyleSheet("font-size: 12px;")
        self.ui.pythonWidgetLayout.addWidget(self.pyconsole)
        self.pyconsole.eval_in_thread()

        # self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        # self.media_player.setVideoOutput(self.ui.webcamView)
        # self.media_loaded = False

    @property
    def slider_pressed(self):
        locker = QMutexLocker(self._slider_pressed_mutex)
        value = self._slider_pressed
        return value

    @slider_pressed.setter
    def slider_pressed(self, slider_pressed):
        locker = QMutexLocker(self._slider_pressed_mutex)
        self._slider_pressed = slider_pressed

    def keyPressEvent(self, event):
        if not self.dataset_loaded:
            return

        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_B:
                self.slider_pressed = True
                new_index = int(self.ui.timeSlider.value()) - 1
                dataset_percentage = float(new_index) / float(
                    self.ui.timeSlider.maximum()
                )
                self.signal_provider.set_dataset_percentage(dataset_percentage)
                self.ui.timeLabel.setText(f"{self.signal_provider.current_time:.2f}")
                self.text_logger.highlight_cell(
                    self.find_text_log_index(self.get_text_log_item_path())
                )

                # for every video item we set the instant
                for video_item in self.video_items:
                    if video_item.media_loaded:
                        video_item.media_player.setPosition(
                            int(dataset_percentage * video_item.media_player.duration())
                        )

                # update the time slider
                self.ui.timeSlider.setValue(new_index)
                self.slider_pressed = False
            elif event.key() == Qt.Key_F:
                self.slider_pressed = True
                new_index = int(self.ui.timeSlider.value()) + 1
                dataset_percentage = float(new_index) / float(
                    self.ui.timeSlider.maximum()
                )
                self.signal_provider.set_dataset_percentage(dataset_percentage)
                self.ui.timeLabel.setText(f"{self.signal_provider.current_time:.2f}")
                self.text_logger.highlight_cell(
                    self.find_text_log_index(self.get_text_log_item_path())
                )

                # for every video item we set the instant
                for video_item in self.video_items:
                    if video_item.media_loaded:
                        video_item.media_player.setPosition(
                            int(dataset_percentage * video_item.media_player.duration())
                        )

                self.ui.timeSlider.setValue(new_index)
                self.slider_pressed = False
        else:
            # If the user presses the space bar, the play/pause state is toggled.
            if event.key() == Qt.Key_Space:
                # toggle the play/pause button
                if self.ui.startButton.isEnabled():
                    self.ui.startButton.click()
                else:
                    self.ui.pauseButton.click()

    def toolButton_on_click(self):
        self.plot_items.append(PlotItem(period=self.animation_period))
        self.plot_items[-1].set_signal_provider(self.signal_provider)
        self.ui.tabPlotWidget.addTab(self.plot_items[-1], "Plot")

        if self.ui.tabPlotWidget.count() == 1:
            self.ui.tabPlotWidget.setTabsClosable(False)
        else:
            self.ui.tabPlotWidget.setTabsClosable(True)

    def timeSlider_on_pressed(self):
        self.slider_pressed = True

    def timeSlider_on_sliderMoved(self):
        index = int(self.ui.timeSlider.value())
        dataset_percentage = float(index) / float(self.ui.timeSlider.maximum())

        for video_item in self.video_items:
            if video_item.media_loaded:
                video_item.media_player.setPosition(
                    int(dataset_percentage * video_item.media_player.duration())
                )

        self.signal_provider.set_dataset_percentage(dataset_percentage)
        self.ui.timeLabel.setText(f"{self.signal_provider.current_time:.2f}")
        self.text_logger.highlight_cell(
            self.find_text_log_index(self.get_text_log_item_path())
        )

    def timeSlider_on_release(self):
        index = int(self.ui.timeSlider.value())
        dataset_percentage = float(index) / float(self.ui.timeSlider.maximum())

        for video_item in self.video_items:
            if video_item.media_loaded:
                video_item.media_player.setPosition(
                    int(dataset_percentage * video_item.media_player.duration())
                )

        self.signal_provider.set_dataset_percentage(dataset_percentage)
        self.ui.timeLabel.setText(f"{self.signal_provider.current_time:.2f}")
        self.text_logger.highlight_cell(
            self.find_text_log_index(self.get_text_log_item_path())
        )
        self.slider_pressed = False

    def startButton_on_click(self):
        self.ui.startButton.setEnabled(False)
        self.ui.pauseButton.setEnabled(True)
        self.signal_provider.state = PeriodicThreadState.running
        self.meshcat_provider.state = PeriodicThreadState.running

        self.logger.write_to_log("Dataset started.")

    def pauseButton_on_click(self):
        self.ui.pauseButton.setEnabled(False)
        self.ui.startButton.setEnabled(True)

        for video_item in self.video_items:
            if video_item.media_loaded:
                video_item.media_player.pause()

        self.signal_provider.state = PeriodicThreadState.pause
        self.meshcat_provider.state = PeriodicThreadState.pause

        self.logger.write_to_log("Dataset paused.")

    def plotTabCloseButton_on_click(self, index):
        self.plot_items[index].canvas.quit_animation()
        del self.plot_items[index]
        if self.ui.tabPlotWidget.count() == 1:
            self.ui.tabPlotWidget.setTabsClosable(False)
        self.ui.tabPlotWidget.removeTab(index)

    def plotTabBar_on_doubleClick(self, index):
        dlg, plot_title = build_plot_title_box_dialog()
        if dlg.exec_() == QDialog.Accepted:
            self.ui.tabPlotWidget.setTabText(index, plot_title.text())

    def variableTreeWidget_on_click(self):
        paths = []
        legends = []
        for index in self.ui.variableTreeWidget.selectedIndexes():
            path = []
            legend = []
            is_leaf = True
            while index.data() is not None:
                legend.append(index.data())
                if not is_leaf:
                    path.append(index.data())
                else:
                    path.append(str(index.row()))
                    is_leaf = False

                index = index.parent()
            path.reverse()
            legend.reverse()

            paths.append(path)
            legends.append(legend)

        # if there is no selection we do nothing
        if not paths:
            return

        self.plotData[self.ui.tabPlotWidget.currentIndex()] = {
            "paths": paths,
            "legends": legends,
        }

        missing_curves = self.plot_items[
            self.ui.tabPlotWidget.currentIndex()
        ].canvas.update_plots(paths, legends)

        if missing_curves:
            self.logger.write_to_log(
                "Some signals could not be plotted: "
                + ", ".join(sorted(set(missing_curves)))
            )

    def find_text_log_index(self, path):
        current_time = self.signal_provider.current_time
        initial_time = self.signal_provider.initial_time

        path = self.get_text_log_item_path()
        if path:
            ref = self.signal_provider.text_logging_data
            for key in path:
                ref = ref[key]

            s = np.flatnonzero(ref["timestamps"] <= current_time + initial_time)
            if len(s) == 1:
                return s[0]
            elif not s.any():
                return None
            else:
                return s[-1]

        return None

    def show_text_log(self, path):
        initial_time = self.signal_provider.initial_time
        ref = self.signal_provider.text_logging_data
        for key in path:
            ref = ref[key]

        self.text_logger.clean()
        logs = ref["data"]
        timestamps = ref["timestamps"]
        for i in range(len(ref["data"])):
            self.text_logger.add_entry(
                logs[i].text, timestamps[i] - initial_time, font_color=logs[i].color()
            )

    def get_text_log_item_path(self):
        paths = []
        for index in self.ui.yarpTextLogTreeWidget.selectedIndexes():
            path = []
            is_leaf = True
            while index.data() is not None:
                if not is_leaf:
                    path.append(index.data())
                else:
                    path.append(index.data())
                    is_leaf = False

                index = index.parent()

            path.reverse()
            paths.append(path)
        if paths:
            return paths[0]
        else:
            return None

    def textLogTreeWidget_on_click(self):
        path = self.get_text_log_item_path()
        if path:
            self.show_text_log(path)
            self.text_logger.highlight_cell(self.find_text_log_index(path))

    def plotTabBar_currentChanged(self, index):
        # pause all the animations except the one that is selected, this is done to avoid the overhead of the animations
        for i in range(len(self.plot_items)):
            if i != index:
                self.plot_items[i].canvas.pause_animation()
            else:
                self.plot_items[i].canvas.resume_animation()

        # clear the selection to prepare a new one
        self.ui.variableTreeWidget.clearSelection()
        for active_path_str in self.plot_items[index].canvas._curves.keys():
            path = active_path_str.split("/")

            # select the item in the tree from the path
            item = self.ui.variableTreeWidget.topLevelItem(0)
            for subpath in path[1:-1]:
                # find the item given its name
                for child_id in range(item.childCount()):
                    if item.child(child_id).text(0) == subpath:
                        item = item.child(child_id)
                        break

            # the latest value is a number
            item = item.child(int(path[-1]))
            item.setSelected(True)

    @pyqtSlot()
    def update_index(self):
        if self.slider_pressed:
            return

        self.ui.timeSlider.setValue(self.signal_provider.index)
        self.ui.timeLabel.setText(f"{self.signal_provider.current_time:.2f}")
        self.text_logger.highlight_cell(
            self.find_text_log_index(self.get_text_log_item_path())
        )

        # TODO: this is a hack to update the video player and it should be done only for the activated videos
        for video_item in self.video_items:
            if video_item.media_loaded:
                video_percentage = float(self.ui.timeSlider.value()) / float(
                    self.ui.timeSlider.maximum()
                )
                video_item.media_player.setPosition(
                    int(video_percentage * video_item.media_player.duration())
                )

    def closeEvent(self, event):
        # ensure update callbacks are not triggered while tearing down the UI
        if self.signal_provider is not None:
            try:
                self.signal_provider.update_index_signal.disconnect(self.update_index)
            except (TypeError, RuntimeError):
                # ignore if already disconnected
                pass

        # stop timers/animations before widgets disappear
        for plot_item in self.plot_items:
            plot_item.canvas.quit_animation()

        # stop the embedded Python console (it owns a QThread)
        self.pyconsole.close()

        # gracefully stop worker threads before deleting widgets they use
        if self.signal_provider is not None:
            self.signal_provider.state = PeriodicThreadState.closed
            self.signal_provider.wait()
            self.signal_provider = None

        # Stop the meshcat_provider if exists
        if self.meshcat_provider is not None:
            self.meshcat_provider.state = PeriodicThreadState.closed
            self.meshcat_provider.wait()

        # release multimedia resources explicitly to avoid late callbacks
        # while closing
        for video_item in self.video_items:
            media_player = getattr(video_item, "media_player", None)
            if media_player is not None:
                if video_item.media_loaded:
                    media_player.stop()
                try:
                    media_player.setVideoOutput(None)
                except Exception:
                    pass
                media_player.deleteLater()
            video_item.deleteLater()
        self.video_items.clear()

        # Disable realtime connection
        if self.realtime_connection_enabled:
            self.realtime_connection_enabled = False

        event.accept()

    def __populate_variable_tree_widget(self, obj, parent) -> QTreeWidgetItem:
        if not isinstance(obj, dict):
            return parent
        if "data" in obj.keys() and "timestamps" in obj.keys():
            temp_array = obj["data"]
            try:
                n_cols = temp_array.shape[1]
            except IndexError:
                # This happens in the case the variable is a scalar.
                n_cols = 1

            # In yarp telemetry v0.4.0 the elements_names was saved.
            if "elements_names" in obj.keys():
                for name in obj["elements_names"]:
                    item = QTreeWidgetItem([name])
                    parent.addChild(item)
            else:
                for i in range(n_cols):
                    item = QTreeWidgetItem(["Element " + str(i)])
                    parent.addChild(item)
            return parent
        for key, value in obj.items():
            item = QTreeWidgetItem([key])
            item = self.__populate_variable_tree_widget(value, item)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            parent.addChild(item)
        return parent

    def __populate_text_logging_tree_widget(self, obj, parent) -> QTreeWidgetItem:
        if not isinstance(obj, dict):
            return parent

        if "data" in obj.keys() and "timestamps" in obj.keys():
            return parent

        for key, value in obj.items():
            item = QTreeWidgetItem([key])
            item = self.__populate_text_logging_tree_widget(value, item)
            if "data" not in value.keys():
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            parent.addChild(item)
        return parent

    def _clear_plot_tabs(self) -> None:
        while self.ui.tabPlotWidget.count() > 0:
            widget = self.ui.tabPlotWidget.widget(0)
            if isinstance(widget, PlotItem):
                widget.canvas.quit_animation()
                widget.deleteLater()
            self.ui.tabPlotWidget.removeTab(0)
        self.plot_items.clear()
        self.plotData.clear()

    def _ensure_plot_tab_count(self, count: int) -> None:
        count = max(1, count)
        while self.ui.tabPlotWidget.count() > count:
            self.plotTabCloseButton_on_click(self.ui.tabPlotWidget.count() - 1)
        while self.ui.tabPlotWidget.count() < count:
            self.toolButton_on_click()

    def _clear_visualization_items(self) -> None:
        """Remove all registered 3D primitives from Meshcat and reset trackers."""

        if self.meshcat_provider is not None:
            for point in list(self.visualized_3d_points):
                try:
                    self.meshcat_provider.unregister_3d_point(point)
                except KeyError:
                    pass
            for trajectory in list(self.visualized_3d_trajectories):
                try:
                    self.meshcat_provider.unregister_3d_trajectory(trajectory)
                except KeyError:
                    pass
            for arrow in list(self.visualized_3d_arrows):
                try:
                    self.meshcat_provider.unregister_3d_arrow(arrow)
                except KeyError:
                    pass

        self.visualized_3d_points.clear()
        self.visualized_3d_trajectories.clear()
        self.visualized_3d_arrows.clear()
        self.visualized_3d_points_colors.clear()
        self.visualized_3d_trajectories_colors.clear()
        self.visualized_3d_arrows_colors.clear()
        self.visualized_3d_points_colors_palette.reset()

    def _prepare_for_new_dataset(self) -> None:
        if self.signal_provider is not None:
            try:
                self.signal_provider.update_index_signal.disconnect(self.update_index)
            except (TypeError, RuntimeError):
                pass
            self.signal_provider.state = PeriodicThreadState.closed
            self.signal_provider.wait()
            self.signal_provider = None

        self.dataset_loaded = False
        self.loaded_mat_path = None

        self.ui.variableTreeWidget.clear()
        self.ui.yarpTextLogTreeWidget.clear()
        self.robot_state_path = RobotStatePath()

        # Clear registered 3D items in Meshcat
        self._clear_visualization_items()

        # Remove video tabs (keep meshcat tab at index 0)
        while self.ui.meshcatAndVideoTab.count() > 1:
            widget = self.ui.meshcatAndVideoTab.widget(1)
            widget.deleteLater()
            self.ui.meshcatAndVideoTab.removeTab(1)
        for video_item in self.video_items:
            video_item.deleteLater()
        self.video_items.clear()

        self._clear_plot_tabs()
        self.toolButton_on_click()
        self.ui.tabPlotWidget.setCurrentIndex(0)
        self.ui.tabPlotWidget.setTabsClosable(False)

        self.ui.timeSlider.setEnabled(False)
        self.ui.timeSlider.setValue(0)
        self.ui.startButton.setEnabled(False)
        self.ui.pauseButton.setEnabled(False)

        self.realtime_connection_enabled = False
        self.ui.actionRealtime_Connect.setEnabled(True)
        self.ui.actionSave_View.setEnabled(False)

    def _snapshot_start_directory(self) -> pathlib.Path:
        if self._snapshot_last_dir.exists():
            return self._snapshot_last_dir
        return pathlib.Path.home()

    def _remember_snapshot_directory(self, path: pathlib.Path) -> None:
        self._snapshot_last_dir = path
        self._settings.setValue(self._snapshot_dir_key, str(path))

    @staticmethod
    def _encode_qbytearray(data: QtCore.QByteArray | None) -> Optional[str]:
        if data is None or data.isEmpty():
            return None
        return bytes(data.toBase64()).decode("ascii")

    @staticmethod
    def _decode_qbytearray(encoded: Optional[str]) -> Optional[QtCore.QByteArray]:
        if not encoded:
            return None
        return QtCore.QByteArray.fromBase64(encoded.encode("ascii"))

    def _selected_variable_paths(self) -> List[List[str]]:
        paths: List[List[str]] = []
        for index in self.ui.variableTreeWidget.selectedIndexes():
            if index.column() != 0:
                continue
            path: List[str] = []
            is_leaf = True
            current = index
            while current.data() is not None:
                if is_leaf:
                    path.append(str(current.row()))
                    is_leaf = False
                else:
                    path.append(str(current.data()))
                current = current.parent()
            path.reverse()
            if path:
                paths.append(path)
        return paths

    def _selected_text_log_paths(self) -> List[List[str]]:
        paths: List[List[str]] = []
        for index in self.ui.yarpTextLogTreeWidget.selectedIndexes():
            if index.column() != 0:
                continue
            path: List[str] = []
            current = index
            while current.data() is not None:
                path.append(str(current.data()))
                current = current.parent()
            path.reverse()
            if path:
                paths.append(path)
        return paths

    def _find_variable_tree_item(
        self, path: Sequence[str]
    ) -> Optional[QTreeWidgetItem]:
        if not path:
            return None

        matches = self.ui.variableTreeWidget.findItems(
            path[0], Qt.MatchFixedString | Qt.MatchExactly
        )
        if not matches:
            return None
        item = matches[0]

        for part in path[1:]:
            try:
                child_index = int(part)
            except (TypeError, ValueError):
                child_index = None

            if child_index is not None:
                if 0 <= child_index < item.childCount():
                    item = item.child(child_index)
                else:
                    return None
            else:
                found = None
                for i in range(item.childCount()):
                    if item.child(i).text(0) == part:
                        found = item.child(i)
                        break
                if found is None:
                    return None
                item = found

        return item

    def _find_text_log_tree_item(
        self, path: Sequence[str]
    ) -> Optional[QTreeWidgetItem]:
        if not path:
            return None

        matches = self.ui.yarpTextLogTreeWidget.findItems(
            path[0], Qt.MatchFixedString | Qt.MatchExactly
        )
        if not matches:
            return None
        item = matches[0]

        for part in path[1:]:
            found = None
            for i in range(item.childCount()):
                if item.child(i).text(0) == part:
                    found = item.child(i)
                    break
            if found is None:
                return None
            item = found

        return item

    def _collect_plot_snapshots(self) -> List[PlotSnapshot]:
        snapshots: List[PlotSnapshot] = []
        for index, plot_item in enumerate(self.plot_items):
            plot_info = self.plotData.get(index, {"paths": [], "legends": []})
            paths = [
                [str(component) for component in path]
                for path in plot_info.get("paths", [])
            ]
            legends = [
                [str(component) for component in legend]
                for legend in plot_info.get("legends", [])
            ]
            snapshots.append(
                PlotSnapshot(
                    title=self.ui.tabPlotWidget.tabText(index) or "Plot",
                    paths=paths,
                    legends=legends,
                    canvas=plot_item.capture_canvas_state(),
                )
            )
        return snapshots

    def _collect_visualization_snapshot(self) -> VisualizationSnapshot:
        visualization = VisualizationSnapshot()

        if self.signal_provider is None:
            return visualization

        for key, path in self.signal_provider.export_registered_3d_points().items():
            visualization.points.append(
                {
                    "key": key,
                    "path": list(path),
                    "color": self.visualized_3d_points_colors.get(key),
                }
            )

        for (
            key,
            path,
        ) in self.signal_provider.export_registered_3d_trajectories().items():
            visualization.trajectories.append(
                {
                    "key": key,
                    "path": list(path),
                    "color": self.visualized_3d_trajectories_colors.get(key),
                }
            )

        for key, path in self.signal_provider.export_registered_3d_arrows().items():
            visualization.arrows.append(
                {
                    "key": key,
                    "path": list(path),
                    "color": self.visualized_3d_arrows_colors.get(key),
                }
            )

        visualization.robot_state = {
            "base_position_path": list(self.robot_state_path.base_position_path),
            "base_orientation_path": list(self.robot_state_path.base_orientation_path),
            "joints_state_path": list(self.robot_state_path.joints_state_path),
        }
        if getattr(self.meshcat_provider, "base_frame", ""):
            visualization.robot_state["base_frame"] = self.meshcat_provider.base_frame

        return visualization

    def _collect_timeline_snapshot(self) -> TimelineSnapshot:
        if self.signal_provider is None:
            return TimelineSnapshot(
                slider_value=self.ui.timeSlider.value(),
                slider_max=self.ui.timeSlider.maximum(),
            )

        return TimelineSnapshot(
            index=self.signal_provider.index,
            slider_value=self.ui.timeSlider.value(),
            slider_max=self.ui.timeSlider.maximum(),
            is_running=self.signal_provider.state == PeriodicThreadState.running,
            current_time=self.signal_provider.current_time,
        )

    def _apply_base_highlights(
        self, base_position_path: Sequence[str], base_orientation_path: Sequence[str]
    ) -> None:
        selected_color = QtGui.QColor(255, 0, 0, 127)

        if base_position_path:
            item = self._find_variable_tree_item(base_position_path)
            if item is not None:
                item.setBackground(0, QtGui.QBrush(selected_color))

        if base_orientation_path:
            item = self._find_variable_tree_item(base_orientation_path)
            if item is not None:
                item.setBackground(0, QtGui.QBrush(selected_color))

    def _register_snapshot_point(
        self, key: str, path: Sequence[str], color_hex: Optional[str]
    ) -> bool:
        if self.signal_provider is None:
            return False

        item = self._find_variable_tree_item(path)
        if item is None:
            return False

        color_obj = (
            Color(color_hex)
            if color_hex
            else next(self.visualized_3d_points_colors_palette)
        )
        color_hex_value = color_obj.as_hex()

        item.setForeground(0, QtGui.QBrush(QtGui.QColor(color_hex_value)))
        self.meshcat_provider.register_3d_point(
            key, list(color_obj.as_normalized_rgb())
        )
        self.signal_provider.register_3d_point(key, list(path))

        self.visualized_3d_points.add(key)
        self.visualized_3d_points_colors[key] = color_hex_value
        return True

    def _register_snapshot_trajectory(
        self, key: str, path: Sequence[str], color_hex: Optional[str]
    ) -> bool:
        if self.signal_provider is None:
            return False

        item = self._find_variable_tree_item(path)
        if item is None:
            return False

        color_obj = (
            Color(color_hex)
            if color_hex
            else next(self.visualized_3d_points_colors_palette)
        )
        color_hex_value = color_obj.as_hex()

        item.setForeground(0, QtGui.QBrush(QtGui.QColor(color_hex_value)))
        self.meshcat_provider.register_3d_trajectory(
            key, list(color_obj.as_normalized_rgb())
        )
        self.signal_provider.register_3d_trajectory(key, list(path))

        self.visualized_3d_trajectories.add(key)
        self.visualized_3d_trajectories_colors[key] = color_hex_value
        return True

    def _register_snapshot_arrow(
        self, key: str, path: Sequence[str], color_hex: Optional[str]
    ) -> bool:
        if self.signal_provider is None:
            return False

        item = self._find_variable_tree_item(path)
        if item is None:
            return False

        color_obj = (
            Color(color_hex)
            if color_hex
            else next(self.visualized_3d_points_colors_palette)
        )
        color_hex_value = color_obj.as_hex()

        item.setForeground(0, QtGui.QBrush(QtGui.QColor(color_hex_value)))
        self.meshcat_provider.register_3d_arrow(
            key, list(color_obj.as_normalized_rgb())
        )
        self.signal_provider.register_3d_arrow(key, list(path))

        self.visualized_3d_arrows.add(key)
        self.visualized_3d_arrows_colors[key] = color_hex_value
        return True

    def _set_playback_running(self, running: bool) -> None:
        if self.signal_provider is None:
            return

        if running:
            if self.signal_provider.state != PeriodicThreadState.running:
                self.startButton_on_click()
        else:
            if self.signal_provider.state == PeriodicThreadState.running:
                self.pauseButton_on_click()

    def _build_view_snapshot(self) -> ViewSnapshot:
        dataset_provider = "offline"
        dataset_path: Optional[str] = None
        robot_name: Optional[str] = None
        if self.signal_provider is not None:
            robot_name = getattr(self.signal_provider, "robot_name", None)
            if self.signal_provider.provider_type == ProviderType.REALTIME:
                dataset_provider = "realtime"
            else:
                dataset_path = self.loaded_mat_path

        window_snapshot = WindowSnapshot(
            geometry=self._encode_qbytearray(self.saveGeometry()),
            state=self._encode_qbytearray(self.saveState()),
            plot_tab_index=self.ui.tabPlotWidget.currentIndex(),
            main_tab_index=self.ui.tabWidget.currentIndex(),
            meshcat_tab_index=self.ui.meshcatAndVideoTab.currentIndex(),
        )

        metadata = {
            "created_at": datetime.utcnow().isoformat(timespec="seconds"),
            "application": "robot-log-visualizer",
        }

        return ViewSnapshot(
            metadata=metadata,
            dataset=DatasetSnapshot(
                path=dataset_path,
                robot_name=robot_name,
                provider=dataset_provider,
            ),
            window=window_snapshot,
            timeline=self._collect_timeline_snapshot(),
            plots=self._collect_plot_snapshots(),
            tree=TreeSnapshot(
                selected_variables=self._selected_variable_paths(),
                selected_text_logs=self._selected_text_log_paths(),
            ),
            visualization=self._collect_visualization_snapshot(),
        )

    def save_view_snapshot(self) -> None:
        if self.signal_provider is None:
            QMessageBox.information(
                self,
                "Save view snapshot",
                "No dataset is currently loaded. Load a dataset before saving a view.",
            )
            return

        start_dir = str(self._snapshot_start_directory())
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save view snapshot",
            start_dir,
            "View snapshots (*.json)",
        )

        if not file_name:
            return

        snapshot_path = pathlib.Path(file_name)
        if snapshot_path.suffix.lower() != ".json":
            snapshot_path = snapshot_path.with_suffix(".json")

        if snapshot_path.exists():
            answer = QMessageBox.question(
                self,
                "Overwrite snapshot",
                f"The file '{snapshot_path}' already exists. Overwrite it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        snapshot = self._build_view_snapshot()

        try:
            payload = json.dumps(snapshot.to_dict(), indent=2, sort_keys=True)
        except TypeError as exc:  # pragma: no cover - defensive branch
            message = f"Unable to serialise snapshot: {exc}"
            QMessageBox.critical(self, "Save view snapshot", message)
            self.logger.write_to_log(message)
            return

        save_file = QSaveFile(str(snapshot_path))
        if not save_file.open(QIODevice.WriteOnly | QIODevice.Text):
            message = f"Cannot open '{snapshot_path}' for writing."
            QMessageBox.critical(self, "Save view snapshot", message)
            self.logger.write_to_log(message)
            return

        save_file.write(payload.encode("utf-8"))
        if not save_file.commit():  # pragma: no cover - defensive branch
            message = f"Failed to write snapshot to '{snapshot_path}'."
            QMessageBox.critical(self, "Save view snapshot", message)
            self.logger.write_to_log(message)
            return

        self._remember_snapshot_directory(snapshot_path.parent)
        self.logger.write_to_log(f"Snapshot saved to '{snapshot_path}'.")

    def _ensure_dataset_for_snapshot(
        self, snapshot: ViewSnapshot, *, quiet: bool = False
    ) -> bool:
        provider_mode = (snapshot.dataset.provider or "offline").lower()

        if provider_mode == "realtime":
            QMessageBox.warning(
                self,
                "Load view snapshot",
                "Snapshots captured from real-time sessions cannot be restored yet.",
            )
            self.logger.write_to_log(
                "Realtime snapshot restoration is not supported; aborting load."
            )
            return False

        expected_path = snapshot.dataset.path

        # If no dataset is currently loaded and no path is provided, ask the user.
        if not expected_path:
            if self.dataset_loaded:
                return True
            replacement, _ = QFileDialog.getOpenFileName(
                self,
                "Select dataset for snapshot",
                str(self._snapshot_start_directory()),
                "MAT files (*.mat)",
            )
            if not replacement:
                self.logger.write_to_log(
                    "Snapshot restoration cancelled: dataset selection skipped."
                )
                return False
            return self._load_mat_file(replacement)

        expected_path_obj = pathlib.Path(expected_path).expanduser()
        expected_exists = expected_path_obj.exists()

        if not expected_exists:
            warning = f"Dataset '{expected_path_obj}' referenced in the snapshot could not be found."
            if not quiet:
                QMessageBox.warning(self, "Load view snapshot", warning)
            self.logger.write_to_log(warning)

        user_choice = None
        if not quiet:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle("Load dataset")
            if expected_exists:
                msg_box.setText(
                    "The snapshot references the dataset:\n" f"{expected_path_obj}"
                )
            else:
                msg_box.setText("The dataset referenced in the snapshot was not found.")
            msg_box.setInformativeText(
                "Yes: load the referenced dataset.\n"
                "No: choose a different dataset.\n"
                "Cancel: keep the current dataset."
            )
            msg_box.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            msg_box.setDefaultButton(QMessageBox.Yes)
            user_choice = msg_box.exec_()
        else:
            user_choice = QMessageBox.Yes if expected_exists else QMessageBox.No

        if user_choice == QMessageBox.Cancel:
            if self.dataset_loaded:
                self.logger.write_to_log(
                    "Snapshot dataset load skipped by user; keeping current dataset."
                )
                return True
            self.logger.write_to_log(
                "Snapshot restoration cancelled: no dataset loaded."
            )
            return False

        if user_choice == QMessageBox.Yes and expected_exists:
            if self.dataset_loaded and self.loaded_mat_path == str(expected_path_obj):
                return True
            if self._load_mat_file(str(expected_path_obj)):
                return True
            self.logger.write_to_log(
                f"Snapshot restoration cancelled: failed to load '{expected_path_obj}'."
            )
            return False

        # Either user selected "No" or the referenced dataset is missing -> prompt for replacement.
        replacement_dir = (
            expected_path_obj.parent
            if expected_path_obj.parent.exists()
            else self._snapshot_start_directory()
        )
        replacement, _ = QFileDialog.getOpenFileName(
            self,
            "Select dataset",
            str(replacement_dir),
            "MAT files (*.mat)",
        )
        if not replacement:
            self.logger.write_to_log(
                "Snapshot restoration cancelled: replacement dataset not selected."
            )
            return False

        if self._load_mat_file(replacement):
            return True

        self.logger.write_to_log(
            f"Snapshot restoration cancelled: failed to load '{replacement}'."
        )
        return False

    def _apply_view_snapshot(self, snapshot: ViewSnapshot) -> None:
        window_snapshot = snapshot.window
        geometry = self._decode_qbytearray(window_snapshot.geometry)
        if geometry is not None:
            self.restoreGeometry(geometry)
        state = self._decode_qbytearray(window_snapshot.state)
        if state is not None:
            self.restoreState(state)

        # Ensure the requested number of plot tabs and clear existing data.
        plot_snapshots = snapshot.plots or []
        self._ensure_plot_tab_count(len(plot_snapshots))
        self.plotData.clear()
        for plot_item in self.plot_items:
            plot_item.clear_canvas()

        missing_curves: set[str] = set()
        missing_annotations: set[str] = set()

        for index, plot_snapshot in enumerate(plot_snapshots):
            plot_item = self.plot_items[index]

            paths = [
                [str(component) for component in path] for path in plot_snapshot.paths
            ]
            legends = [
                [str(component) for component in legend]
                for legend in plot_snapshot.legends
            ]

            self.plotData[index] = {"paths": paths, "legends": legends}

            missing = plot_item.canvas.update_plots(paths, legends)
            if missing:
                missing_curves.update(missing)

            missing_ann = plot_item.apply_canvas_state(plot_snapshot.canvas)
            if missing_ann:
                missing_annotations.update(missing_ann)

            self.ui.tabPlotWidget.setTabText(index, plot_snapshot.title)

        # Restore selections in the variable tree (plots).
        missing_variable_paths: List[str] = []
        self.ui.variableTreeWidget.clearSelection()
        for path in snapshot.tree.selected_variables:
            item = self._find_variable_tree_item(path)
            if item is None:
                missing_variable_paths.append("/".join(map(str, path)))
                continue
            item.setSelected(True)

        # Restore Meshcat visualisations if a dataset is loaded.
        missing_points: List[str] = []
        missing_trajectories: List[str] = []
        missing_arrows: List[str] = []

        if self.signal_provider is not None:
            self._clear_visualization_items()

            for entry in snapshot.visualization.points:
                key = entry.get("key")
                path = entry.get("path", [])
                color = entry.get("color")
                if not key or not path:
                    continue
                if not self._register_snapshot_point(key, path, color):
                    missing_points.append(str(key))

            for entry in snapshot.visualization.trajectories:
                key = entry.get("key")
                path = entry.get("path", [])
                color = entry.get("color")
                if not key or not path:
                    continue
                if not self._register_snapshot_trajectory(key, path, color):
                    missing_trajectories.append(str(key))

            for entry in snapshot.visualization.arrows:
                key = entry.get("key")
                path = entry.get("path", [])
                color = entry.get("color")
                if not key or not path:
                    continue
                if not self._register_snapshot_arrow(key, path, color):
                    missing_arrows.append(str(key))

            robot_state_info = snapshot.visualization.robot_state or {}
            robot_state_path = RobotStatePath()
            robot_state_path.base_position_path = [
                str(component)
                for component in robot_state_info.get("base_position_path", [])
            ]
            robot_state_path.base_orientation_path = [
                str(component)
                for component in robot_state_info.get("base_orientation_path", [])
            ]
            robot_state_path.joints_state_path = [
                str(component)
                for component in robot_state_info.get("joints_state_path", [])
            ]
            self.robot_state_path = robot_state_path

            base_frame = robot_state_info.get("base_frame")
            if base_frame:
                self.meshcat_provider.base_frame = str(base_frame)

            self._apply_base_highlights(
                self.robot_state_path.base_position_path,
                self.robot_state_path.base_orientation_path,
            )

        # Restore playback state only; keep timeline position on current dataset defaults.
        timeline = snapshot.timeline
        if self.signal_provider is not None:
            self._set_playback_running(timeline.is_running)

        # Restore tab selections (clamp indices to available ranges).
        if self.ui.tabWidget.count() > 0:
            self.ui.tabWidget.setCurrentIndex(
                max(
                    0,
                    min(window_snapshot.main_tab_index, self.ui.tabWidget.count() - 1),
                )
            )
        if self.ui.tabPlotWidget.count() > 0:
            self.ui.tabPlotWidget.setCurrentIndex(
                max(
                    0,
                    min(
                        window_snapshot.plot_tab_index,
                        self.ui.tabPlotWidget.count() - 1,
                    ),
                )
            )
        if self.ui.meshcatAndVideoTab.count() > 0:
            self.ui.meshcatAndVideoTab.setCurrentIndex(
                max(
                    0,
                    min(
                        window_snapshot.meshcat_tab_index,
                        self.ui.meshcatAndVideoTab.count() - 1,
                    ),
                )
            )

        # Report missing artefacts, if any.
        if missing_curves:
            self.logger.write_to_log(
                "Missing signals while restoring plots: "
                + ", ".join(sorted(missing_curves))
            )
        if missing_annotations:
            self.logger.write_to_log(
                "Annotations skipped because their signals were unavailable: "
                + ", ".join(sorted(missing_annotations))
            )
        if missing_variable_paths:
            self.logger.write_to_log(
                "Variables not found for selection: "
                + ", ".join(sorted(missing_variable_paths))
            )
        if missing_points:
            self.logger.write_to_log(
                "3D points not restored: " + ", ".join(sorted(missing_points))
            )
        if missing_trajectories:
            self.logger.write_to_log(
                "3D trajectories not restored: "
                + ", ".join(sorted(missing_trajectories))
            )
        if missing_arrows:
            self.logger.write_to_log(
                "3D arrows not restored: " + ", ".join(sorted(missing_arrows))
            )

    def load_view_snapshot_from_path(
        self, snapshot_path: pathlib.Path | str, *, quiet: bool = False
    ) -> bool:
        path = pathlib.Path(snapshot_path).expanduser()

        try:
            with path.open("r", encoding="utf-8") as handle:
                raw_snapshot = json.load(handle)
        except FileNotFoundError:
            message = f"Snapshot file '{path}' does not exist."
            if not quiet:
                QMessageBox.warning(self, "Load view snapshot", message)
            self.logger.write_to_log(message)
            return False
        except json.JSONDecodeError as exc:
            message = f"Snapshot file '{path}' is not valid JSON: {exc}."
            if not quiet:
                QMessageBox.critical(self, "Load view snapshot", message)
            self.logger.write_to_log(message)
            return False
        except OSError as exc:  # pragma: no cover - filesystem errors
            message = f"Unable to read snapshot '{path}': {exc}."
            if not quiet:
                QMessageBox.critical(self, "Load view snapshot", message)
            self.logger.write_to_log(message)
            return False

        try:
            snapshot = ViewSnapshot.from_dict(raw_snapshot)
        except Exception as exc:  # pragma: no cover - defensive branch
            message = f"Snapshot file '{path}' is not compatible: {exc}."
            if not quiet:
                QMessageBox.critical(self, "Load view snapshot", message)
            self.logger.write_to_log(message)
            return False

        self._remember_snapshot_directory(path.parent)

        if snapshot.version > SNAPSHOT_VERSION:
            warning = (
                f"Snapshot was created with a newer version ({snapshot.version}). "
                "Attempting to load with current version."
            )
            if not quiet:
                QMessageBox.information(self, "Load view snapshot", warning)
            self.logger.write_to_log(warning)

        if not self._ensure_dataset_for_snapshot(snapshot, quiet=quiet):
            return False

        self._apply_view_snapshot(snapshot)
        self.ui.actionSave_View.setEnabled(self.dataset_loaded)
        self.logger.write_to_log(f"Snapshot '{path}' loaded.")
        return True

    def load_view_snapshot(self) -> None:
        start_dir = str(self._snapshot_start_directory())
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load view snapshot",
            start_dir,
            "View snapshots (*.json)",
        )

        if not file_name:
            return

        self.load_view_snapshot_from_path(file_name)

    def _load_mat_file(self, file_name: str, *, quiet: bool = False) -> bool:
        file_path = pathlib.Path(file_name).expanduser()

        if not file_path.exists():
            message = f"File '{file_path}' not found."
            if not quiet:
                self.logger.write_to_log(message)
                QMessageBox.warning(self, "Load dataset", message)
            return False

        self._prepare_for_new_dataset()

        provider = MatfileSignalProvider(
            self.signal_provider_period, "robot_logger_device"
        )

        try:
            provider.open(str(file_path))
        except Exception as exc:  # pragma: no cover - defensive
            message = f"Unable to read '{file_path}': {exc}"
            if not quiet:
                self.logger.write_to_log(message)
                QMessageBox.critical(self, "Load dataset", message)
            return False

        self.signal_provider = provider
        self.signal_size = len(provider)
        provider.start()

        provider.register_update_index(self.update_index)

        for plot_item in self.plot_items:
            plot_item.set_signal_provider(provider)

        # load the model and load the provider
        self.meshcat_provider.set_signal_provider(provider)
        if not self.meshcat_provider.load_model(
            provider.joints_name, provider.robot_name
        ):
            msg = "Unable to load the model: "
            if self.meshcat_provider.model_path:
                msg += self.meshcat_provider.model_path
            else:
                msg += provider.robot_name
            self.logger.write_to_log(msg)

        self.meshcat_provider.start()

        # populate tree
        root = list(provider.data.keys())[0]
        root_item = QTreeWidgetItem([root])
        root_item.setFlags(root_item.flags() & ~Qt.ItemIsSelectable)
        items = self.__populate_variable_tree_widget(provider.data[root], root_item)
        self.ui.variableTreeWidget.insertTopLevelItems(0, [items])

        # populate text logging tree
        if provider.text_logging_data:
            root = list(provider.text_logging_data.keys())[0]
            root_item = QTreeWidgetItem([root])
            root_item.setFlags(root_item.flags() & ~Qt.ItemIsSelectable)
            items = self.__populate_text_logging_tree_widget(
                provider.text_logging_data[root], root_item
            )
            self.ui.yarpTextLogTreeWidget.insertTopLevelItems(0, [items])

        # spawn the console
        self.pyconsole.push_local_ns("data", provider.data)

        self.ui.timeSlider.setMaximum(self.signal_size)
        self.ui.timeSlider.setValue(0)
        self.ui.startButton.setEnabled(True)
        self.ui.pauseButton.setEnabled(False)
        self.ui.timeSlider.setEnabled(True)

        # get all the videos associated to the dataset
        filename_without_path = file_path.name
        prefix, _, _ = filename_without_path.rpartition(".")

        video_filenames = [
            file_path.parent / pathlib.Path(f)
            for f in os.listdir(file_path.parent)
            if re.search(prefix + r"_[a-zA-Z0-9_]*\.mp4$", f)
        ]

        for video_filename in video_filenames:
            video_prefix, _, _ = video_filename.name.rpartition(".")
            video_label = str(video_prefix).replace(prefix + "_", "")
            video_item = VideoItem(video_filename=str(video_filename))
            self.video_items.append(video_item)
            self.ui.meshcatAndVideoTab.addTab(
                video_item, get_icon("videocam-outline.svg"), video_label
            )
            self.logger.write_to_log(f"Video '{video_filename}' opened.")

        for video_item in self.video_items:
            if video_item.media_loaded:
                video_item.media_player.pause()

        self.meshcat_provider.state = PeriodicThreadState.running
        self.ui.actionRealtime_Connect.setEnabled(False)

        self.dataset_loaded = True
        self.loaded_mat_path = str(file_path)
        self.ui.actionSave_View.setEnabled(True)

        self.logger.write_to_log(f"File '{file_path}' opened.")
        self.logger.write_to_log(f"Robot name: '{provider.robot_name}'.")
        return True

    def open_mat_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open a mat file", ".", filter="*.mat"
        )
        if file_name:
            self._load_mat_file(file_name)
            return True
        return False

    def connect_realtime_logger(self):
        self.signal_provider = RealtimeSignalProvider(
            self.signal_provider_period, "robot_realtime"
        )
        self.realtime_connection_enabled = True

        # Do initial connection to populate the necessary data
        if not self.signal_provider.open("/yarp-robot-logger/rt_logging"):
            self.logger.write_to_log("Could not connect to the real-time logger.")
            self.realtime_connection_enabled = False
            self.signal_provider = None
            return
        # only display one root in the gui
        root = list(self.signal_provider.data.keys())[0]
        root_item = QTreeWidgetItem([root])
        root_item.setFlags(root_item.flags() & ~Qt.ItemIsSelectable)
        items = self.__populate_variable_tree_widget(
            self.signal_provider.data[root], root_item
        )
        self.ui.variableTreeWidget.insertTopLevelItems(0, [items])

        if not self.meshcat_provider.load_model(
            self.signal_provider.joints_name, self.signal_provider.robot_name
        ):
            # if not loaded we print an error but we continue
            msg = "Unable to load the model: "
            if self.meshcat_provider.model_path:
                msg = msg + self.meshcat_provider.model_path
            else:
                msg = msg + self.signal_provider.robot_name

            self.logger.write_to_log(msg)

        # Disable these buttons for RT communication
        self.ui.startButton.setEnabled(False)
        self.ui.timeSlider.setEnabled(False)

        # start the threads accordingly
        self.signal_provider.state = PeriodicThreadState.running
        self.signal_provider.start()
        self.meshcat_provider.set_signal_provider(self.signal_provider)
        self.meshcat_provider.state = PeriodicThreadState.running
        self.meshcat_provider.start()
        for plot in self.plot_items:
            plot.set_signal_provider(self.signal_provider)

    def open_about(self):
        self.about.show()

    def open_set_robot_model(self):
        dlg = SetRobotModelDialog(
            self.meshcat_provider,
            self,
            self.dataset_loaded,
        )
        outcome = dlg.exec_()
        if outcome == QDialog.Accepted:

            # check which button was clicked
            button_role = dlg.get_clicked_button_role()
            button_text = dlg.get_clicked_button_text()
            std_button = dlg.get_clicked_standard_button()

            if std_button == QtWidgets.QDialogButtonBox.SaveAll:
                if not self.dataset_loaded:
                    self.meshcat_provider.model_path = dlg.get_urdf_path()
                    self.meshcat_provider.custom_package_dir = (
                        dlg.get_package_directory()
                    )

                arrow_scaling_value = dlg.ui.arrowScaling_lineEdit.text()
                if not arrow_scaling_value:
                    arrow_scaling_value = "1.0"
                else:
                    arrow_scaling_value = float(arrow_scaling_value)
                self.signal_provider.set_custom_max_arrow(
                    not dlg.ui.arrowScaling_checkBox.isChecked(), arrow_scaling_value
                )
            if std_button == QtWidgets.QDialogButtonBox.Save:
                # we need to check which tab is selected in the dlg
                if dlg.ui.tabWidget.currentIndex() == 0:
                    if not self.dataset_loaded:
                        self.meshcat_provider.model_path = dlg.get_urdf_path()
                        self.meshcat_provider.custom_package_dir = (
                            dlg.get_package_directory()
                        )
                else:
                    arrow_scaling_value = dlg.ui.arrowScaling_lineEdit.text()
                    # if it is empty we set it to 1.0
                    if not arrow_scaling_value:
                        arrow_scaling_value = "1.0"
                    else:
                        arrow_scaling_value = float(arrow_scaling_value)
                    self.signal_provider.set_custom_max_arrow(
                        not dlg.ui.arrowScaling_checkBox.isChecked(),
                        arrow_scaling_value,
                    )

            else:
                self.meshcat_provider.load_model(
                    self.signal_provider.joints_name,
                    self.signal_provider.robot_name,
                    base_frame=dlg.ui.frameNameComboBox.currentText(),
                )

    def dropEvent(self, event):
        if len(event.mimeData().urls()) != 1:
            event.ignore()

        url = event.mimeData().urls()[0].toLocalFile()
        ext = os.path.splitext(url)[-1].lower()
        if ext == ".mat":
            self._load_mat_file(url)
            event.accept()
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def variableTreeWidget_on_right_click(self, item_position):
        # check if the variable tree widget is empty
        if self.ui.variableTreeWidget.topLevelItemCount() == 0:
            menu = QtWidgets.QMenu()
            menu.addAction("Open a mat file")
            action = menu.exec_(self.ui.variableTreeWidget.mapToGlobal(item_position))
            if action is None:
                return
            if action.text() == "Open a mat file":
                self.open_mat_file()

            return

        # find the item from the position
        item = self.ui.variableTreeWidget.itemAt(item_position)
        if item is None:
            return

        if item.childCount() == 0:
            return

        # the child has to be a leaf
        if item.child(0).childCount() != 0:
            return

        # check the number of children
        item_size = item.childCount()
        item_path = self.get_item_path(item)
        item_key = "/".join(item_path)

        menu = QtWidgets.QMenu()

        add_3d_point_str = "Show as a 3D point"
        add_3d_trajectory_str = "Show as a 3D trajectory"
        add_3d_arrow_str = "Show as a 3D arrow"
        remove_3d_point_str = "Remove the 3D point"
        remove_3d_trajectory_str = "Remove the 3D trajectory"
        remove_3d_arrow_str = "Remove the 3D arrow"
        use_as_base_position_str = "Use as base position"
        use_as_base_orientation_str = "Use as base orientation"
        dont_use_as_base_position_str = "Don't use as base position"
        dont_use_as_base_orientation_str = "Don't use as base orientation"
        selected_base_color = QtGui.QColor(255, 0, 0, 127)
        deselected_base_color = QtGui.QColor(0, 0, 0, 0)

        # in this case we can use the item as 3d point where the z coordinate is set to 0
        if item_size == 2:
            if item_key in self.visualized_3d_points:
                menu.addAction(remove_3d_point_str)
            if item_key in self.visualized_3d_trajectories:
                menu.addAction(remove_3d_trajectory_str)
            if (
                item_key not in self.visualized_3d_points
                and item_key not in self.visualized_3d_trajectories
            ):
                menu.addAction(add_3d_point_str)
                menu.addAction(add_3d_trajectory_str)

        # in this case we can use the item as base position, base orientation or 3d point
        if item_size == 3:
            if item_path == self.robot_state_path.base_position_path:
                menu.addAction(dont_use_as_base_position_str)
            else:
                menu.addAction(use_as_base_position_str)

            if item_path == self.robot_state_path.base_orientation_path:
                menu.addAction(dont_use_as_base_orientation_str)
            else:
                menu.addAction(use_as_base_orientation_str + " (Roll-Pitch-Yaw)")

            menu.addSeparator()

            if item_key in self.visualized_3d_points:
                menu.addAction(remove_3d_point_str)
            if item_key in self.visualized_3d_trajectories:
                menu.addAction(remove_3d_trajectory_str)
            if (
                item_key not in self.visualized_3d_points
                and item_key not in self.visualized_3d_trajectories
            ):
                menu.addAction(add_3d_point_str)
                menu.addAction(add_3d_trajectory_str)

        if item_size == 4:
            if item_path == self.robot_state_path.base_orientation_path:
                menu.addAction(dont_use_as_base_orientation_str)
            else:
                menu.addAction(use_as_base_orientation_str + " (xyzw Quaternion)")

        if item_size == 6:
            if item_key in self.visualized_3d_arrows:
                menu.addAction(remove_3d_arrow_str)
            else:
                menu.addAction(add_3d_arrow_str)

        # show the menu
        action = menu.exec_(self.ui.variableTreeWidget.mapToGlobal(item_position))
        if action is None:
            return

        item_path = self.get_item_path(item)

        if (
            action.text() == add_3d_point_str
            or action.text() == add_3d_trajectory_str
            or action.text() == add_3d_arrow_str
        ):
            color = next(self.visualized_3d_points_colors_palette)

            item.setForeground(0, QtGui.QBrush(QtGui.QColor(color.as_hex())))

            if action.text() == add_3d_point_str:
                self.meshcat_provider.register_3d_point(
                    item_key, list(color.as_normalized_rgb())
                )
                self.signal_provider.register_3d_point(item_key, item_path)
                self.visualized_3d_points.add(item_key)
                self.visualized_3d_points_colors[item_key] = color.as_hex()
            elif action.text() == add_3d_trajectory_str:
                self.meshcat_provider.register_3d_trajectory(
                    item_key, list(color.as_normalized_rgb())
                )
                self.signal_provider.register_3d_trajectory(item_key, item_path)
                self.visualized_3d_trajectories.add(item_key)
                self.visualized_3d_trajectories_colors[item_key] = color.as_hex()
            elif action.text() == add_3d_arrow_str:
                self.meshcat_provider.register_3d_arrow(
                    item_key, list(color.as_normalized_rgb())
                )
                self.signal_provider.register_3d_arrow(item_key, item_path)
                self.visualized_3d_arrows.add(item_key)
                self.visualized_3d_arrows_colors[item_key] = color.as_hex()
            else:
                raise ValueError("Unknown action")

        if action.text() == remove_3d_point_str:
            self.meshcat_provider.unregister_3d_point(item_key)
            self.signal_provider.unregister_3d_point(item_key)
            self.visualized_3d_points.remove(item_key)
            self.visualized_3d_points_colors.pop(item_key, None)
            item.setForeground(0, QtGui.QBrush(QtGui.QColor(0, 0, 0)))

        if action.text() == remove_3d_trajectory_str:
            self.meshcat_provider.unregister_3d_trajectory(item_key)
            self.signal_provider.unregister_3d_trajectory(item_key)
            self.visualized_3d_trajectories.remove(item_key)
            self.visualized_3d_trajectories_colors.pop(item_key, None)
            item.setForeground(0, QtGui.QBrush(QtGui.QColor(0, 0, 0)))

        if action.text() == remove_3d_arrow_str:
            self.meshcat_provider.unregister_3d_arrow(item_key)
            self.signal_provider.unregister_3d_arrow(item_key)
            self.visualized_3d_arrows.remove(item_key)
            self.visualized_3d_arrows_colors.pop(item_key, None)
            item.setForeground(0, QtGui.QBrush(QtGui.QColor(0, 0, 0)))

        if (
            use_as_base_orientation_str in action.text()
            or action.text() == use_as_base_position_str
        ):
            item.setBackground(0, QtGui.QBrush(selected_base_color))

        # check that the action is the one we want
        if action.text() == use_as_base_position_str:
            # if base position is already set we remove the color
            if self.robot_state_path.base_position_path:
                self.get_item_from_path(
                    self.robot_state_path.base_position_path
                ).setBackground(0, QtGui.QBrush(deselected_base_color))
            self.robot_state_path.base_position_path = item_path
            # In real time mode, add those signal to the provider buffer
            if (
                self.signal_provider
                and self.signal_provider.provider_type == ProviderType.REALTIME
            ):
                # Convert item_path to signal name string
                signal_name = "robot_realtime::" + "::".join(item_path)
                self.signal_provider.add_signals_to_buffer([signal_name])

        if use_as_base_orientation_str in action.text():
            # if base orientation is already set we remove the color
            if self.robot_state_path.base_orientation_path:
                self.get_item_from_path(
                    self.robot_state_path.base_orientation_path
                ).setBackground(0, QtGui.QBrush(deselected_base_color))
            self.robot_state_path.base_orientation_path = item_path
            # In real time mode, add those signal to the provider buffer
            if (
                self.signal_provider
                and self.signal_provider.provider_type == ProviderType.REALTIME
            ):
                signal_name = "robot_realtime::" + "::".join(item_path)
                self.signal_provider.add_signals_to_buffer([signal_name])

        if action.text() == dont_use_as_base_position_str:
            self.robot_state_path.base_position_path = []
            # if the item is used as base orientation we do not remove the color
            if item_path != self.robot_state_path.base_orientation_path:
                item.setBackground(0, QtGui.QBrush(deselected_base_color))

        if action.text() == dont_use_as_base_orientation_str:
            self.robot_state_path.base_orientation_path = []
            # if the item is used as base position we do not remove the color
            if item_path != self.robot_state_path.base_position_path:
                item.setBackground(0, QtGui.QBrush(deselected_base_color))

        # we update the robot state path
        self.signal_provider.robot_state_path = self.robot_state_path

    def get_item_from_path(self, path):
        item = self.ui.variableTreeWidget.topLevelItem(0)
        for subpath in path:
            # find the item given its name
            for child_id in range(item.childCount()):
                if item.child(child_id).text(0) == subpath:
                    item = item.child(child_id)
                    break
        return item

    def get_item_path(self, item):
        path = []
        while item.parent() is not None:
            path.append(item.text(0))
            item = item.parent()
        path.reverse()
        return path


class Logger:
    """
    Logger class shows events during the execution of the viewer.
    """

    def __init__(self, log_widget, scroll_area, add_time=True):
        # set log widget from main window
        self.log_widget = log_widget

        # set scroll area form main window
        self.scroll_area = scroll_area

        self.add_time = add_time

    def write_to_log(self, text, font_color=None, background_color=None):
        """
        Log the text "text" with a timestamp.
        """

        # extract current text from the log widget
        current_text = self.log_widget.text()

        if font_color is not None:
            text = '<font color="' + str(font_color) + '">' + text + "</font>"

        if background_color is not None:
            text = (
                '<span style="background-color:'
                + str(background_color)
                + '">'
                + text
                + "</span>"
            )

        # compose new text
        # convert local time to string
        if self.add_time:
            time_str = strftime(" [%H:%M:%S] ", localtime())
            #
            new_text = current_text + time_str + text + "<br>"
        else:
            new_text = current_text + text + "<br>"

        # log into the widget
        self.log_widget.setText(new_text)

        # scroll down text
        self.scroll_down()

    def clean(self):
        self.log_widget.clear()

    def scroll_down(self):
        """
        Scroll down the slider of the scroll area
        linked to this logger
        """
        # extract scroll bar from the scroll area
        scroll_bar = self.scroll_area.verticalScrollBar()

        # set maximum value of the slider, 1000 is enough
        scroll_bar.setMaximum(1000)
        scroll_bar.setValue(scroll_bar.maximum())


if __name__ == "__main__":
    # construct a QApplication
    app = QtWidgets.QApplication(sys.argv)

    # instantiate the main window and add the Matplotlib canvas
    gui = RobotViewerMainWindow()

    # show the main window
    gui.show()

    exec_method = getattr(app, "exec", None)
    if exec_method is None:
        exec_method = app.exec_

    sys.exit(exec_method())
