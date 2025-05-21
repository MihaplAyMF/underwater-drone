# data_processor.py
import cv2
import base64
import numpy as np
import socket
import time
from PyQt5 import QtGui, QtCore

class DataProcessor:
    def __init__(self, parent):
        self.parent = parent

    def update_data(self):
        try:
            sensor_data = self.parent.network.receive_data()
            if not all(key in sensor_data for key in ["camera", "sonar", "imu"]):
                print("Incomplete sensor data:", sensor_data)
                return
            dt = 0.05
            velocity = np.array([self.parent.thruster_speeds[0], self.parent.thruster_speeds[1], self.parent.thruster_speeds[4]])
            self.parent.drone_position += velocity * dt
            if self.parent.thruster_speeds != self.parent.last_thruster_speeds:
                print(f"Thruster speeds: {self.parent.thruster_speeds}, Velocity: {velocity}, New position: {self.parent.drone_position}")
                self.parent.last_thruster_speeds = self.parent.thruster_speeds.copy()
            if self.parent.display_mode in ["camera", "both"]:
                camera_data = sensor_data["camera"]
                if camera_data:
                    frame = cv2.imdecode(np.frombuffer(base64.b64decode(camera_data), np.uint8), cv2.IMREAD_GRAYSCALE)
                    if frame is not None:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                        height, width, _ = frame_rgb.shape
                        qimage = QtGui.QImage(frame_rgb.data, width, height, width * 3, QtGui.QImage.Format_RGB888)
                        pixmap = QtGui.QPixmap.fromImage(qimage).scaled(self.parent.camera_label.size(), QtCore.Qt.KeepAspectRatio)
                        if self.parent.display_mode == "camera":
                            self.parent.camera_label.setPixmap(pixmap)
                        else:
                            self.parent.both_camera_label.setPixmap(pixmap)
                    else:
                        print("Failed to decode camera frame")
                else:
                    print("Empty camera data received")
                    if self.parent.display_mode == "camera":
                        self.parent.camera_label.setText("No camera data")
                    else:
                        self.parent.both_camera_label.setText("No camera data")
            if self.parent.display_mode in ["sonar", "both"]:
                current_time = time.time()
                if current_time - self.parent.last_update_time >= 0.1:
                    print(f"Sonar distance: {sensor_data['sonar']['distance']}, Quaternion: {sensor_data['imu']['quaternion']}, Drone position: {self.parent.drone_position}")
                    print(f"Received thruster_speeds: {sensor_data['thruster_speeds']}")
                    self.parent.map_utils.update_3d_map(self.parent, sensor_data["sonar"], sensor_data["imu"])
                    if self.parent.display_mode == "sonar":
                        self.parent.visualization.update_open3d_image(self.parent.sonar_label)
                    else:
                        self.parent.visualization.update_open3d_image(self.parent.both_sonar_label)
                    self.parent.last_update_time = current_time
        except socket.timeout:
            pass
        except Exception as e:
            print(f"Error: {e}")
