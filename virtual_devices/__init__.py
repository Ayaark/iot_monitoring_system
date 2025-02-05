# File: virtual_devices/__init__.py
from .device_simulator import VirtualDevice, DeviceManager
from .sensor_generators import SensorDataGenerator, WeatherSensorGenerator

__all__ = [
    'VirtualDevice',
    'DeviceManager',
    'SensorDataGenerator',
    'WeatherSensorGenerator'
]

__version__ = '1.0.0'