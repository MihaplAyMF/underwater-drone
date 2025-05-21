# network.py
import socket
import json

class NetworkHandler:
    def __init__(self):
        self.rpi_ip = "127.0.0.1"
        self.rpi_port = 5006
        self.local_ip = "127.0.0.1"
        self.local_port = 5005
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.local_ip, self.local_port))
        self.udp_socket.settimeout(0.1)

    def send_command(self, thruster_speeds):
        command = {"thruster_speeds": thruster_speeds}
        print(f"Sending command to {self.rpi_ip}:{self.rpi_port}: {command}")
        try:
            message = json.dumps(command)
            if len(message) > 1024:
                print(f"Warning: Command size {len(message)} exceeds 1024 bytes")
            self.udp_socket.sendto(message.encode(), (self.rpi_ip, self.rpi_port))
        except Exception as e:
            print(f"Send command error: {e}")

    def receive_data(self):
        try:
            data, addr = self.udp_socket.recvfrom(8192)  # Збільшено буфер
            print(f"Received data size: {len(data)} bytes from {addr}")
            decoded_data = data.decode()
            sensor_data = json.loads(decoded_data)
            print_data = sensor_data.copy()
            if "camera" in print_data:
                print_data["camera"] = "[base64 image]"
            print(f"Raw data from {addr}: {print_data}")
            print(f"Received data: {print_data}")
            return sensor_data
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {}
        except socket.timeout:
            raise
        except Exception as e:
            print(f"Receive error: {e}")
            return {}

    def close(self):
        self.udp_socket.close()
