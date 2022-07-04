from enum import Enum
__all__ = ['DeviceEnum', 'SmartDeviceEnum']


class SmartDeviceEnum(Enum):
    LOCK = "lock"
    CONSOLE = "terminal"


class DeviceEnum(Enum):
    POWER = 'pwr'
    LIGHT = 'rgb'
    SCALE = 'scl'
