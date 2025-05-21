# mock/sonar.py

import numpy as np
from scipy.spatial.transform import Rotation as R

class MockSonar:
    def __init__(self, detection_distance=1.5):
        self.detection_distance = detection_distance

    def get_data(self, drone_position, quaternion):
        """
        Simulate sonar by returning a point in front of the drone based on its orientation.
        :param drone_position: np.array([x, y, z])
        :param quaternion: list or np.array [x, y, z, w]
        """
        # Convert quaternion to rotation
        rotation = R.from_quat(quaternion)  # Note: [x, y, z, w] order!
        forward = rotation.apply([1.0, 0.0, 0.0])  # Rotate forward vector
        detected_point = drone_position + forward * self.detection_distance

        return {
            "point": detected_point.tolist(),
            "distance": self.detection_distance
        }

