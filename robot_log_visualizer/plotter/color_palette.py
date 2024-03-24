# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

import matplotlib.pyplot as plt


class ColorPalette:
    def __init__(self):
        # Define the color taking from the default matplotlib color palette
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
