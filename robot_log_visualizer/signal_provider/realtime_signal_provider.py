# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

import numpy as np
from robot_log_visualizer.signal_provider.signal_provider import SignalProvider

class RealtimeSignalProvider(SignalProvider):
    def __init__(self, period: float, signal_root_name: str):
        super().__init__(period, signal_root_name)

        import bipedal_locomotion_framework.bindings as blf

        self.initMetadata = False
        self.realtime_fixed_plot_window = 20

        # for networking with the real-time logger
        self.realtime_network_init = False
        self.vector_collections_client = blf.yarp_utilities.VectorsCollectionClient()
        self.rt_metadata_dict = {}

    def __populate_realtime_logger_data(self, raw_data, keys, value, recent_timestamp):
        if keys[0] not in raw_data:
            raw_data[keys[0]] = {}

        if len(keys) == 1:
            raw_data[keys[0]]["data"] = np.append(raw_data[keys[0]]["data"], value).reshape(-1, len(value))
            raw_data[keys[0]]["timestamps"] = np.append(raw_data[keys[0]]["timestamps"], recent_timestamp)

            temp_initial_time = raw_data[keys[0]]["timestamps"][0]
            temp_end_time = raw_data[keys[0]]["timestamps"][-1]
            while temp_end_time - temp_initial_time > self.realtime_fixed_plot_window:
                raw_data[keys[0]]["data"] = np.delete(raw_data[keys[0]]["data"], 0, axis=0)
                raw_data[keys[0]]["timestamps"] = np.delete(raw_data[keys[0]]["timestamps"], 0)
                temp_initial_time = raw_data[keys[0]]["timestamps"][0]
                temp_end_time = raw_data[keys[0]]["timestamps"][-1]

        else:
            self.__populate_realtime_logger_data(raw_data[keys[0]], keys[1:], value, recent_timestamp)

    def __populate_realtime_logger_metadata(self, raw_data, keys, value):
        if keys[0] == "timestamps":
            return
        if keys[0] not in raw_data:
            raw_data[keys[0]] = {}

        if len(keys) == 1:
            if len(value) == 0:
                del raw_data[keys[0]]
                return
            if "elements_names" not in raw_data[keys[0]]:
                raw_data[keys[0]]["elements_names"] = np.array([])
                raw_data[keys[0]]["data"] = np.array([])
                raw_data[keys[0]]["timestamps"] = np.array([])

            raw_data[keys[0]]["elements_names"] = np.append(raw_data[keys[0]]["elements_names"], value)
        else:
            self.__populate_realtime_logger_metadata(raw_data[keys[0]], keys[1:], value)


    def open(self, source) -> bool:
        if not self.realtime_network_init:
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
                self.rt_metadata_dict = self.vector_collections_client.get_metadata().vectors
            except ValueError:
                print("Error in retreiving the metadata from the logger")
                print("Check if the logger is running and configured for realtime connection")
                return False

            self.realtime_network_init = True
            self.joints_name = self.rt_metadata_dict["robot_realtime::description_list"]
            self.robot_name = self.rt_metadata_dict["robot_realtime::yarp_robot_name"][0]
            for key_string, value in self.rt_metadata_dict.items():
                keys = key_string.split("::")
                self.__populate_realtime_logger_metadata(self.data, keys, value)
            del self.data[self.root_name]["description_list"]
            del self.data[self.root_name]["yarp_robot_name"]

        vc_input = self.vector_collections_client.read_data(True).vectors

        if not vc_input:
            return False
        else:
            # Update the timestamps
            recent_timestamp = vc_input["robot_realtime::timestamps"][0]
            self.timestamps = np.append(self.timestamps, recent_timestamp).reshape(-1)
            del vc_input["robot_realtime::timestamps"]

            # Keep the data within the fixed time interval
            while recent_timestamp - self.timestamps[0] > self.realtime_fixed_plot_window:
                self.initial_time = self.timestamps[0]
                self.end_time = self.timestamps[-1]
                self.timestamps = np.delete(self.timestamps, 0).reshape(-1)
            self.initial_time = self.timestamps[0]
            self.end_time = self.timestamps[-1]

            # Store the new data that comes in
            for key_string, value in vc_input.items():
                keys = key_string.split("::")
                self.__populate_realtime_logger_data(self.data, keys, value, recent_timestamp)

            return True


