# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

import time
import math
import h5py
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread, QMutex, QMutexLocker
from robot_log_visualizer.utils.utils import PeriodicThreadState


class SignalProvider(QThread):
    update_index_signal = pyqtSignal()

    def __init__(self, period: float):
        QThread.__init__(self)

        # set device state
        self._state = PeriodicThreadState.pause
        self.state_lock = QMutex()

        self._index = 0
        self.index_lock = QMutex()

        self.period = period

        self.data = {}
        self.timestamps = np.array([])

        self.initial_time = math.inf
        self.end_time = -math.inf

        self.joints_name = []
        self.robot_name = ""

        self._current_time = 0

    def __populate_data(self, file_object):
        data = {}
        for key, value in file_object.items():
            if not isinstance(value, h5py._hl.group.Group):
                continue
            if key == "#refs#":
                continue
            if "data" in value.keys():
                data[key] = {}
                data[key]["data"] = np.squeeze(np.array(value["data"]))
                data[key]["timestamps"] = np.array(value["timestamps"])

                # if the initial or end time has been updated we can also update the entire timestamps dataset
                if data[key]["timestamps"][0] < self.initial_time:
                    self.timestamps = data[key]["timestamps"]
                    self.initial_time = data[key]["timestamps"][0]

                if data[key]["timestamps"][-1] > self.end_time:
                    self.timestamps = data[key]["timestamps"]
                    self.end_time = data[key]["timestamps"][-1]

                # In yarp telemetry v0.4.0 the elements_names was saved.
                if "elements_names" in value.keys():
                    elements_names_ref = value["elements_names"]
                    data[key]["elements_names"] = [
                        "".join(chr(c[0]) for c in value[ref])
                        for ref in elements_names_ref[0]
                    ]
            else:
                data[key] = self.__populate_data(file_object=value)

        return data

    def open_mat_file(self, file_name: str):
        with h5py.File(file_name, "r") as f:
            self.data = self.__populate_data(f)
            joint_ref = f["robot_logger_device"]["description_list"]
            self.joints_name = [
                "".join(chr(c[0]) for c in f[ref]) for ref in joint_ref[0]
            ]
            if "yarp_robot_name" in f["robot_logger_device"].keys():
                robot_name_ref = f["robot_logger_device"]["yarp_robot_name"]
                try:
                    self.robot_name = "".join(chr(c[0]) for c in robot_name_ref)
                except:
                    pass
            self.index = 0

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

    def register_update_index(self, slot):
        self.update_index_signal.connect(slot)

    def update_index(self, index):
        locker = QMutexLocker(self.index_lock)
        self._index = max(min(index, len(self.timestamps) - 1), 0)
        self._current_time = self.timestamps[self._index] - self.initial_time

    @property
    def current_time(self):
        locker = QMutexLocker(self.index_lock)
        value = self._current_time
        return value

    def run(self):

        while True:
            start = time.time()
            if self.state == PeriodicThreadState.running:
                self.index_lock.lock()
                tmp_index = self._index
                # check if index must be increased
                if self._current_time > self.timestamps[tmp_index] - self.initial_time:
                    tmp_index += 1
                    tmp_index = min(tmp_index, self.timestamps.shape[0] - 1)

                self._index = tmp_index
                self._current_time += self.period
                self.index_lock.unlock()

                self.update_index_signal.emit()

            sleep_time = self.period - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

            if self.state == PeriodicThreadState.closed:
                return
