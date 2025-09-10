# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# BSD 3-Clause License

import time
import traceback
from collections import deque

import numpy as np

from robot_log_visualizer.signal_provider.signal_provider import (
    ProviderType,
    SignalProvider,
)
from robot_log_visualizer.utils.utils import PeriodicThreadState


def are_deps_installed():
    try:
        import bipedal_locomotion_framework.bindings
        import yarp
    except ImportError as e:
        print("Missing dependencies for RealtimeSignalProvider:", e)
        traceback.print_exc()
        return False
    return True


class DequeToNumpyLeaf(dict):
    """
    A dictionary-like object that internally stores "data" and "timestamps"
    as deques for efficient appends/popleft, but returns them as NumPy arrays
    when accessed via dict["data"] or dict["timestamps"].
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def append(self, key, value):
        super().__getitem__(key).append(value)

    def get_raw(self, key):
        return super().__getitem__(key)

    def __getitem__(self, key):
        """
        Intercept requests for 'data' or 'timestamps'.
        Return them as NumPy arrays constructed from the internal deques.
        For any other key, return as a normal dictionary would.
        """
        if key == "data":
            return np.array(super().__getitem__("data"))
        elif key == "timestamps":
            return np.array(super().__getitem__("timestamps"))
        else:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        """
        If you (or code) try to do leaf["data"] = something, you might
        want to do a custom setter. For simplicity, we just set it normally
        for non-'data_deque'/'timestamps_deque' keys.
        """
        # Example logic if you want to intercept "data":
        # if key == "data":
        #     # Convert to deque
        #     self["data_deque"] = deque(value)
        # else:
        super().__setitem__(key, value)


class RealtimeSignalProvider(SignalProvider):
    def __init__(self, period: float, signal_root_name: str):
        """
        Initialize the realtime signal provider.

        - Initializes the network client.
        - Sets up an internal buffer (using deques) to store data within a fixed time window.
        """
        super().__init__(period, signal_root_name, ProviderType.REALTIME)

        if not are_deps_installed():
            raise ImportError(
                "The realtime signal provider requires the bipedal_locomotion_framework and yarp packages."
            )

        # Import realtime-related bindings.
        import bipedal_locomotion_framework.bindings as blf

        self.vector_collections_client = blf.yarp_utilities.VectorsCollectionClient()

        # Time window (in seconds) for the online plot buffer.
        self.realtime_fixed_plot_window = 20
        self.realtime_network_init = False

        # Dictionary for metadata retrieved once from the remote logger.
        self.rt_metadata_dict = {}

        # Global data buffers:
        # - self.data holds the hierarchical data coming from the logger.
        # - self.timestamps holds the timestamps (as a deque) for the global buffer.
        self.data = DequeToNumpyLeaf()
        self._timestamps = deque()

        self.selected_signals = set()  # Track signals to buffer

    def set_selected_signals(self, signals):
        """Update the set of signals to buffer (called by the plotter)."""
        self.selected_signals = set(signals)

    def __len__(self):
        return len(self._timestamps)

    def _update_data_buffer(
        self, raw_data: dict, keys: list, value, recent_timestamp: float
    ):
        """
        Recursively update the data buffers in the raw_data dictionary.
        At a leaf node, the buffer is maintained as two deques:
          - raw_data[key]["data"]
          - raw_data[key]["timestamps"]
        Any sample older than the fixed time window is removed.
        """

        if keys[0] not in raw_data:
            raw_data[keys[0]] = DequeToNumpyLeaf()

        if len(keys) == 1:
            # Leaf node: initialize deques if needed.
            if "data" not in raw_data[keys[0]]:
                raw_data[keys[0]]["data"] = deque()
                raw_data[keys[0]]["timestamps"] = deque()
            raw_data[keys[0]].append("data", value)
            raw_data[keys[0]].append("timestamps", recent_timestamp)
            # Remove old data outside the time window.
            while raw_data[keys[0]].get_raw("timestamps") and (
                recent_timestamp - raw_data[keys[0]].get_raw("timestamps")[0]
                > self.realtime_fixed_plot_window
            ):
                raw_data[keys[0]].get_raw("data").popleft()
                raw_data[keys[0]].get_raw("timestamps").popleft()
        else:
            # Recursive call for nested dictionaries.
            self._update_data_buffer(
                raw_data[keys[0]], keys[1:], value, recent_timestamp
            )

    def _populate_realtime_logger_metadata(self, raw_data: dict, keys: list, value):
        """
        Recursively populate metadata into raw_data.
        Here we simply store metadata (e.g. elements names) into a list.
        """
        if keys[0] == "timestamps":
            return
        if keys[0] not in raw_data:
            raw_data[keys[0]] = DequeToNumpyLeaf()
        if len(keys) == 1:
            if not value:
                if keys[0] in raw_data:
                    del raw_data[keys[0]]
                return
            if "elements_names" not in raw_data[keys[0]]:
                raw_data[keys[0]]["elements_names"] = []
                # Also create empty buffers (which will later be updated in run())
                raw_data[keys[0]]["data"] = deque()
                raw_data[keys[0]]["timestamps"] = deque()

            raw_data[keys[0]]["elements_names"] = value
        else:
            self._populate_realtime_logger_metadata(raw_data[keys[0]], keys[1:], value)

    def open(self, source: str) -> bool:
        """
        Initializes the connection with the remote realtime logger.
        This method retrieves metadata (e.g. joint names, robot name, etc.)
        but does not yet read the realtime data.
        """
        if not self.realtime_network_init:
            # Initialize YARP network and parameters.
            import bipedal_locomotion_framework.bindings as blf
            import yarp

            yarp.Network.init()

            param_handler = blf.parameters_handler.YarpParametersHandler()
            param_handler.set_parameter_string("remote", source)
            param_handler.set_parameter_string("local", "/visualizerInput")
            param_handler.set_parameter_string("carrier", "udp")
            self.vector_collections_client.initialize(param_handler)
            self.vector_collections_client.connect()

            try:
                self.rt_metadata_dict = (
                    self.vector_collections_client.get_metadata().vectors
                )
            except ValueError:
                print(
                    "Error retrieving metadata from the logger. "
                    "Ensure the logger is running and configured for realtime connection."
                )
                return False

            self.realtime_network_init = True
            self.joints_name = self.rt_metadata_dict["robot_realtime::description_list"]
            self.robot_name = self.rt_metadata_dict["robot_realtime::yarp_robot_name"][
                0
            ]

            # Populate metadata into self.data recursively.
            for key_string, value in self.rt_metadata_dict.items():
                keys = key_string.split("::")
                self._populate_realtime_logger_metadata(self.data, keys, value)

            # Remove keys that are not needed for the realtime plotting.
            if self.root_name in self.data:
                self.data[self.root_name].pop("description_list", None)
                self.data[self.root_name].pop("yarp_robot_name", None)

        return True

    @property
    def timestamps(self):
        return np.array(self._timestamps)

    def run(self):
        """
        This is the periodic thread that reads data from the remote realtime logger.
        It:
          - Reads new data.
          - Updates the global timestamp buffer.
          - For each key (except for the timestamps key), updates the data buffers.
          - Emits an update signal to inform the visualizer that new data are available.
        """
        while True:
            start = time.time()
            if self.state == PeriodicThreadState.running:
                # Read the latest data from the realtime logger.
                vc_input = self.vector_collections_client.read_data(True).vectors

                if vc_input:
                    self.index_lock.lock()
                    # Retrieve the most recent timestamp from the input.
                    recent_timestamp = vc_input["robot_realtime::timestamps"][0]
                    self._timestamps.append(recent_timestamp)
                    # Keep the global timestamps within the fixed plot window.
                    while self._timestamps and (
                        recent_timestamp - self._timestamps[0]
                        > self.realtime_fixed_plot_window
                    ):
                        self._timestamps.popleft()

                    # Update initial and end times.
                    if self._timestamps:
                        self.initial_time = self._timestamps[0]
                        self.end_time = self._timestamps[-1]

                    # For signal selected from the user that is in the received data (except timestamps),
                    # update the appropriate buffer.
                    for key_string, value in vc_input.items():
                        if key_string == "robot_realtime::timestamps":
                            continue

                        # Check if any selected signal starts with this path
                        match = any(
                            sel.startswith(key_string) for sel in self.selected_signals
                        )
                        if not match:
                            continue

                        keys = key_string.split("::")
                        self._update_data_buffer(
                            self.data, keys, value, recent_timestamp
                        )

                    self._index = len(self._timestamps) - 1
                    self.index_lock.unlock()

                # Signal that new data are available.
                self.update_index_signal.emit()

            # Sleep until the next period.
            sleep_time = self.period - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

            if self.state == PeriodicThreadState.closed:
                return
