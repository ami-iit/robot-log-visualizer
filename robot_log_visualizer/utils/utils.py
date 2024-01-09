# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

from enum import Enum


class PeriodicThreadState(Enum):
    running = (0,)
    pause = (1,)
    closed = 2


class RobotStatePath:
    def __init__(self):
        self.joints_state_path = []
        self.base_orientation_path = []
        self.base_position_path = []


class Color:
    """
    Color class to handle color in different formats
    """

    def __init__(self, hex="#000000"):
        self.hex = hex

    def as_hex(self):
        return self.hex

    def as_rgb(self):
        return self.hex_to_rgb(self.hex)

    def as_normalized_rgb(self):
        return self.get_to_normalized_rgb(self.hex)

    @staticmethod
    def hex_to_rgb(hex):
        # https://stackoverflow.com/questions/29643352/converting-hex-to-rgb-value-in-python
        hex = hex.lstrip("#")
        hlen = len(hex)
        return tuple(int(hex[i : i + hlen // 3], 16) for i in range(0, hlen, hlen // 3))

    @staticmethod
    def get_to_normalized_rgb(hex):
        rgb = Color.hex_to_rgb(hex)
        return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)


class ColorPalette:
    """
    Color palette class to handle color palette.
    The user can get a color from the palette and the palette will automatically
    cycle through the colors.
    """

    def __init__(self):
        # use matlab color palette
        self._color_palette = [
            Color("#0072BD"),
            Color("#D95319"),
            Color("#EDB120"),
            Color("#7E2F8E"),
            Color("#77AC30"),
            Color("#4DBEEE"),
            Color("#A2142F"),
            Color("#7E2F8E"),
            Color("#77AC30"),
            Color("#4DBEEE"),
            Color("#A2142F"),
        ]
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        color = self._color_palette[self._index]
        self._index = (self._index + 1) % len(self._color_palette)
        return color
