# numpy
import numpy as np

# PyQt
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# matplotilb
from matplotlib.figure import Figure
import matplotlib.animation as animation


class MatplotlibViewerCanvas(FigureCanvas):
    """
    Inherits from FigureCanvasQTAgg in order to integrate with PyQt.
    """

    def __init__(self, parent, animation_frame_rate, signal_provider):

        # create a new figure
        fig = Figure(dpi=100)

        # call FigureCanvas constructor
        FigureCanvas.__init__(self, fig)

        # set the parent of this FigureCanvas
        self.setParent(parent)

        # set signal provider
        self.signal_provider = signal_provider

        # setup the plot and the animations
        self.index = 0
        self.animation_frame_rate = animation_frame_rate
        self.setup_plot(fig)

        # active paths
        self.active_paths = {}

        #add plot toolbar from matplotlib
        self.toolbar = NavigationToolbar(self, self)

    def setup_plot(self, figure):
        """
        Setup the main plot of the figure.
        """

        # add plot to the figure
        self.axes = figure.add_subplot()

        # set axes labels
        self.axes.set_xlabel("time [s]")
        self.axes.set_ylabel("value")

        # Define animations timestep
        time_step = 1.0 / self.animation_frame_rate * 1000

        # start the vertical line animation
        self.vertical_line, = self.axes.plot([], [], 'o-', lw=1, c='k')
        #self.vertical_line_anim = animation.FuncAnimation(figure, self.update_vertical_line, interval=time_step, ) # TODO blit=True

    def update_plots(self, paths):

        for path in paths:
            path_string = '/'.join(path)

            if path_string not in self.active_paths.keys():

                data = self.signal_provider.data
                for key in path[:-1]:
                    data = data[key]
                datapoints = data['data'][:,int(path[-1])]
                timestamps = data['timestamps'] - self.signal_provider.initial_time

                self.active_paths[path_string] = self.axes.plot(timestamps, datapoints, label=path_string)

        paths_to_be_canceled = []

        for active_path in self.active_paths.keys():

            path = active_path.split('/')

            if path not in paths:
                paths_to_be_canceled.append(active_path)

        for path in paths_to_be_canceled:
            self.active_paths[path].pop(0).remove()
            self.active_paths.pop(path)

        self.axes.set_xlim(0, self.signal_provider.end_time - self.signal_provider.initial_time)
        self.axes.legend()
        self.draw()

    def update_index(self, index):
        self.index = index

    def update_vertical_line(self, frame_number):
        """
        Update the vertical line
        """

        # Draw vertical line at current index
        x = [self.index, self.index]
        y = [-1000, 1000]
        self.vertical_line.set_data(x, y)

