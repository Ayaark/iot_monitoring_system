# File: virtual_devices/sensor_generators.py
import random
import psutil
from datetime import datetime

class SensorDataGenerator:
    """Generates realistic sensor data for virtual IoT devices"""
    
    def __init__(self):
        # Initialize base values for sensors
        self.base_temperature = random.uniform(20, 25)
        self.base_humidity = random.uniform(45, 55)
        self.temp_drift = 0
        self.humid_drift = 0

    def get_temperature(self) -> float:
        """Generate realistic temperature data with drift"""
        # Add small random drift
        self.temp_drift += random.uniform(-0.1, 0.1)
        # Limit drift to reasonable range
        self.temp_drift = max(min(self.temp_drift, 5), -5)
        
        temperature = self.base_temperature + self.temp_drift
        # Ensure temperature stays within realistic bounds
        return round(max(min(temperature, 35), 15), 2)

    def get_humidity(self) -> float:
        """Generate realistic humidity data with drift"""
        self.humid_drift += random.uniform(-0.2, 0.2)
        self.humid_drift = max(min(self.humid_drift, 10), -10)
        
        humidity = self.base_humidity + self.humid_drift
        return round(max(min(humidity, 90), 20), 2)

    def get_system_metrics(self) -> dict:
        """Get real system metrics for simulation"""
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }

    def generate_data(self) -> dict:
        """Generate complete sensor data package"""
        system_metrics = self.get_system_metrics()
        
        return {
            "temperature": self.get_temperature(),
            "humidity": self.get_humidity(),
            "cpu_usage": system_metrics["cpu_usage"],
            "memory_usage": system_metrics["memory_usage"],
            "disk_usage": system_metrics["disk_usage"],
            "timestamp": datetime.now().isoformat(),
            "battery_level": random.uniform(50, 100),  # Simulated battery level
            "signal_strength": random.randint(-90, -30)  # Simulated WiFi signal strength in dBm
        }

class WeatherSensorGenerator(SensorDataGenerator):
    """Specialized generator for weather-related data"""
    
    def __init__(self):
        super().__init__()
        self.base_pressure = random.uniform(1000, 1020)
        self.pressure_drift = 0
        self.wind_speed = random.uniform(0, 10)

    def get_pressure(self) -> float:
        """Generate realistic atmospheric pressure data"""
        self.pressure_drift += random.uniform(-0.1, 0.1)
        self.pressure_drift = max(min(self.pressure_drift, 5), -5)
        
        pressure = self.base_pressure + self.pressure_drift
        return round(max(min(pressure, 1040), 980), 2)

    def get_wind_data(self) -> dict:
        """Generate wind speed and direction data"""
        self.wind_speed += random.uniform(-0.5, 0.5)
        self.wind_speed = max(min(self.wind_speed, 20), 0)
        
        return {
            "speed": round(self.wind_speed, 2),
            "direction": random.randint(0, 359),
            "gust": round(self.wind_speed + random.uniform(0, 5), 2)
        }

    def generate_data(self) -> dict:
        """Generate complete weather station data"""
        base_data = super().generate_data()
        wind_data = self.get_wind_data()
        
        return {
            **base_data,
            "pressure": self.get_pressure(),
            "wind_speed": wind_data["speed"],
            "wind_direction": wind_data["direction"],
            "wind_gust": wind_data["gust"],
            "rain_rate": round(random.uniform(0, 5), 2),
            "uv_index": round(random.uniform(0, 11), 1)
        }