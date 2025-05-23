# drone_visualizer.py
import numpy as np
from PyQt5 import QtWidgets, QtCore
from src.network import NetworkHandler
from src.map_utils import MapUtils
from src.navigation import Navigation
from src.visualization import Visualization
from src.input_handler import InputHandler
from src.route_manager import RouteManager
from src.data_processor import DataProcessor
import tempfile
import os
import pandas as pd  # Додано імпорт pandas
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DroneVisualizer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Underwater Drone Visualizer")
        self.resize(1200, 800)

        self.network = NetworkHandler()
        self.map_utils = MapUtils()
        self.navigation = Navigation(self.network)
        self.visualization = Visualization(self)
        self.input_handler = InputHandler(self)
        self.route_manager = RouteManager(self)
        self.data_processor = DataProcessor(self)

        self.drone_position = np.array([0.0, 0.0, 0.0])
        self.points = []
        self.object_types = []
        self.thruster_speeds = [0.0] * 6
        self.last_thruster_speeds = [0.0] * 6
        self.display_mode = "both"
        self.control_mode = "manual"
        self.temp_image_path = os.path.join(tempfile.gettempdir(), "open3d_temp.png")
        self.last_update_time = 0.0
        self.is_processing = False

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.stack = QtWidgets.QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.camera_widget = QtWidgets.QWidget()
        self.camera_layout = QtWidgets.QVBoxLayout(self.camera_widget)
        self.camera_label = QtWidgets.QLabel("Camera Feed")
        self.camera_label.setMinimumSize(320, 240)
        self.camera_label.setAlignment(QtCore.Qt.AlignCenter)
        self.camera_layout.addWidget(self.camera_label)
        self.stack.addWidget(self.camera_widget)

        self.sonar_widget = QtWidgets.QWidget()
        self.sonar_layout = QtWidgets.QVBoxLayout(self.sonar_widget)
        self.sonar_label = QtWidgets.QLabel()
        self.sonar_label.setMinimumSize(800, 600)
        self.sonar_label.setAlignment(QtCore.Qt.AlignCenter)
        self.sonar_label.setMouseTracking(True)
        self.sonar_layout.addWidget(self.sonar_label)
        self.stack.addWidget(self.sonar_widget)

        self.both_widget = QtWidgets.QWidget()
        self.both_layout = QtWidgets.QHBoxLayout(self.both_widget)
        self.both_camera_label = QtWidgets.QLabel("Camera Feed")
        self.both_camera_label.setMinimumSize(320, 240)
        self.both_camera_label.setMaximumSize(400, 300)
        self.both_layout.addWidget(self.both_camera_label, 3)
        self.both_sonar_label = QtWidgets.QLabel()
        self.both_sonar_label.setMinimumSize(800, 600)
        self.both_sonar_label.setAlignment(QtCore.Qt.AlignCenter)
        self.both_sonar_label.setMouseTracking(True)
        self.both_layout.addWidget(self.both_sonar_label, 7)
        self.stack.addWidget(self.both_widget)

        self.control_layout = QtWidgets.QHBoxLayout()
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["Camera", "Sonar", "Both"])
        self.mode_combo.setCurrentText("Both")
        self.mode_combo.currentTextChanged.connect(self.change_display_mode)
        self.control_layout.addWidget(QtWidgets.QLabel("Display Mode:"))
        self.control_layout.addWidget(self.mode_combo)
        self.toggle_mode_button = QtWidgets.QPushButton("Manual Mode")
        self.toggle_mode_button.setCheckable(True)
        self.toggle_mode_button.clicked.connect(self.toggle_control_mode)
        self.control_layout.addWidget(self.toggle_mode_button)
        self.route_input = QtWidgets.QLineEdit()
        self.route_input.setPlaceholderText("Enter x,y,z (e.g., 1,2,-1.5)")
        self.route_input.setMaximumWidth(150)
        self.control_layout.addWidget(self.route_input)
        self.add_point_button = QtWidgets.QPushButton("Add Point")
        self.add_point_button.clicked.connect(self.add_route_point)
        self.control_layout.addWidget(self.add_point_button)
        self.control_layout.addStretch()
        self.main_layout.addLayout(self.control_layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.process_data)
        self.timer.start(100)

        self.route_timer = QtCore.QTimer()
        self.route_timer.timeout.connect(self.update_auto_route)
        self.route_timer.start(200)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.map_utils.load_map(self)
        self.change_display_mode("both")

    def process_data(self):
        """Обробка даних з таймера."""
        if self.is_processing:
            logger.warning("Previous data processing not finished, skipping")
            return
        self.is_processing = True
        try:
            self.data_processor.update_data()
        finally:
            self.is_processing = False

    def change_display_mode(self, mode):
        """Зміна режиму відображення."""
        self.display_mode = mode.lower()
        logger.info(f"Changing display mode to: {self.display_mode}")
        if self.display_mode == "camera":
            self.stack.setCurrentWidget(self.camera_widget)
            self.visualization.cleanup()
        elif self.display_mode == "sonar":
            self.stack.setCurrentWidget(self.sonar_widget)
            if not self.visualization.vis_initialized:
                self.visualization.init_open3d()
        else:
            self.stack.setCurrentWidget(self.both_widget)
            if not self.visualization.vis_initialized:
                self.visualization.init_open3d()

    def update_auto_route(self):
        """Оновлення автоматичного маршруту."""
        if self.control_mode == "auto":
            self.navigation.update_auto_route(self)

    def toggle_control_mode(self):
        """Перемикання між ручним і автоматичним режимами."""
        if self.control_mode == "manual":
            self.control_mode = "auto"
            self.toggle_mode_button.setText("Auto Mode")
            self.navigation.start_default_route(self)
            logger.info("Switched to auto mode")
        else:
            self.control_mode = "manual"
            self.toggle_mode_button.setText("Manual Mode")
            self.thruster_speeds = [0.0] * 6
            self.network.send_command(self.thruster_speeds)
            logger.info("Switched to manual mode")

    def add_route_point(self):
        """Додавання точки маршруту."""
        text = self.route_input.text().strip()
        if text:
            try:
                x, y, z = map(float, text.split(','))
                point = np.array([x, y, z])
                self.navigation.add_route_point(self, point)
                self.route_input.clear()
                logger.info(f"Added route point: {point}")
            except ValueError:
                logger.error("Invalid route point format. Use x,y,z (e.g., 1,2,-1.5)")

    def closeEvent(self, event):
        """Обробка закриття вікна."""
        self.timer.stop()
        self.route_timer.stop()
        self.network.close()
        self.visualization.cleanup()
        if os.path.exists(self.temp_image_path):
            os.remove(self.temp_image_path)
        map_path = os.path.join(os.getcwd(), "terrain_map.csv")
        with self.map_utils.lock:
            terrain_data = {
                "x": [p[0] for p in self.points],
                "y": [p[1] for p in self.points],
                "depth": [p[2] for p in self.points],
                "object_type": self.object_types
            }
            if self.points:  # Зберігаємо лише, якщо є точки
                df = pd.DataFrame(terrain_data)
                df.to_csv(map_path, index=False)
                logger.info(f"Saved terrain_map.csv at: {map_path}")
            else:
                logger.info("No points to save, skipping terrain_map.csv")
        event.accept()

    def keyPressEvent(self, event):
        self.input_handler.keyPressEvent(event)

    def mousePressEvent(self, event):
        self.input_handler.mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.input_handler.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.input_handler.mouseReleaseEvent(event)

    def wheelEvent(self, event):
        self.input_handler.wheelEvent(event)
