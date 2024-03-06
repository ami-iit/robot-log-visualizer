# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

import sys
import time
import math
import h5py
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread, QMutex, QMutexLocker
from robot_log_visualizer.utils.utils import PeriodicThreadState, RobotStatePath
import idyntree.swig as idyn

import bipedal_locomotion_framework.bindings as blf

# for real-time logging
import yarp
import json


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

    def __init__(self, period: float):
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

        self.root_name = "robot_logger_device"

        self._current_time = 0

        self.realtimeBufferReached = False
        self.initMetadata = False
        self.realtimeFixedPlotWindow = 20

        # for networking with the real-time logger
        self.realtimeNetworkInit = False
        self.vectorCollectionsClient = blf.yarp_utilities.VectorsCollectionClient()
        self.trajectory_span = 200
        self.rtMetadataDict = {}

    def __populate_text_logging_data(self, file_object):
        data = {}
        for key, value in file_object.items():
            if not isinstance(value, h5py._hl.group.Group):
                continue
            if key == "#refs#":
                continue
            if "data" in value.keys():
                data[key] = {}
                level_ref = value["data"]["level"]
                text_ref = value["data"]["text"]

                data[key]["timestamps"] = np.squeeze(np.array(value["timestamps"]))

                # New way to store the struct array in robometry https://github.com/robotology/robometry/pull/175
                if text_ref.shape[0] == len(data[key]["timestamps"]):
                    # If len(value[text[0]].shape) == 2 then the text contains a string, otherwise it is empty
                    # We need to manually check the shape to handle the case in which the text is empty
                    data[key]["data"] = [
                        TextLoggingMsg(
                            text="".join(chr(c[0]) for c in value[text[0]]),
                            level="".join(chr(c[0]) for c in value[level[0]]),
                        )
                        if len(value[text[0]].shape) == 2
                        else TextLoggingMsg(
                            text="",
                            level="".join(chr(c[0]) for c in value[level[0]]),
                        )
                        for text, level in zip(text_ref, level_ref)
                    ]

                # Old approach (before https://github.com/robotology/robometry/pull/175)
                else:
                    data[key]["data"] = [
                        TextLoggingMsg(
                            text="".join(chr(c[0]) for c in value[text]),
                            level="".join(chr(c[0]) for c in value[level]),
                        )
                        for text, level in zip(text_ref[0], level_ref[0])
                    ]

            else:
                data[key] = self.__populate_text_logging_data(file_object=value)

        return data

    def __populate_numerical_data(self, file_object):
        data = {}
        for key, value in file_object.items():
            if not isinstance(value, h5py._hl.group.Group):
                continue
            if key == "#refs#":
                print("Skipping for refs")
                continue
            if key == "log":
                print("Skipping for log")
                continue
            if "data" in value.keys():
                data[key] = {}
                data[key]["data"] = np.squeeze(np.array(value["data"]))
                data[key]["timestamps"] = np.squeeze(np.array(value["timestamps"]))

                # if the initial or end time has been updated we can also update the entire timestamps dataset
                if data[key]["timestamps"][0] < self.initial_time:
                    self.timestamps = data[key]["timestamps"]
                    self.initial_time = self.timestamps[0]

                if data[key]["timestamps"][-1] > self.end_time:
                    self.timestamps = data[key]["timestamps"]
                    self.end_time = self.timestamps[-1]

                # In yarp telemetry v0.4.0 the elements_names was saved.
                if "elements_names" in value.keys():
                    elements_names_ref = value["elements_names"]
                    data[key]["elements_names"] = [
                        "".join(chr(c[0]) for c in value[ref])
                        for ref in elements_names_ref[0]
                    ]

            else:
                data[key] = self.__populate_numerical_data(file_object=value)

        return data

    def __populateRealtimeLoggerData(self, rawData, keys, value, recentTimestamp):
        if keys[0] not in rawData:
            rawData[keys[0]] = {}

        if len(keys) == 1:
            rawData[keys[0]]["data"] = np.append(rawData[keys[0]]["data"], value).reshape(-1, len(value))
            rawData[keys[0]]["timestamps"] = np.append(rawData[keys[0]]["timestamps"], recentTimestamp)

            tempInitialTime = rawData[keys[0]]["timestamps"][0]
            tempEndTime = rawData[keys[0]]["timestamps"][-1]
            while tempEndTime - tempInitialTime > self.realtimeFixedPlotWindow:
                rawData[keys[0]]["data"] = np.delete(rawData[keys[0]]["data"], 0, axis=0)
                rawData[keys[0]]["timestamps"] = np.delete(rawData[keys[0]]["timestamps"], 0)
                tempInitialTime = rawData[keys[0]]["timestamps"][0]
                tempEndTime = rawData[keys[0]]["timestamps"][-1]

        else:
            self.__populateRealtimeLoggerData(rawData[keys[0]], keys[1:], value, recentTimestamp)

    def __populateRealtimeLoggerMetadata(self, rawData, keys, value):
        if keys[0] == "timestamps":
            return
        if keys[0] not in rawData:
            rawData[keys[0]] = {}

        if len(keys) == 1:
            if len(value) == 0:
                del rawData[keys[0]]
                return
            if "elements_names" not in rawData[keys[0]]:
                rawData[keys[0]]["elements_names"] = np.array([])
                rawData[keys[0]]["data"] = np.array([])
                rawData[keys[0]]["timestamps"] = np.array([])

            rawData[keys[0]]["elements_names"] = np.append(rawData[keys[0]]["elements_names"], value)
        else:
            self.__populateRealtimeLoggerMetadata(rawData[keys[0]], keys[1:], value)


    def establish_connection(self):
        if not self.realtimeNetworkInit:
            yarp.Network.init()

            param_handler = blf.parameters_handler.YarpParametersHandler()
            param_handler.set_parameter_string("remote", "/rtLoggingVectorCollections") # you must have some local port as well
            param_handler.set_parameter_string("local", "/visualizerInput") # remote must match the server
            param_handler.set_parameter_string("carrier", "udp")
            self.vectorCollectionsClient.initialize(param_handler)

            self.vectorCollectionsClient.connect()
            self.realtimeNetworkInit = True
            self.rtMetadataDict = self.vectorCollectionsClient.get_metadata().vectors
            if not self.rtMetadataDict:
                print("Failed to read realtime YARP port, closing")
                return False

            self.joints_name = self.rtMetadataDict["robot_realtime::description_list"]
            self.robot_name = self.rtMetadataDict["robot_realtime::yarp_robot_name"][0]
            for keyString, value in self.rtMetadataDict.items():
                keys = keyString.split("::")
                self.__populateRealtimeLoggerMetadata(self.data, keys, value)
            del self.data["robot_realtime"]["description_list"]
            del self.data["robot_realtime"]["yarp_robot_name"]

        input = self.vectorCollectionsClient.read_data(True)

        if not input:
            print("Failed to read realtime YARP port, closing")
            return False
        else:
            # Update the timestamps
            recentTimestamp = input["robot_realtime::timestamps"][0]
            self.timestamps = np.append(self.timestamps, recentTimestamp).reshape(-1)
            del input["robot_realtime::timestamps"]

            # Keep the data within the fixed time interval
            while recentTimestamp - self.timestamps[0] > self.realtimeFixedPlotWindow:
                self.initial_time = self.timestamps[0]
                self.end_time = self.timestamps[-1]
                self.timestamps = np.delete(self.timestamps, 0).reshape(-1)
            self.initial_time = self.timestamps[0]
            self.end_time = self.timestamps[-1]

            # Store the new data that comes in
            for keyString, value in input.items():
                keys = keyString.split("::")
                self.__populateRealtimeLoggerData(self.data, keys, value, recentTimestamp)

            return True

    def open_mat_file(self, file_name: str):
        with h5py.File(file_name, "r") as file:

            root_variable = file.get(self.root_name)
            self.data = self.__populate_numerical_data(file)

            if "log" in root_variable.keys():
                self.text_logging_data["log"] = self.__populate_text_logging_data(
                    root_variable["log"]
                )

            for name in file.keys():
                if "description_list" in file[name].keys():
                    self.root_name = name
                    break

            joint_ref = root_variable["description_list"]
            self.joints_name = [
                "".join(chr(c[0]) for c in file[ref]) for ref in joint_ref[0]
            ]
            if "yarp_robot_name" in root_variable.keys():
                robot_name_ref = root_variable["yarp_robot_name"]
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
