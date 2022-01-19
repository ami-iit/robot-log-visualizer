
# PyQt
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
        self.fig = Figure(dpi=200)

        # call FigureCanvas constructor
        FigureCanvas.__init__(self, self.fig)

        # set the parent of this FigureCanvas
        self.setParent(parent)

        # set signal provider
        self.signal_provider = signal_provider

        # setup the plot and the animations
        self.index = 0
        self.animation_frame_rate = animation_frame_rate
        # add plot to the figure
        self.axes = self.fig.add_subplot()

        # set axes labels
        self.axes.set_xlabel("time [s]")
        self.axes.set_ylabel("value")

        # start the vertical line animation
        self.vertical_line, = self.axes.plot([], [], '-', lw=1, c='k')
        self.vertical_line_anim = animation.FuncAnimation(self.fig, self.update_vertical_line,
                                                          interval=30, blit=True)

        # active paths
        self.active_paths = {}

        # add plot toolbar from matplotlib
        self.toolbar = NavigationToolbar(self, self)

    def quit_animation(self):
        # https://stackoverflow.com/questions/32280140/cannot-delete-matplotlib-animation-funcanimation-objects
        # this is to close the event associated to the animation
        self.vertical_line_anim._stop()

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

    def init_vertical_line(self):
        self.vertical_line.set_data([], [])
        return self.vertical_line,

    def update_vertical_line(self, _):
        """
        Update the vertical line
        """
        current_time = self.signal_provider.current_time
        # Draw vertical line at current index
        self.vertical_line.set_data([current_time, current_time], self.axes.get_ylim())
        return self.vertical_line,

