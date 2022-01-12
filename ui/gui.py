#PyQt5
from PyQt5 import QtWidgets
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog

import sys

# QtDesigner generated classes
from ui.visualizer import Ui_MainWindow

# for logging
from time import localtime, strftime


class RobotViewerMainWindow(QtWidgets.QMainWindow):
    """
    Main window class of EVB1000 Viewer
    """
    def __init__(self, meshcat: str, signal_provider):
        # call QMainWindow constructor
        super().__init__()

        # set up the user interface
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.signal_provider = signal_provider
        self.signal_size = len(self.signal_provider)
        self.signal_provider.register_update_index(self.update_slider)

        # instantiate the Logger
        self.logger = Logger(self.ui.logLabel, self.ui.logScrollArea)

        self.slider_pressed = False

        # connect action
        self.ui.actionQuit.triggered.connect(self.quit)
        self.ui.actionOpen.triggered.connect(self.open_mat_file)

        self.ui.meshcatView.setUrl(QUrl(meshcat.viewer.url()))

        self.ui.pauseButton.clicked.connect(self.pauseButton_on_click)
        self.ui.startButton.clicked.connect(self.startButton_on_click)
        self.ui.timeSlider.sliderReleased.connect(self.timeSlider_on_release)
        self.ui.timeSlider.sliderPressed.connect(self.timeSlider_on_pressed)

    def timeSlider_on_pressed(self):
        self.slider_pressed = True

    def timeSlider_on_release(self):
        index = int(self.ui.timeSlider.value() / 100 * self.signal_size)
        self.signal_provider.index = index
        self.slider_pressed = False
        self.logger.write_to_log("Dataset index set at " + str(index) + ".")


    def startButton_on_click(self):
        self.ui.startButton.setEnabled(False)
        self.ui.pauseButton.setEnabled(True)
        self.signal_provider.state = "running"

        self.logger.write_to_log("Dataset started.")

    def pauseButton_on_click(self):
        self.ui.pauseButton.setEnabled(False)
        self.ui.startButton.setEnabled(True)
        self.signal_provider.state = "pause"

        self.logger.write_to_log("Dataset paused.")

    @pyqtSlot()
    def update_slider(self):
        if not self.slider_pressed:
            index = 100 * self.signal_provider.index / self.signal_size
            self.ui.timeSlider.setValue(index)

    def quit(self):
        """
        Quit method.

        Method called when actionQuit is triggered.
        """

        # close the window
        self.close()

    def open_mat_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open a mat file", ".", filter='*.mat')
        self.signal_provider.open_mat_file(file_name)
        self.ui.startButton.setEnabled(True)
        self.ui.timeSlider.setEnabled(True)
        self.ui.timeLabel.setEnabled(True)
        self.signal_size = len(self.signal_provider)
        self.logger.write_to_log("File '" + file_name + "' opened.")


class Logger:
    """
    Logger class shows events during the execution of the viewer.
    """

    def __init__(self, log_widget, scroll_area):

        # set log widget from main window
        self.log_widget = log_widget

        # set scroll area form main window
        self.scroll_area = scroll_area

        # print welcome message
        self.write_to_log("Robot Viewer started.")

    def write_to_log(self, text):
        """
        Log the text "text" with a timestamp.
        """

        # extract current text from the log widget
        current_text = self.log_widget.text()

        # compose new text
        # convert local time to string
        time_str = strftime(" [%H:%M:%S] ", localtime())
        #
        new_text = current_text + time_str + text + "\n"

        # log into the widget
        self.log_widget.setText(new_text)

        # scroll down text
        self.scroll_down()

    def scroll_down(self):
        """
        Scroll down the slider of the scroll area
        linked to this logger
        """
        # extract scroll bar from the scroll area
        scroll_bar = self.scroll_area.verticalScrollBar()

        # set maximum value of the slider, 1000 is enough
        scroll_bar.setMaximum(1000)
        scroll_bar.setValue(scroll_bar.maximum())


if __name__ == '__main__':
    # construct a QApplication
    app = QtWidgets.QApplication(sys.argv)

    # instantiate the main window and add the Matplotlib canvas
    gui = RobotViewerMainWindow()

    # show the main window
    gui.show()

    sys.exit(app.exec_())
