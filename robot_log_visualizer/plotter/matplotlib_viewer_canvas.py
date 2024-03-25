# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

# PyQt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.animation as animation
from robot_log_visualizer.plotter.color_palette import ColorPalette

import numpy as np
import matplotlib.pyplot as plt


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

        self.annotations = {}
        self.selected_points = {}
        self.frame_legend = None

        # start the vertical line animation
        (self.vertical_line,) = self.axes.plot([], [], "-", lw=1, c="k")

        self.period_in_ms = int(period * 1000)

        # active paths
        self.active_paths = {}

        self.vertical_line_anim = animation.FuncAnimation(
            self.fig,
            self.update_vertical_line,
            init_func=self.init_vertical_line,
            interval=self.period_in_ms,
            blit=True,
        )

        # add plot toolbar from matplotlib
        self.toolbar = NavigationToolbar(self, self)

        # connect an event on click
        self.fig.canvas.mpl_connect("pick_event", self.on_pick)

        self.color_palette = ColorPalette()

    def quit_animation(self):
        # https://stackoverflow.com/questions/32280140/cannot-delete-matplotlib-animation-funcanimation-objects
        # this is to close the event associated to the animation

        # this is required with matplotlib 3.1.2 but not with 3.5.1.
        # However this code will run with both version of matplotlib
        if self.vertical_line_anim:
            self.vertical_line_anim._stop()

    def pause_animation(self):
        self.vertical_line_anim.pause()

    def resume_animation(self):
        self.vertical_line_anim.resume()

    def on_pick(self, event):
        if isinstance(event.artist, plt.Line2D):
            # get the color of the line
            color = event.artist.get_color()

            line_xdata = event.artist.get_xdata()
            line_ydata = event.artist.get_ydata()
            index = event.ind[0]
            x_data = line_xdata[index]
            y_data = line_ydata[index]

            # find the nearest annotated point to the clicked point if yes we assume the user want to remove it
            should_remove = False
            min_distance = float("inf")
            nearest_point = None
            radius = 0.01
            for x, y in self.annotations.keys():
                distance = np.sqrt((x - x_data) ** 2 + (y - y_data) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = (x, y)

            if min_distance < radius:
                x_data, y_data = nearest_point
                should_remove = True

            # Stop the animation
            self.vertical_line_anim._stop()

            if should_remove:
                # Remove the annotation
                self.annotations[(x_data, y_data)].remove()
                del self.annotations[(x_data, y_data)]

                # Remove the point
                self.selected_points[(x_data, y_data)].remove()
                del self.selected_points[(x_data, y_data)]
            else:
                # Otherwise, create a new annotation and change color of the point
                annotation = self.axes.annotate(
                    f"({x_data:.2f}, {y_data:.2f})",
                    xy=(x_data, y_data),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=10,
                    bbox=dict(
                        boxstyle="round,pad=0.3",
                        facecolor=self.frame_legend.get_facecolor(),
                        edgecolor=self.frame_legend.get_edgecolor(),
                        linewidth=self.frame_legend.get_linewidth(),
                    ),
                    color="black",
                )

                self.annotations[(x_data, y_data)] = annotation
                selected_point = self.axes.plot(
                    x_data,
                    y_data,
                    "o",
                    markersize=5,
                    markerfacecolor=color,
                    markeredgecolor="k",
                )
                self.selected_points[(x_data, y_data)] = selected_point[0]

            # Restart the animation
            self.vertical_line_anim = animation.FuncAnimation(
                self.fig,
                self.update_vertical_line,
                init_func=self.init_vertical_line,
                interval=self.period_in_ms,
                blit=True,
            )

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
                    timestamps,
                    datapoints,
                    label=legend_string,
                    picker=True,
                    color=next(self.color_palette),
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

        if not self.frame_legend:
            self.frame_legend = self.axes.legend().get_frame()

        self.vertical_line_anim = animation.FuncAnimation(
            self.fig,
            self.update_vertical_line,
            init_func=self.init_vertical_line,
            interval=self.period_in_ms,
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
        return (
            self.vertical_line,
            *(self.active_paths.values()),
            *(self.selected_points.values()),
            *(self.annotations.values()),
        )
