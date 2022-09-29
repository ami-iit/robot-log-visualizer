#!/usr/bin/env python3

# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

import sys
import os

# GUI
from robot_log_visualizer.ui.gui import RobotViewerMainWindow
from PyQt5.QtWidgets import QApplication

from robot_log_visualizer.file_reader.signal_provider import SignalProvider

# Meshcat
from robot_log_visualizer.robot_visualizer.meshcat_provider import MeshcatProvider


def main():
    thread_periods = {
        "meshcat_provider": 0.03,
        "signal_provider": 0.03,
        "plot_animation": 0.03,
    }

    # instantiate device_manager
    signal_provider = SignalProvider(period=thread_periods["signal_provider"])

    meshcat_provider = MeshcatProvider(
        period=thread_periods["meshcat_provider"], signal_provider=signal_provider
    )

    # instantiate a QApplication
    app = QApplication(sys.argv)

    # instantiate the main window
    gui = RobotViewerMainWindow(
        signal_provider=signal_provider,
        meshcat_provider=meshcat_provider,
        animation_period=thread_periods["plot_animation"],
    )

    # show the main window
    gui.show()

    signal_provider.start()
    meshcat_provider.start()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
