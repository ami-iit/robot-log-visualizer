# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# Released under the terms of the BSD 3-Clause License

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.animation as animation

from robot_log_visualizer.plotter.color_palette import ColorPalette
from robot_log_visualizer.signal_provider.signal_provider import ProviderType


class MatplotlibViewerCanvas(FigureCanvas):
    """
    A FigureCanvas that shows the plot with two (mutually exclusive) animations:
      - In offline mode, a vertical line is animated (sweeping over the plot).
      - In realtime (online) mode, the plotted data is updated “online”.
    """

    def __init__(self, parent, period):
        # Create the figure
        self.fig = Figure(dpi=100)

        # call FigureCanvas constructor
        FigureCanvas.__init__(self, self.fig)

        # set the parent of this FigureCanvas
        self.setParent(parent)

        # Initially no signal provider
        self.signal_provider = None

        # Basic plot setup
        self.axes = self.fig.add_subplot()
        self.axes.set_xlabel("time [s]")
        self.axes.set_ylabel("value")
        self.axes.grid(True)

        # Data structures to store annotation and selected points
        self.annotations = {}
        self.selected_points = {}
        self.frame_legend = None

        # Plot the vertical line (we will update its position)
        (self.vertical_line,) = self.axes.plot([], [], "-", lw=1, c="k")

        self.period_in_ms = int(period * 1000)

        # Dictionary of active plotted lines
        self.active_paths = {}

        # Here we hold the two possible animations – only one will run.
        self.vertical_line_anim = None
        self.online_plot_anim = None

        # Add the toolbar (for zoom/pan etc.)
        self.toolbar = NavigationToolbar(self, self)

        # Connect the pick event (for selecting points)
        self.fig.canvas.mpl_connect("pick_event", self.on_pick)

        self.color_palette = ColorPalette()

    def start_animation(self):
        """
        Create (or restart) the proper animation depending on the signal provider type.
        Only one of self.vertical_line_anim or self.online_plot_anim will be active.
        """
        if self.signal_provider is None:
            return

        if self.signal_provider.provider_type == ProviderType.REALTIME:
            self.online_plot_anim = animation.FuncAnimation(
                self.fig,
                self.update_online_plot,
                interval=self.period_in_ms,
                blit=True,
            )
        elif self.signal_provider.provider_type == ProviderType.OFFLINE:
            self.vertical_line_anim = animation.FuncAnimation(
                self.fig,
                self.update_vertical_line,
                init_func=self.init_vertical_line,
                interval=self.period_in_ms,
                blit=True,
            )
        else:
            raise ValueError("Unknown provider type")

    def _current_animation(self):
        """Return the animation object that is currently active."""
        if self.signal_provider is None:
            return None
        if self.signal_provider.provider_type == ProviderType.REALTIME:
            return self.online_plot_anim
        elif self.signal_provider.provider_type == ProviderType.OFFLINE:
            return self.vertical_line_anim
        else:
            raise ValueError("Unknown provider type")

    def set_signal_provider(self, signal_provider):
        """
        Store the signal provider and start the proper animation.
        The signal provider is assumed to have a member 'provider_type'
        (which is an enum with REALTIME or OFFLINE).
        """
        if signal_provider is None:
            return
        self.signal_provider = signal_provider
        self.start_animation()

    def quit_animation(self):
        """Stop the currently running animation."""
        anim = self._current_animation()
        if anim:
            anim._stop()

    def pause_animation(self):
        """Pause the current animation."""
        anim = self._current_animation()
        if anim:
            anim.pause()

    def resume_animation(self):
        """Resume the current animation (by restarting it)."""
        anim = self._current_animation()
        if anim:
            anim.resume()

    def on_pick(self, event):
        """Handle a pick event to add or remove an annotation."""
        if isinstance(event.artist, plt.Line2D):
            color = event.artist.get_color()
            line_xdata = event.artist.get_xdata()
            line_ydata = event.artist.get_ydata()
            index = event.ind[0]
            x_data = line_xdata[index]
            y_data = line_ydata[index]

            # Find the closest annotated point, if any.
            should_remove = False
            min_distance = float("inf")
            nearest_point = (float("inf"), float("inf"))
            radius_x = 0.01 * (self.axes.get_xlim()[1] - self.axes.get_xlim()[0])
            radius_y = 0.01 * (self.axes.get_ylim()[1] - self.axes.get_ylim()[0])
            for ax, ay in self.annotations.keys():
                distance = np.sqrt((ax - x_data) ** 2 + (ay - y_data) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = (ax, ay)
            if (
                abs(x_data - nearest_point[0]) < radius_x
                and abs(y_data - nearest_point[1]) < radius_y
            ):
                x_data, y_data = nearest_point
                should_remove = True

            # Stop the current animation while we process the pick
            anim = self._current_animation()
            if anim:
                anim.event_source.stop()

            if should_remove:
                # Remove annotation and selected point.
                self.annotations[(x_data, y_data)].remove()
                del self.annotations[(x_data, y_data)]
                self.selected_points[(x_data, y_data)].remove()
                del self.selected_points[(x_data, y_data)]
            else:
                # Add an annotation at the picked point.
                # (Grid precision is computed from axis limits.)
                x_grid_precision = max(
                    0,
                    int(
                        np.ceil(
                            -np.log10(self.axes.get_xlim()[1] - self.axes.get_xlim()[0])
                        )
                    )
                    + 2,
                )
                y_grid_precision = max(
                    0,
                    int(
                        np.ceil(
                            -np.log10(self.axes.get_ylim()[1] - self.axes.get_ylim()[0])
                        )
                    )
                    + 2,
                )
                format_string_x = "{:." + str(x_grid_precision) + "f}"
                format_string_y = "{:." + str(y_grid_precision) + "f}"
                annotation_text = (
                    format_string_x.format(x_data)
                    + ", "
                    + format_string_y.format(y_data)
                )
                annotation = self.axes.annotate(
                    annotation_text,
                    xy=(x_data, y_data),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=10,
                    bbox=dict(
                        boxstyle="round,pad=0.3",
                        facecolor=(
                            self.frame_legend.get_facecolor()
                            if self.frame_legend
                            else "w"
                        ),
                        edgecolor=(
                            self.frame_legend.get_edgecolor()
                            if self.frame_legend
                            else "k"
                        ),
                        linewidth=(
                            self.frame_legend.get_linewidth()
                            if self.frame_legend
                            else 1
                        ),
                    ),
                    color="black",
                )
                self.annotations[(x_data, y_data)] = annotation
                (selected_point,) = self.axes.plot(
                    x_data,
                    y_data,
                    "o",
                    markersize=5,
                    markerfacecolor=color,
                    markeredgecolor="k",
                )
                self.selected_points[(x_data, y_data)] = selected_point

            # Restart the proper animation after handling the pick.
            self.start_animation()

    def update_plots(self, paths, legends):
        self.quit_animation()
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

                if timestamps.size > 1:
                    (self.active_paths[path_string],) = self.axes.plot(
                        timestamps,
                        datapoints,
                        label=legend_string,
                        picker=True,
                        color=next(self.color_palette),
                        animated=True,
                    )
                else:
                    (self.active_paths[path_string],) = self.axes.plot(
                        timestamps,
                        datapoints,
                        label=legend_string,
                        picker=True,
                        color=next(self.color_palette),
                        marker="o",
                        animated=True,
                    )

        paths_to_be_canceled = []
        for active_path in self.active_paths.keys():
            path = active_path.split("/")

            if path not in paths:
                paths_to_be_canceled.append(active_path)

        for path in paths_to_be_canceled:
            self.active_paths[path].remove()
            self.active_paths.pop(path)

        try:
            self.axes.set_xlim(0, self.signal_provider.realtime_fixed_plot_window)
        except AttributeError:
            self.axes.set_xlim(
                0, self.signal_provider.end_time - self.signal_provider.initial_time)

        self.axes.legend()

        if not self.frame_legend:
            self.frame_legend = self.axes.legend().get_frame()

        self.start_animation()

    # ------ Vertical Line Animation (for OFFLINE mode) ------

    def init_vertical_line(self):
        """Initializes the vertical line (offline mode)."""
        self.vertical_line.set_data([], [])
        return self.vertical_line, *(self.active_paths.values())

    def update_vertical_line(self, _):
        """
        In offline mode, update the vertical line position.
        Assumes that self.signal_provider.current_time is available.
        """
        current_time = self.signal_provider.current_time
        self.vertical_line.set_data([current_time, current_time], self.axes.get_ylim())
        return (
            self.vertical_line,
            *(self.active_paths.values()),
            *(self.selected_points.values()),
            *(self.annotations.values()),
        )

    # ------ Online Plot Animation (for REALTIME mode) ------

    def update_online_plot(self, frame):
        """
        In realtime mode, update the plotted lines with the latest data.
        (You will need to modify this method so that it retrieves updated data from your
         signal_provider. Here we show one example approach.)
        """
        for path_string, line in self.active_paths.items():
            # Example: re-read data from the signal provider.
            # (For efficiency you might wish to cache the “path” list when you create the line.)
            data = self.signal_provider.data.copy()
            # Assume the original path was stored as a string with "/" separators.
            path_keys = path_string.split("/")
            for key in path_keys[:-1]:
                data = data[key]
            try:
                datapoints = data["data"][:, int(path_keys[-1])]
            except IndexError:
                datapoints = data["data"][:]
            timestamps = data["timestamps"] - self.signal_provider.initial_time
            line.set_data(timestamps, datapoints)

        self.axes.relim()
        self.axes.autoscale_view()

        return (
            *(self.active_paths.values()),
            *(self.selected_points.values()),
            *(self.annotations.values()),
        )
