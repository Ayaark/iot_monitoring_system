# File: virtual_devices/device_simulator.py
import time
import json
import requests
from datetime import datetime
from virtual_devices.sensor_generators import SensorDataGenerator


class VirtualDevice:
    """Virtual IoT device simulator"""

    def __init__(self, device_id: str, server_url: str = "http://localhost:5001"):
        self.device_id = device_id
        self.server_url = server_url
        self.sensor_generator = SensorDataGenerator()
        self.is_running = False
        self.auth_token = None

    def register_device(self, username: str, password: str) -> bool:
        """Register device with authentication service"""
        try:
            # Login to get auth token
            auth_response = requests.post(
                "http://localhost:5000/api/auth/login",
                json={"username": username, "password": password}
            )

            if auth_response.status_code == 200:
                self.auth_token = auth_response.json()['data']['access_token']

                # Register device
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                device_data = {
                    "device_id": self.device_id,
                    "name": f"Virtual Device {self.device_id}",
                    "device_type": "virtual",
                    "device_metadata": {}
                }

                register_response = requests.post(
                    f"{self.server_url}/api/devices",
                    json=device_data,
                    headers=headers
                )

                return register_response.status_code in [201, 200]
            return False

        except requests.RequestException as e:
            print(f"Registration error for device {self.device_id}: {e}")
            return False

    def send_data(self):
        """Send generated sensor data"""
        try:
            sensor_data = self.sensor_generator.generate_data()
            data = {
                "device_id": self.device_id,
                "temperature": sensor_data["temperature"],
                "humidity": sensor_data["humidity"],
                "cpu_usage": sensor_data["cpu_usage"],
                "memory_usage": sensor_data["memory_usage"],
                "timestamp": datetime.now().isoformat()
            }
        
            print(f"Sending data for {self.device_id}: {data}")
            response = requests.post(
                "http://127.0.0.1:5001/api/device-data",
                json=data
            )
        
            if response.status_code == 200:
                print(f"Data sent successfully for {self.device_id}")
                return True
            
            print(f"Failed to send data: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"Error sending data: {e}")
            return False

    def start(self, interval: int = 5):
        """Start sending data"""
        self.is_running = True
        print(f"Starting device {self.device_id}")

        while self.is_running:
            try:
                self.send_data()
                time.sleep(interval)
            except Exception as e:
                print(f"Device error: {e}")
                time.sleep(interval)

    def stop(self):
        """Stop the virtual device simulation"""
        self.is_running = False
        print(f"Stopping virtual device {self.device_id}")


class DeviceManager:
    """Manages multiple virtual devices"""

    def __init__(self, num_devices: int = 3):
        self.devices = [
            VirtualDevice(f"VIRTUAL_{i:03d}")
            for i in range(num_devices)
        ]

    def start_all_devices(self, username: str, password: str, interval: int = 5):
        """Start all virtual devices"""
        print(f"Starting {len(self.devices)} virtual devices...")

        # Register all devices
        for device in self.devices:
            if device.register_device(username, password):
                print(f"Device {device.device_id} registered successfully")
            else:
                print(f"Failed to register device {device.device_id}")

        # Start all devices
        for device in self.devices:
            device.start(interval)

    def stop_all_devices(self):
        """Stop all virtual devices"""
        for device in self.devices:
            device.stop()


if __name__ == "__main__":
    # Example usage
    manager = DeviceManager(num_devices=3)
    try:
        manager.start_all_devices("test_user", "test_password")
    except KeyboardInterrupt:
        manager.stop_all_devices()
