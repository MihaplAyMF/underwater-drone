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

class DroneVisualizer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Underwater Drone Visualizer")
        self.resize(1200, 800)

        # Ініціалізація компонентів
        self.network = NetworkHandler()
        self.map_utils = MapUtils()
        self.navigation = Navigation(self.network)
        self.visualization = Visualization(self)
        self.input_handler = InputHandler(self)
        self.route_manager = RouteManager(self)
        self.data_processor = DataProcessor(self)

        # Стан дрона
        self.drone_position = np.array([0.0, 0.0, 0.0])
        self.points = []
        self.thruster_speeds = [0.0] * 6
        self.last_thruster_speeds = [0.0] * 6
        self.display_mode = "both"
        self.auto_mode = False
        self.temp_image_path = os.path.join(tempfile.gettempdir(), "open3d_temp.png")
        self.last_update_time = 0.0

        # Налаштування GUI
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
        self.auto_route_button = QtWidgets.QPushButton("Auto Route")
        self.auto_route_button.clicked.connect(self.start_auto_route)
        self.control_layout.addWidget(self.auto_route_button)
        self.stop_route_button = QtWidgets.QPushButton("Stop Route")
        self.stop_route_button.clicked.connect(self.stop_auto_route)
        self.control_layout.addWidget(self.stop_route_button)
        self.route_input = QtWidgets.QLineEdit()
        self.route_input.setPlaceholderText("Enter x,y,z (e.g., 1,2,-1.5)")
        self.route_input.setMaximumWidth(150)
        self.control_layout.addWidget(self.route_input)
        self.add_point_button = QtWidgets.QPushButton("Add Point")
        self.add_point_button.clicked.connect(self.add_route_point)
        self.control_layout.addWidget(self.add_point_button)
        self.control_layout.addStretch()
        self.main_layout.addLayout(self.control_layout)

        # Таймери
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.data_processor.update_data)
        self.timer.start(50)

        self.route_timer = QtCore.QTimer()
        self.route_timer.timeout.connect(self.update_auto_route)
        self.route_timer.start(100)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.map_utils.load_map(self)
        self.change_display_mode("both")

    def change_display_mode(self, mode):
        self.display_mode = mode.lower()
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
        if self.auto_mode:
            self.navigation.update_auto_route(self)

    def start_auto_route(self):
        if not self.auto_mode:
            self.auto_mode = True
            self.navigation.start_default_route(self)
            print("Auto route started via button")

    def stop_auto_route(self):
        if self.auto_mode:
            self.auto_mode = False
            print("Auto route stopped via button")

    def add_route_point(self):
        text = self.route_input.text().strip()
        if text:
            try:
                x, y, z = map(float, text.split(','))
                point = np.array([x, y, z])
                self.navigation.add_route_point(self, point)
                self.route_input.clear()
            except ValueError:
                print("Invalid route point format. Use x,y,z (e.g., 1,2,-1.5)")

    def closeEvent(self, event):
        self.timer.stop()
        self.route_timer.stop()
        self.network.close()
        self.visualization.cleanup()
        if os.path.exists(self.temp_image_path):
            os.remove(self.temp_image_path)
        map_path = os.path.join(os.getcwd(), "terrain_map.csv")
        np.savetxt(map_path, np.array(self.points), delimiter=',')
        print(f"Saved terrain_map.csv at: {map_path}")
        event.accept()

    # Делегування подій вводу до InputHandler
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

    def wheelEvent(self, event):
        self.input_handler.wheelEvent(event)
