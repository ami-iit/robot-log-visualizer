# sys
import sys
import os

# GUI
from ui.gui import RobotViewerMainWindow
from PyQt5.QtWidgets import QApplication

from file_reader.signal_provider import SignalProvider

# Meshcat
from idyntree.visualize import MeshcatVisualizer


def get_model_path(robot_name='iCubGazeboV3'):
    seperbuild_prefix = os.environ["ROBOTOLOGY_SUPERBUILD_INSTALL_PREFIX"]
    robots_folder = os.path.join("share", "iCub", "robots", robot_name)

    return os.path.join(seperbuild_prefix, robots_folder, "model.urdf")


def get_joint_list():
    joint_list = ['neck_pitch', 'neck_roll', 'neck_yaw',
                  'torso_pitch', 'torso_roll', 'torso_yaw',
                  'l_shoulder_pitch', 'l_shoulder_roll', 'l_shoulder_yaw', 'l_elbow',
                  'r_shoulder_pitch', 'r_shoulder_roll', 'r_shoulder_yaw', 'r_elbow',
                  'l_hip_pitch', 'l_hip_roll', 'l_hip_yaw', 'l_knee', 'l_ankle_pitch', 'l_ankle_roll',
                  'r_hip_pitch', 'r_hip_roll', 'r_hip_yaw', 'r_knee', 'r_ankle_pitch', 'r_ankle_roll']

    return joint_list


if __name__ == '__main__':
    # instantiate device_manager
    meshcat = MeshcatVisualizer()
    meshcat.set_model_from_file(get_model_path(), get_joint_list())
    meshcat.load_model(color=[1, 1, 1, 0.8])

    signal_provider = SignalProvider(meshcat)

    # instantiate a QApplication
    app = QApplication(sys.argv)

    # instantiate the main window
    gui = RobotViewerMainWindow(meshcat=meshcat, signal_provider=signal_provider)

    # show the main window
    gui.show()

    signal_provider.start()

    sys.exit(app.exec_())


    
