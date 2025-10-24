# Copyright (C) 2025 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# BSD 3-Clause License

import time
import traceback
from collections import deque
from typing import Iterable, Union

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
        """
        Append a value to the deque associated with the given key.
        Args:
            key (str): The key for the deque ('data' or 'timestamps').
            value: The value to append.
        """
        super().__getitem__(key).append(value)

    def get_raw(self, key):
        """
        Get the raw deque object for the given key.
        Args:
            key (str): The key for the deque ('data' or 'timestamps').
        Returns:
            deque: The raw deque object.
        """
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
        Set the value for the given key. For non-'data'/'timestamps' keys, sets normally.
        Args:
            key (str): The key to set.
            value: The value to set.
        """
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

        # Track signals to buffer
        self.buffered_signals = set()
        # Always include joints_state
        self.buffered_signals.add("robot_realtime::joints_state::positions")

    # TODO: implement a logic to remove signals that are not needed anymore
    def add_signals_to_buffer(self, signals: Union[str, Iterable[str]]):
        """Add signals to the buffer set."""
        if isinstance(signals, str):
            signals = {signals}
        self.buffered_signals.update(signals)
        # Always include joints_state
        self.buffered_signals.add("robot_realtime::joints_state::positions")
        print(f"=== Buffered signals updated: {self.buffered_signals} ===")

    def __len__(self):
        """
        Return the number of timestamps in the buffer.
        Returns:
            int: Number of timestamps.
        """
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

        - Creates only missing nested nodes.
        - At a leaf: initialize buffers if missing and merge elements_names
          (do not overwrite existing elements_names).
        - Returns True if the call created or extended metadata for the given path,
          False otherwise.
        """

        if not isinstance(keys, list) or not keys:
            raise ValueError(
                f"Invalid keys parameter: {keys}. Expected a non-empty list."
            )
        if not all(isinstance(k, str) for k in keys):
            raise ValueError(
                f"Invalid keys elements: {keys}. All elements must be strings."
            )

        if not isinstance(raw_data, (dict, DequeToNumpyLeaf)):
            raise ValueError(
                f"Invalid raw_data parameter: {raw_data}. Expected a dictionary-like object."
            )

        if not isinstance(value, (list, tuple, str, int, float)):
            raise ValueError(
                f"Invalid value parameter: {value}. Expected a list, tuple, or scalar."
            )

        if keys[0] == "timestamps":
            return False

        # ensure node exists
        if keys[0] not in raw_data:
            raw_data[keys[0]] = DequeToNumpyLeaf()
            created = True
        else:
            created = False

        if len(keys) == 1:
            # leaf
            if not value:
                # do not delete existing node on empty value; just no-op
                print(f"=== Skipping empty value for key: {keys[0]} ===")
                return created

            node = raw_data[keys[0]]

            # initialize leaf buffers if missing
            if "elements_names" not in node:
                node["elements_names"] = (
                    list(value) if isinstance(value, (list, tuple)) else value
                )
                node["data"] = deque()
                node["timestamps"] = deque()
                print(f"=== Created leaf node for key: {keys[0]} ===")
                return True

            # merge element names (append only new entries)
            if isinstance(node["elements_names"], list) and isinstance(
                value, (list, tuple)
            ):
                added = False
                for v in value:
                    if v not in node["elements_names"]:
                        node["elements_names"].append(v)
                        added = True
                return added or created

            # fallback: if elements_names is not a list, don't overwrite
            return created
        else:
            # recurse into the subtree
            return self._populate_realtime_logger_metadata(
                raw_data[keys[0]], keys[1:], value
            )

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

    @property
    def index(self):
        self.index_lock.lock()
        try:
            # Always return the latest index for real-time mode
            return len(self._timestamps) - 1 if len(self._timestamps) > 0 else 0
        finally:
            self.index_lock.unlock()

    def get_item_from_path_at_index(self, path, index, default_path=None, neighbor=0):
        """
        Get the latest data item from the given path at the latest index.
        Args:
            path: Path to the data item.
            index: Index (ignored, always latest).
            default_path: Default path if not found.
            neighbor: Neighbor offset (currently not handled).
        Returns:
            np.ndarray or None: Latest data item, or None if not available.
        """
        # With respect to the parent implementation, here index is always the latest index
        # TODO: handle case with neighbor > 0
        data, timestamps = self.get_item_from_path(path, default_path)
        if (
            data is None
            or timestamps is None
            or len(self.timestamps) == 0
            or len(timestamps) == 0
        ):
            return None
        return data[-1, :]

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

                        if "alpha" in key_string:
                            print(f"controllerdata alpha gravity value: {value}")

                        # Check if any selected signal starts with this path
                        match = any(
                            sel.startswith(key_string) for sel in self.buffered_signals
                        )
                        if not match:
                            continue

                        keys = key_string.split("::")
                        self._update_data_buffer(
                            self.data, keys, value, recent_timestamp
                        )

                    self.index_lock.unlock()

                # Signal that new data are available.
                self.update_index_signal.emit()

            # Sleep until the next period.
            sleep_time = self.period - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

            if self.state == PeriodicThreadState.closed:
                return
