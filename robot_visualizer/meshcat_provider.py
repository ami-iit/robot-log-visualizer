from PyQt5.QtCore import QThread, QMutex, QMutexLocker

import numpy as np
import time

from utils.utils import PeriodicThreadState


class MeshcatProvider(QThread):
    def __init__(self, meshcat_visualizer, signal_provider, period):
        QThread.__init__(self)

        self._state = PeriodicThreadState.pause
        self.state_lock = QMutex()

        self._period = period
        self._meshcat_visualizer = meshcat_visualizer
        self._signal_provider = signal_provider

    @property
    def state(self):
        locker = QMutexLocker(self.state_lock)
        value = self._state
        return value

    @state.setter
    def state(self, new_state: PeriodicThreadState):
        locker = QMutexLocker(self.state_lock)
        self._state = new_state

    def run(self):
        base_rotation = np.eye(3)
        base_position = np.array([0.0, 0.0, 0.0])

        while True:
            start = time.time()

            if self.state == PeriodicThreadState.running:

                # These are the robot measured joint positions in radians
                joints = self._signal_provider.data['robot_logger_device']['joints_state']['positions']['data']

                self._meshcat_visualizer.set_multy_body_system_state(base_position, base_rotation,
                                                                     joint_value=joints[self._signal_provider.index, :],
                                                                     model_name="robot")

            if self.state == PeriodicThreadState.closed:
                return

            sleep_time = self._period - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)
