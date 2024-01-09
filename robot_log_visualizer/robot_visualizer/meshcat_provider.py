# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

from PyQt5.QtCore import QThread, QMutex, QMutexLocker

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
        self._meshcat_visualizer = MeshcatVisualizer()
        self.meshcat_visualizer_mutex = QMutex()

        self._is_model_loaded = False
        self._signal_provider = signal_provider

        self.custom_model_path = ""
        self.custom_package_dir = ""
        self.env_list = ["GAZEBO_MODEL_PATH", "ROS_PACKAGE_PATH", "AMENT_PREFIX_PATH"]
        self._registered_3d_points = set()

    @property
    def state(self):
        locker = QMutexLocker(self.state_lock)
        value = self._state
        return value

    @state.setter
    def state(self, new_state: PeriodicThreadState):
        locker = QMutexLocker(self.state_lock)
        self._state = new_state

    def register_3d_point(self, point_path, color):
        radius = 0.02
        locker = QMutexLocker(self.meshcat_visualizer_mutex)
        self._registered_3d_points.add(point_path)
        self._meshcat_visualizer.load_sphere(
            radius=radius, color=color, shape_name=point_path
        )

    def unregister_3d_point(self, point_path):
        locker = QMutexLocker(self.meshcat_visualizer_mutex)
        self._registered_3d_points.remove(point_path)
        self._meshcat_visualizer.delete(shape_name=point_path)

    def load_model(self, considered_joints, model_name):
        def get_model_path_from_envs(env_list):
            return [
                Path(f) if (env != "AMENT_PREFIX_PATH") else Path(f) / "share"
                for env in env_list
                if os.getenv(env) is not None
                for f in os.getenv(env).split(os.pathsep)
            ]

        def check_if_model_exist(folder_path, model):
            path = folder_path / Path(model)
            return path.is_dir()

        # Find the index of the model joints in the considered joints
        # This function is required if some of the considered joints are not in the model
        # For instance in underactuated robots
        def find_model_joints(model_name, considered_joints):
            ml = idyn.ModelLoader()
            ml.loadModelFromFile(model_name)
            model_joints_index = []
            model = ml.model()
            number_of_joints = model.getNrOfJoints()
            for i in range(number_of_joints):
                joint_name = model.getJointName(i)
                if joint_name in considered_joints:
                    # find the index of the joint in the considered joints
                    index = considered_joints.index(joint_name)
                    model_joints_index.append(index)

            return model_joints_index

        self._is_model_loaded = False

        # Load the model
        model_loader = idyn.ModelLoader()

        self.model_joints_index = []
        # In this case the user specify the model path
        if self.custom_model_path:
            self.model_joints_index = find_model_joints(
                self.custom_model_path, considered_joints
            )
            considered_model_joints = [
                considered_joints[i] for i in self.model_joints_index
            ]

            model_loader.loadReducedModelFromFile(
                self.custom_model_path,
                considered_model_joints,
                "urdf",
                [self.custom_package_dir],
            )
        else:
            # Attempt to find the model in the envs folders
            model_found_in_env_folders = False

            # Check if the model is in one of the folders specified in the envs
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

            # If the model is not found we exit
            if not model_found_in_env_folders:
                return False

            self.model_joints_index = find_model_joints(
                self.custom_model_path, considered_joints
            )
            considered_model_joints = [
                considered_joints[i] for i in self.model_joints_index
            ]
            model_loader.loadReducedModelFromFile(
                self.custom_model_path, considered_model_joints
            )

        if not model_loader.isValid():
            return False

        self._meshcat_visualizer.load_model(
            model_loader.model(), model_name="robot", color=0.8
        )

        self._is_model_loaded = True

        return True

    def run(self):
        identity = np.eye(3)

        while True:
            start = time.time()

            if self.state == PeriodicThreadState.running and self._is_model_loaded:
                robot_state = self._signal_provider.get_robot_state_at_index(
                    self._signal_provider.index
                )

                self.meshcat_visualizer_mutex.lock()
                # These are the robot measured joint positions in radians
                self._meshcat_visualizer.set_multibody_system_state(
                    base_position=robot_state["base_position"],
                    base_rotation=robot_state["base_orientation"],
                    joint_value=robot_state["joints_position"][self.model_joints_index],
                    model_name="robot",
                )

                for points_path, points in self._signal_provider.get_3d_point_at_index(
                    self._signal_provider.index
                ).items():
                    if points_path not in self._registered_3d_points:
                        continue

                    self._meshcat_visualizer.set_primitive_geometry_transform(
                        position=points, rotation=identity, shape_name=points_path
                    )

                self.meshcat_visualizer_mutex.unlock()

            sleep_time = self._period - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

            if self.state == PeriodicThreadState.closed:
                return

    # For the real-time logger
    def updateMesh(self):
        base_rotation = np.eye(3)
        base_position = np.array([0.0, 0.0, 0.0])

        self._signal_provider.index = len(self._signal_provider.timestamps) - 1
        # These are the robot measured joint positions in radians
        self.meshcat_visualizer.set_multibody_system_state(
            base_position,
            base_rotation,
            joint_value=self._signal_provider.get_joints_position_at_index(
                self._signal_provider.index
            )[self.model_joints_index],
            model_name="robot",
        )
