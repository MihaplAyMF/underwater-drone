# data_processor.py
import cv2
import base64
import numpy as np
import socket
import time
from PyQt5 import QtGui, QtCore
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, parent):
        self.parent = parent
        self.latest_frame = None
        self.lock = threading.Lock()

    def update_data(self):
        """Оновлення даних з мережі (камера або сенсори)."""
        try:
            data = self.parent.network.receive_data()
            
            if not data or "type" not in data:
                logger.warning("Invalid or empty data received")
                return

            data_type = data["type"]
            if data_type == "camera":
                try:
                    camera_data = data.get("data")
                    if not isinstance(camera_data, str):
                        logger.error("Invalid camera data format")
                        return
                    # Змінено на кольорове зображення
                    frame = cv2.imdecode(np.frombuffer(base64.b64decode(camera_data), np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        self.latest_frame = frame
                        if self.parent.display_mode in ["camera", "both"]:
                            height, width, channels = frame.shape
                            qimage = QtGui.QImage(frame.data, width, height, width * channels, QtGui.QImage.Format_RGB888)
                            pixmap = QtGui.QPixmap.fromImage(qimage).scaled(
                                self.parent.camera_label.size(), QtCore.Qt.KeepAspectRatio
                            )
                            if self.parent.display_mode == "camera":
                                self.parent.camera_label.setPixmap(pixmap)
                            else:
                                self.parent.both_camera_label.setPixmap(pixmap)
                            logger.info("Updated camera frame")
                    else:
                        logger.error("Failed to decode camera frame")
                except cv2.error as e:
                    logger.error(f"OpenCV error: {e}")
                except Exception as e:
                    logger.error(f"Camera processing error: {e}")

            elif data_type == "sensor":
                sensor_data = data.get("data", {})
                required_keys = ["imu", "sonar", "thruster_speeds"]
                if not all(isinstance(sensor_data.get(key), (dict, list)) for key in required_keys):
                    logger.error(f"Incomplete sensor data: {sensor_data}")
                    return
                if all(key in sensor_data for key in required_keys):
                    with self.lock:
                        dt = 0.05
                        velocity = np.array([sensor_data["thruster_speeds"][0], sensor_data["thruster_speeds"][1], sensor_data["thruster_speeds"][4]])
                        if not np.allclose(velocity, [0.0, 0.0, 0.0]):
                            self.parent.drone_position += velocity * dt
                            logger.info(f"Updated drone position: {self.parent.drone_position}")
                        if sensor_data["thruster_speeds"] != self.parent.last_thruster_speeds:
                            logger.info(f"Thruster speeds: {sensor_data['thruster_speeds']}, Velocity: {velocity}, New position: {self.parent.drone_position}")
                            self.parent.last_thruster_speeds = sensor_data["thruster_speeds"].copy()
                    
                    if self.parent.display_mode in ["sonar", "both"]:
                        current_time = time.time()
                        if current_time - self.parent.last_update_time >= 0.5:
                            logger.info(f"Sonar distance: {sensor_data['sonar']['distance']}, Quaternion: {sensor_data['imu']['quaternion']}, Drone position: {self.parent.drone_position}")
                            logger.debug(f"Received thruster_speeds: {sensor_data['thruster_speeds']}")
                            self.parent.map_utils.update_3d_map(self.parent, sensor_data["sonar"], sensor_data["imu"])
                            if self.parent.display_mode == "sonar":
                                self.parent.visualization.update_open3d_image(self.parent.sonar_label)
                            else:
                                self.parent.visualization.update_open3d_image(self.parent.both_sonar_label)
                            self.parent.last_update_time = current_time
                    logger.info(f"Processed sensor data: imu={sensor_data['imu']}, sonar={sensor_data['sonar']}")
                else:
                    logger.error(f"Incomplete sensor data: {sensor_data}")

        except socket.timeout:
            if self.latest_frame is not None and self.parent.display_mode in ["camera", "both"]:
                height, width, channels = self.latest_frame.shape
                qimage = QtGui.QImage(self.latest_frame.data, width, height, width * channels, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qimage).scaled(
                    self.parent.camera_label.size(), QtCore.Qt.KeepAspectRatio
                )
                if self.parent.display_mode == "camera":
                    self.parent.camera_label.setPixmap(pixmap)
                else:
                    self.parent.both_camera_label.setPixmap(pixmap)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
