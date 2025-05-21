# mock/imu.py
import numpy as np

class MockIMU:
    def get_data(self):
        """Return fixed identity quaternion (no rotation)."""
        return {"quaternion": [0.0, 0.0, 0.0, 1.0]}

# class MockIMU:
#     def get_data(self):
#         """Simulate realistic quaternion data."""
#         q = [random.uniform(-1, 1) for _ in range(4)]
#         norm = np.sqrt(sum(x*x for x in q))
#         return {"quaternion": [x/norm for x in q]}
