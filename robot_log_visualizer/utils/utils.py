# Copyright (C) 2022 Istituto Italiano di Tecnologia (IIT). All rights reserved.
# This software may be modified and distributed under the terms of the
# Released under the terms of the BSD 3-Clause License

from enum import Enum


class PeriodicThreadState(Enum):
    running = (0,)
    pause = (1,)
    closed = 2
