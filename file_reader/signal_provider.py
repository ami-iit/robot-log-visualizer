import time
import math

import h5py
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread
from threading import Lock

# Matplotlib class
from plotter.matplotlib_viewer_canvas import MatplotlibViewerCanvas


class SignalProvider(QThread):
    update_index = pyqtSignal()

    def __init__(self, meshcat_visualizer):
        QThread.__init__(self)

        # set device state
        self._state = 'pause'
        self.state_lock = Lock()

        self._last_data = None

        self._index = 0
        self.index_lock = Lock()

        self.fps = 50
        self.meshcat_visualizer = meshcat_visualizer

        self.s = np.array([])

        self.data = {}
        #
        # # Plotter
        # self.mpl_canvas = None

        self.initial_time = math.inf
        self.end_time = - math.inf

    def __populate_data(self, file_object):
        data = {}
        for key, value in file_object.items():
            if not isinstance(value, h5py._hl.group.Group):
                continue
            if key == '#refs#':
                continue
            if 'data' in value.keys():
                data[key] = {}
                data[key]['data'] = np.squeeze(np.array(value['data']))
                data[key]['timestamps'] = np.array(value['timestamps'])
                self.initial_time = min(self.initial_time,data[key]['timestamps'][0])
                self.end_time = max(self.end_time,data[key]['timestamps'][-1])
            else:
                data[key] = self.__populate_data(file_object=value)

        return data

    # def assign_canvas(self, mpl_canvas: MatplotlibViewerCanvas):
    #
    #     self.mpl_canvas = mpl_canvas

    def open_mat_file(self, file_name: str):
        with h5py.File(file_name, 'r') as f:
            self.data = self.__populate_data(f)
            self.s = np.squeeze(np.array(f['robot_logger_device']['joints_state']['positions']['data']))
            self.index = 0

    def __len__(self):
        return self.s.shape[0]

    @property
    def state(self):
        self.state_lock.acquire()
        value = self._state
        self.state_lock.release()
        return value

    @state.setter
    def state(self, new_state):
        self.state_lock.acquire()
        self._state = new_state
        self.state_lock.release()

    @property
    def index(self):
        self.index_lock.acquire()
        value = self._index
        self.index_lock.release()
        return value

    @index.setter
    def index(self, index):
        self.index_lock.acquire()
        self._index = index
        self.index_lock.release()

    def register_update_index(self, slot):
        self.update_index.connect(slot)

    def run(self):
        while True:
            if self.state == 'running':
                temp_index = min(self.index, self.s.shape[0] - 1)
                self._last_data = self.s[temp_index, :]
                self.index = temp_index + int(100/self.fps)
                R = np.eye(3)
                p = np.array([0.0, 0.0, 0.0])
                self.meshcat_visualizer.set_multy_body_system_state(p, R, self._last_data, model_name="robot")
                self.update_index.emit()

            time.sleep(1/self.fps)






