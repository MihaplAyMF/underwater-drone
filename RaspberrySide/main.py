# main.py
import time
import socket
import json
import threading
import cv2
import numpy as np
import base64
from mock.camera import MockCamera
from mock.imu import MockIMU
from mock.sonar import MockSonar
from utils.logger import Logger

class UnderwaterDrone:
    def __init__(self):
        self.logger = Logger("drone_log.txt")
        self.camera = MockCamera()
        self.imu = MockIMU()
        self.sonar = MockSonar()
        
        # UDP setup
        self.udp_host = "127.0.0.1"
        self.udp_send_port = 5005
        self.udp_recv_port = 5006
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.udp_host, self.udp_recv_port))
        
        # Control variables
        self.thruster_speeds = [0.0] * 6
        self.drone_position = np.array([0.0, 0.0, 0.0])
        self.running = True
        self.frame_id = 0
        
        # Map of object types based on HSV color ranges
        self.color_map = {
            "sand": [0.957, 0.894, 0.678],   # Бежевий
            "rock": [0.502, 0.502, 0.502],   # Сірий
            "coral": [1.0, 0.412, 0.706],    # Рожевий
            "reef": [0.0, 0.502, 0.0],       # Зелений
            "empty": [0.0, 0.0, 0.0]         # Чорний
        }


        
        # Start control command listener
        self.control_thread = threading.Thread(target=self.receive_control_commands)
        self.control_thread.daemon = True
        self.control_thread.start()

    def receive_control_commands(self):
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                self.logger.log(f"Raw data received from {addr}: {data.decode()}")
                control_data = json.loads(data.decode())
                self.thruster_speeds = control_data.get("thruster_speeds", [0.0] * 6)
                self.logger.log(f"Received control: {self.thruster_speeds}")
                self.apply_thruster_speeds(self.thruster_speeds)
            except json.JSONDecodeError as e:
                self.logger.log(f"JSON decode error: {e}")
            except Exception as e:
                self.logger.log(f"Control error: {e}")

    def apply_thruster_speeds(self, speeds):
        self.logger.log(f"Applying thruster speeds: {speeds}")
        dt = 0.1
        velocity = np.array([speeds[0], speeds[1], speeds[4]])
        self.drone_position += velocity * dt
        self.logger.log(f"Updated position: {self.drone_position}")

    def classify_terrain(self, frame_base64):
        try:
            if not frame_base64:
                raise ValueError("Empty frame_base64")
            img_data = base64.b64decode(frame_base64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("Failed to decode image")
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mean_hsv = np.mean(hsv, axis=(0, 1))
            for terrain, (lower, upper) in self.color_map.items():
                lower = np.array(lower, dtype=np.uint8)
                upper = np.array(upper, dtype=np.uint8)
                if (lower[0] <= mean_hsv[0] <= upper[0] and
                    lower[1] <= mean_hsv[1] <= upper[1] and
                    lower[2] <= mean_hsv[2] <= upper[2]):
                    return terrain
            return "empty"
        except Exception as e:
            self.logger.log(f"Terrain classification error: {e}")
            return "empty"

    def send_image_chunks(self, frame_base64, dest_ip="127.0.0.1"):
        # chunk_size = 4000 для MTU ≥ 4000 (оптоволокно). Якщо MTU = 1500 (Ethernet), використовуйте 1472.
        chunk_size = 4000
        frame_id = self.frame_id
        total_chunks = (len(frame_base64) + chunk_size - 1) // chunk_size
        
        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, len(frame_base64))
            chunk = frame_base64[start:end]
            chunk_data = {
                "type": "image_chunk",
                "frame_id": frame_id,
                "chunk_index": i,
                "total_chunks": total_chunks,
                "data": chunk
            }
            try:
                message = json.dumps(chunk_data)
                if len(message) > 4000:
                    self.logger.log(f"Warning: Chunk size {len(message)} exceeds 4000 bytes")
                self.udp_socket.sendto(message.encode(), (dest_ip, self.udp_send_port))
                self.logger.log(f"Sent chunk {i+1}/{total_chunks} for frame {frame_id} (size: {len(message)} bytes)")
            except Exception as e:
                self.logger.log(f"Chunk send error: {e}")

    def collect_sensor_data(self):
        try:
            camera_frame = self.camera.get_frame()
            imu_data = self.imu.get_data()
            quat = imu_data["quaternion"]
            sonar_data = self.sonar.get_data(self.drone_position, quat)
            sonar_data["object_type"] = self.classify_terrain(camera_frame)
            self.frame_id += 1
            
            return {
                "timestamp": time.time(),
                "imu": imu_data,
                "sonar": sonar_data,
                "thruster_speeds": self.thruster_speeds,
                "frame_id": self.frame_id
            }
        except Exception as e:
            self.logger.log(f"Error collecting sensor data: {e}")
            return {
                "timestamp": time.time(),
                "imu": {"quaternion": [0.0, 0.0, 0.0, 1.0]},
                "sonar": {"point": [0.0, 0.0, 0.0], "distance": 0.0, "object_type": "empty"},
                "thruster_speeds": self.thruster_speeds,
                "frame_id": self.frame_id
            }

    def send_sensor_data(self, data, dest_ip="127.0.0.1"):
        try:
            message = json.dumps(data)
            if len(message) > 1500:
                self.logger.log(f"Warning: Message size {len(message)} exceeds 1500 bytes")
            self.udp_socket.sendto(message.encode(), (dest_ip, self.udp_send_port))
            self.logger.log(f"Sent sensor data to {dest_ip}:{self.udp_send_port} (size: {len(message)} bytes)")
        except Exception as e:
            self.logger.log(f"Send error: {e}")

    def run(self):
        self.logger.log("Starting underwater drone...")
        while self.running:
            try:
                sensor_data = self.collect_sensor_data()
                camera_frame = self.camera.get_frame()
                self.send_sensor_data(sensor_data)
                self.send_image_chunks(camera_frame)
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.running = False
                self.logger.log("Shutting down...")
                break
        self.udp_socket.close()

if __name__ == "__main__":
    drone = UnderwaterDrone()
    drone.run()
