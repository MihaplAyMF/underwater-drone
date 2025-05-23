# visualization.py
import numpy as np
import open3d as o3d
from PyQt5 import QtGui, QtCore
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Visualization:
    def __init__(self, parent):
        self.parent = parent
        self.vis = None
        self.pcd = o3d.geometry.PointCloud()
        self.axes = o3d.geometry.LineSet()
        self.vis_initialized = False
        self.camera_params = None
        self.zoom_factor = 1.0
        self.last_points_count = 0
        self.force_update = False  # Для примусового оновлення при зміні камери

    def init_open3d(self):
        """Ініціалізація Open3D візуалізатора."""
        if not self.vis:
            self.vis = o3d.visualization.Visualizer()
            self.vis.create_window(width=800, height=600, visible=False)
            self.vis.get_render_option().point_size = 3
            self.vis.get_render_option().background_color = np.array([0.8, 0.8, 0.8])
            view_control = self.vis.get_view_control()
            center = np.array([0, 0, 0])
            if len(self.pcd.points) == 0:
                logger.warning("Point cloud is empty, initializing with default point")
                self.parent.points = [np.array([0.0, 0.0, 0.0])]
                self.parent.object_types = ["empty"]
                self.pcd.points = o3d.utility.Vector3dVector(np.array(self.parent.points))
                colors = np.zeros((1, 3))
                colors[:, 0] = 1.0
                self.pcd.colors = o3d.utility.Vector3dVector(colors)
            self.axes.points = o3d.utility.Vector3dVector([
                [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
            ])
            self.axes.lines = o3d.utility.Vector2iVector([
                [0, 1], [0, 2], [0, 3]
            ])
            self.axes.colors = o3d.utility.Vector3dVector([
                [1, 0, 0], [0, 1, 0], [0, 0, 1]
            ])
            view_control.set_lookat(center)
            view_control.set_front([0, 0, -1])
            view_control.set_up([0, -1, 0])
            view_control.set_zoom(self.zoom_factor)
            self.camera_params = view_control.convert_to_pinhole_camera_parameters()
            self.camera_params.extrinsic = np.array([
                [-1, 0, 0, 0],
                [0, -1, 0, 0],
                [0, 0, -1, 10],
                [0, 0, 0, 1]
            ])
            view_control.convert_from_pinhole_camera_parameters(self.camera_params)
            logger.info(f"Initialized camera: front=[0, 0, -1], up=[0, -1, 0], lookat={center}, zoom={self.zoom_factor}, extrinsic={self.camera_params.extrinsic}")
        self.vis.clear_geometries()
        self.vis.add_geometry(self.pcd)
        self.vis.add_geometry(self.axes)
        self.vis_initialized = True
        self.vis.poll_events()
        self.vis.update_renderer()
        self.update_open3d_image(self.parent.sonar_label if self.parent.display_mode == "sonar" else self.parent.both_sonar_label)

    def update_open3d_image(self, label):
        """Оновлення зображення Open3D."""
        if not self.vis or not self.vis_initialized:
            logger.error("Visualizer not initialized")
            label.setText("Visualizer not initialized")
            return
        if len(self.pcd.points) == 0:
            logger.warning("No points to display")
            label.setText("No points to display")
            return
        # Оновлюємо, якщо змінилася кількість точок або потрібне примусове оновлення (наприклад, зміна камери)
        if self.last_points_count != len(self.pcd.points) or self.force_update:
            view_control = self.vis.get_view_control()
            center = np.array([0, 0, 0])
            view_control.set_lookat(center)
            view_control.set_zoom(self.zoom_factor)
            if self.camera_params is not None:
                try:
                    view_control.convert_from_pinhole_camera_parameters(self.camera_params)
                    logger.debug(f"Camera: extrinsic={self.camera_params.extrinsic}, zoom_factor={self.zoom_factor}, lookat={center}")
                except Exception as e:
                    logger.error(f"Camera params error: {e}, resetting")
                    view_control.set_lookat(center)
                    view_control.set_front([0, 0, -1])
                    view_control.set_up([0, -1, 0])
                    view_control.set_zoom(self.zoom_factor)
                    self.camera_params = view_control.convert_to_pinhole_camera_parameters()
                    self.camera_params.extrinsic = np.array([
                        [-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, -1, 10],
                        [0, 0, 0, 1]
                    ])
                    view_control.convert_from_pinhole_camera_parameters(self.camera_params)
                    logger.info(f"Reset camera: extrinsic={self.camera_params.extrinsic}, lookat={center}, zoom={self.zoom_factor}")
            else:
                view_control.set_lookat(center)
                view_control.set_front([0, 0, -1])
                view_control.set_up([0, -1, 0])
                view_control.set_zoom(self.zoom_factor)
                self.camera_params = view_control.convert_to_pinhole_camera_parameters()
                self.camera_params.extrinsic = np.array([
                    [-1, 0, 0, 0],
                    [0, -1, 0, 0],
                    [0, 0, -1, 10],
                    [0, 0, 0, 1]
                ])
                view_control.convert_from_pinhole_camera_parameters(self.camera_params)
                logger.info(f"Initialized camera_params: extrinsic={self.camera_params.extrinsic}, lookat={center}, zoom={self.zoom_factor}")
            self.vis.poll_events()
            self.vis.update_renderer()
            self.vis.capture_screen_image(self.parent.temp_image_path)
            pixmap = QtGui.QPixmap(self.parent.temp_image_path)
            scaled_pixmap = pixmap.scaled(label.size(), QtCore.Qt.KeepAspectRatio)
            logger.debug(f"Pixmap size: {scaled_pixmap.size().width()}x{scaled_pixmap.size().height()}")
            label.setPixmap(scaled_pixmap)
            self.last_points_count = len(self.pcd.points)
            self.force_update = False  # Скидаємо після оновлення

    def cleanup(self):
        """Очищення ресурсів візуалізатора."""
        if hasattr(self, 'vis') and self.vis:
            try:
                self.vis.destroy_window()
                logger.info("Visualizer destroyed")
            except Exception as e:
                logger.error(f"Error during visualizer cleanup: {e}")
            self.vis = None
        self.vis_initialized = False
        self.camera_params = None
