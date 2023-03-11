# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

from PyQt5.QtCore import QThread, QMutex, QMutexLocker

import icub_models

import os
import re
from pathlib import Path

import numpy as np
import time

import idyntree.swig as idyn
from idyntree.visualize import MeshcatVisualizer

from robot_log_visualizer.utils.utils import PeriodicThreadState


class MeshcatProvider(QThread):
    def __init__(self, signal_provider, period):
        QThread.__init__(self)

        self._state = PeriodicThreadState.pause
        self.state_lock = QMutex()

        self._period = period
        self.meshcat_visualizer = MeshcatVisualizer()
        self._signal_provider = signal_provider

        self.custom_model_path = ""
        self.custom_package_dir = ""
        self.env_list = ["GAZEBO_MODEL_PATH", "ROS_PACKAGE_PATH", "AMENT_PREFIX_PATH"]

    @property
    def state(self):
        locker = QMutexLocker(self.state_lock)
        value = self._state
        return value

    @state.setter
    def state(self, new_state: PeriodicThreadState):
        locker = QMutexLocker(self.state_lock)
        self._state = new_state

    def load_model(self, considered_joints, model_name):
        def get_model_path_from_envs(env_list):
            return [
                Path(f) if (env != "AMENT_PREFIX_PATH") else Path(f) / "share"
                for env in env_list
                for f in os.getenv(env).split(os.pathsep)
            ]

        def check_if_model_exist(folder_path, model):
            path = folder_path / Path(model)
            return path.is_dir()

        model_loader = idyn.ModelLoader()

        if self.custom_model_path:
            model_loader.loadReducedModelFromFile(
                self.custom_model_path,
                considered_joints,
                "urdf",
                [self.custom_package_dir],
            )
        else:

            model_found_in_env_folders = False
            for folder in get_model_path_from_envs(self.env_list):
                if check_if_model_exist(folder, model_name):
                    folder_model_path = folder / Path(model_name)
                    model_filenames = [
                        folder_model_path / Path(f)
                        for f in os.listdir(folder_model_path.absolute())
                        if re.search("[a-zA-Z0-9_]*\.urdf", f)
                    ]

                    if model_filenames:
                        model_found_in_env_folders = True
                        self.custom_model_path = str(model_filenames[0])
                        break

            if not model_found_in_env_folders:
                self.custom_model_path = str(icub_models.get_model_file(model_name))

            model_loader.loadReducedModelFromFile(
                self.custom_model_path, considered_joints
            )

        if not model_loader.isValid():
            return False

        self.meshcat_visualizer.load_model(
            model_loader.model(), model_name="robot", color=0.8
        )
        return True

    def run(self):
        base_rotation = np.eye(3)
        base_position = np.array([0.0, 0.0, 0.0])

        while True:
            start = time.time()

            if self.state == PeriodicThreadState.running:
                # These are the robot measured joint positions in radians
                joints = self._signal_provider.data[self._signal_provider.root_name][
                    "joints_state"
                ]["positions"]["data"]

                self.meshcat_visualizer.set_multibody_system_state(
                    base_position,
                    base_rotation,
                    joint_value=joints[self._signal_provider.index, :],
                    model_name="robot",
                )

            sleep_time = self._period - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

            if self.state == PeriodicThreadState.closed:
                return
