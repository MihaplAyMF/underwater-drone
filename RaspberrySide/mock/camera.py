# mock/camera.py
import numpy as np
import cv2
import base64

class MockCamera:
    def __init__(self):
        self.width = 160
        self.height = 120
        self.frame_count = 0

    def get_frame(self):
        """Simulate a camera frame resembling a sea floor and encode as JPEG."""
        self.frame_count += 1

        # Create a base blue-green gradient for sea floor effect
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Generate a smooth gradient for depth effect (darker at bottom)
        for i in range(self.height):
            blue = int(50 + 100 * (i / self.height))
            green = int(70 + 80 * (i / self.height))
            frame[i, :] = [blue, green, 20]

        # Add noise to simulate sea floor texture
        noise = np.random.normal(0, 25, (self.height, self.width, 3)).astype(np.int16)
        frame = frame.astype(np.int16) + noise
        frame = np.clip(frame, 0, 255).astype(np.uint8)

        # Add subtle wave-like patterns
        for i in range(self.height):
            for j in range(self.width):
                wave = int(10 * np.sin((j + self.frame_count) / 20.0) * np.cos(i / 30.0))
                temp = frame[i, j].astype(np.int16) + wave
                frame[i, j] = np.clip(temp, 0, 255).astype(np.uint8)

        # Encode as JPEG with very low quality to reduce size
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 20])
        return base64.b64encode(buffer).decode('utf-8')
