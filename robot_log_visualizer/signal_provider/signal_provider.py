# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

import time
import math
import h5py
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread, QMutex, QMutexLocker
from robot_log_visualizer.utils.utils import PeriodicThreadState, RobotStatePath
import idyntree.swig as idyn
import abc



class TextLoggingMsg:
    def __init__(self, level, text):
        self.level = level
        self.text = text

    def color(self):
        if self.level == "ERROR":
            return "#d62728"
        elif self.level == "WARNING":
            return "#ff7f0e"
        elif self.level == "DEBUG":
            return "#1f77b4"
        elif self.level == "INFO":
            return "#2ca02c"
        else:
            return "black"


class SignalProvider(QThread):
    update_index_signal = pyqtSignal()

    def __init__(self, period: float, signal_root_name: str):
        QThread.__init__(self)

        # set device state
        self._state = PeriodicThreadState.pause
        self.state_lock = QMutex()

        self._index = 0
        self.index_lock = QMutex()

        self._robot_state_path = RobotStatePath()
        self.robot_state_path_lock = QMutex()

        self._3d_points_path = {}
        self._3d_points_path_lock = QMutex()

        self._3d_trajectories_path = {}
        self._3d_trajectories_path_lock = QMutex()

        self.period = period

        self.data = {}
        self.timestamps = np.array([])
        self.text_logging_data = {}

        self.initial_time = math.inf
        self.end_time = -math.inf

        self.joints_name = []
        self.robot_name = ""

        self.root_name = signal_root_name

        self._current_time = 0

        self.trajectory_span = 200

    @abc.abstractmethod
    def open(self, source: str) -> bool:
        return False

    def __len__(self):
        return self.timestamps.shape[0]

    @property
    def state(self):
        locker = QMutexLocker(self.state_lock)
        value = self._state
        return value

    @state.setter
    def state(self, new_state: PeriodicThreadState):
        locker = QMutexLocker(self.state_lock)
        self._state = new_state

    @property
    def index(self):
        locker = QMutexLocker(self.index_lock)
        value = self._index
        return value

    @index.setter
    def index(self, index):
        locker = QMutexLocker(self.index_lock)
        self._index = index

    @property
    def robot_state_path(self):
        locker = QMutexLocker(self.robot_state_path_lock)
        value = self._robot_state_path
        return value

    @robot_state_path.setter
    def robot_state_path(self, robot_state_path):
        locker = QMutexLocker(self.robot_state_path_lock)
        self._robot_state_path = robot_state_path

    def register_update_index(self, slot):
        self.update_index_signal.connect(slot)

    def set_dataset_percentage(self, percentage):
        self.update_index(int(percentage * len(self)))

    def update_index(self, index):
        locker = QMutexLocker(self.index_lock)
        self._index = max(min(index, len(self.timestamps) - 1), 0)
        self._current_time = self.timestamps[self._index] - self.initial_time

    @property
    def current_time(self):
        locker = QMutexLocker(self.index_lock)
        value = self._current_time
        return value

    def get_item_from_path(self, path, default_path=None):
        data = self.data[self.root_name]

        if not path:
            if default_path is None:
                return None, None
            else:
                for key in default_path:
                    data = data[key]
                return data["data"], data["timestamps"]

        for key in path:
            data = data[key]

        return data["data"], data["timestamps"]

    def get_item_from_path_at_index(self, path, index, default_path=None, neighbor=0):
        data, timestamps = self.get_item_from_path(path, default_path)
        if data is None:
            return None
        closest_index = np.argmin(np.abs(timestamps - self.timestamps[index]))

        if neighbor == 0:
            return data[closest_index, :]

        initial_index = max(0, closest_index - neighbor)
        end_index = min(len(timestamps), closest_index + neighbor + 1)
        return data[initial_index:end_index, :]

    def get_robot_state_at_index(self, index):
        robot_state = {}

        self.robot_state_path_lock.lock()
        robot_state["joints_position"] = self.get_item_from_path_at_index(
            self._robot_state_path.joints_state_path,
            index,
            default_path=["joints_state", "positions"],
        )

        robot_state["base_position"] = self.get_item_from_path_at_index(
            self._robot_state_path.base_position_path, index
        )

        robot_state["base_orientation"] = self.get_item_from_path_at_index(
            self._robot_state_path.base_orientation_path, index
        )
        self.robot_state_path_lock.unlock()

        if robot_state["base_position"] is None:
            robot_state["base_position"] = np.zeros(3)

        if robot_state["base_orientation"] is None:
            robot_state["base_orientation"] = np.zeros(3)

        # check the size of the base_orientation if 3 we assume is store ad rpy otherwise as a quaternion we need to convert it in a rotation matrix
        if robot_state["base_orientation"].shape[0] == 3:
            robot_state["base_orientation"] = idyn.Rotation.RPY(
                robot_state["base_orientation"][0],
                robot_state["base_orientation"][1],
                robot_state["base_orientation"][2],
            ).toNumPy()
        if robot_state["base_orientation"].shape[0] == 4:
            # convert the x y z w quaternion into w x y z
            tmp_quat = robot_state["base_orientation"]
            tmp_quat = np.array([tmp_quat[3], tmp_quat[0], tmp_quat[1], tmp_quat[2]])

            robot_state["base_orientation"] = idyn.Rotation.RotationFromQuaternion(
                tmp_quat
            ).toNumPy()

        return robot_state

    def get_3d_point_at_index(self, index):
        points = {}

        self._3d_points_path_lock.lock()

        for key, value in self._3d_points_path.items():
            # force the size of the points to be 3 if less than 3 we assume that the point is a 2d point and we add a 0 as z coordinate
            points[key] = self.get_item_from_path_at_index(value, index)
            if points[key].shape[0] < 3:
                points[key] = np.concatenate(
                    (points[key], np.zeros(3 - points[key].shape[0]))
                )

        self._3d_points_path_lock.unlock()

        return points

    def get_3d_trajectory_at_index(self, index):
        trajectories = {}

        self._3d_trajectories_path_lock.lock()

        for key, value in self._3d_trajectories_path.items():
            trajectories[key] = self.get_item_from_path_at_index(
                value, index, neighbor=self.trajectory_span
            )
            # force the size of the points to be 3 if less than 3 we assume that the point is a 2d point and we add a 0 as z coordinate
            if trajectories[key].shape[1] < 3:
                trajectories[key] = np.concatenate(
                    (
                        trajectories[key],
                        np.zeros(
                            (trajectories[key].shape[0], 3 - trajectories[key].shape[1])
                        ),
                    ),
                    axis=1,
                )

        self._3d_trajectories_path_lock.unlock()

        return trajectories

    def register_3d_point(self, key, points_path):
        self._3d_points_path_lock.lock()
        self._3d_points_path[key] = points_path
        self._3d_points_path_lock.unlock()

    def unregister_3d_point(self, key):
        self._3d_points_path_lock.lock()
        del self._3d_points_path[key]
        self._3d_points_path_lock.unlock()

    def register_3d_trajectory(self, key, trajectory_path):
        self._3d_trajectories_path_lock.lock()
        self._3d_trajectories_path[key] = trajectory_path
        self._3d_trajectories_path_lock.unlock()

    def unregister_3d_trajectory(self, key):
        self._3d_trajectories_path_lock.lock()
        del self._3d_trajectories_path[key]
        self._3d_trajectories_path_lock.unlock()

    def run(self):
        while True:
            start = time.time()
            if self.state == PeriodicThreadState.running:
                self.index_lock.lock()
                tmp_index = self._index
                self._current_time += self.period
                self._current_time = min(
                    self._current_time, self.timestamps[-1] - self.initial_time
                )

                # find the index associated to the current time in self.timestamps
                # this is valid since self.timestamps is sorted and self._current_time is increasing
                while (
                    self._current_time > self.timestamps[tmp_index] - self.initial_time
                ):
                    tmp_index += 1
                    if tmp_index > len(self.timestamps):
                        break

                self._index = tmp_index

                self.index_lock.unlock()

                self.update_index_signal.emit()

            sleep_time = self.period - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

            if self.state == PeriodicThreadState.closed:
                return
