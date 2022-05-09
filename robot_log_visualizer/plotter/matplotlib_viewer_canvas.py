# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

# PyQt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.animation as animation


class MatplotlibViewerCanvas(FigureCanvas):
    """
    Inherits from FigureCanvasQTAgg in order to integrate with PyQt.
    """

    def __init__(self, parent, signal_provider, period):

        # create a new figure
        self.fig = Figure(dpi=100)

        # call FigureCanvas constructor
        FigureCanvas.__init__(self, self.fig)

        # set the parent of this FigureCanvas
        self.setParent(parent)

        # set signal provider
        self.signal_provider = signal_provider

        # setup the plot and the animations
        self.index = 0
        # add plot to the figure
        self.axes = self.fig.add_subplot()
        # set axes labels
        self.axes.set_xlabel("time [s]")
        self.axes.set_ylabel("value")
        self.axes.grid(True)

        # start the vertical line animation
        (self.vertical_line,) = self.axes.plot([], [], "-", lw=1, c="k")

        self.periond_in_ms = int(period * 1000)

        self.vertical_line_anim = animation.FuncAnimation(
            self.fig,
            self.update_vertical_line,
            init_func=self.init_vertical_line,
            interval=self.periond_in_ms,
            blit=True,
        )

        # active paths
        self.active_paths = {}

        # add plot toolbar from matplotlib
        self.toolbar = NavigationToolbar(self, self)

    def quit_animation(self):
        # https://stackoverflow.com/questions/32280140/cannot-delete-matplotlib-animation-funcanimation-objects
        # this is to close the event associated to the animation

        # this is required with matplotlib 3.1.2 but not with 3.5.1.
        # However this code will run with both version of matplotlib
        if self.vertical_line_anim:
            self.vertical_line_anim._stop()

    def update_plots(self, paths, legends):

        for path, legend in zip(paths, legends):
            path_string = "/".join(path)
            legend_string = "/".join(legend[1:])

            if path_string not in self.active_paths.keys():

                data = self.signal_provider.data
                for key in path[:-1]:
                    data = data[key]
                try:
                    datapoints = data["data"][:, int(path[-1])]
                except IndexError:
                    # This happens in the case the variable is a scalar.
                    datapoints = data["data"][:]

                timestamps = data["timestamps"] - self.signal_provider.initial_time

                (self.active_paths[path_string],) = self.axes.plot(
                    timestamps, datapoints, label=legend_string
                )

        paths_to_be_canceled = []
        for active_path in self.active_paths.keys():

            path = active_path.split("/")

            if path not in paths:
                paths_to_be_canceled.append(active_path)

        for path in paths_to_be_canceled:
            self.active_paths[path].remove()
            self.active_paths.pop(path)

        self.axes.set_xlim(
            0, self.signal_provider.end_time - self.signal_provider.initial_time
        )

        # Since a new plot has been added/removed we delete the old animation and we create a new one
        # TODO: this part could be optimized
        self.vertical_line_anim._stop()
        self.axes.legend()
        self.vertical_line_anim = animation.FuncAnimation(
            self.fig,
            self.update_vertical_line,
            init_func=self.init_vertical_line,
            interval=self.periond_in_ms,
            blit=True,
        )

    def update_index(self, index):
        self.index = index

    def init_vertical_line(self):
        self.vertical_line.set_data([], [])
        return self.vertical_line, *(self.active_paths.values())

    def update_vertical_line(self, _):
        """
        Update the vertical line
        """
        current_time = self.signal_provider.current_time
        # Draw vertical line at current index

        self.vertical_line.set_data([current_time, current_time], self.axes.get_ylim())
        return self.vertical_line, *(self.active_paths.values())
