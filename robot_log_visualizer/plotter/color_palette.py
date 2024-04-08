# Copyright (C) 2024 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

import matplotlib.pyplot as plt


class ColorPalette:
    def __init__(self):
        # Define the color taking from the default matplotlib color palette
        # prop_cycle provides the color cycle used as rcParams. In the future,
        # if one wants to change the default color palette in Matplotlib,
        # they can modify the set rcParams directly and our color_palette will
        # always take the one set See here: matplotlib.org/stable/users/explain/customizing.html.
        # For details on prop_cycle, visit: matplotlib.org/stable/users/explain/artists/color_cycle.html
        self.colors = [
            color["color"] for color in list(plt.rcParams["axes.prop_cycle"])
        ]

        self.current_index = 0

    def get_color(self, index):
        return self.colors[index % len(self.colors)]

    def __iter__(self):
        self.current_index = 0
        return self

    def __len__(self):
        return len(self.colors)

    def __next__(self):
        color = self.get_color(self.current_index)
        self.current_index += 1

        return color
