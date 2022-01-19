from enum import Enum


class PeriodicThreadState(Enum):
    running = 0,
    pause = 1,
    closed = 2
