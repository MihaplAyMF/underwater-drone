# map_utils.py
import numpy as np
import open3d as o3d
import os
import pandas as pd
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MapUtils:
    def __init__(self):
        self.color_map = {
            "sand": [0.957, 0.894, 0.678],
            "rock": [0.502, 0.502, 0.502],
            "coral": [1.0, 0.412, 0.706],
            "reef": [0.0, 0.502, 0.0],
            "empty": [0.0, 0.0, 0.0]
        }
        self.lock = threading.Lock()
        self.last_point = None  # Для перевірки дублювання

    def load_map(self, visualizer):
        """Завантаження карти з terrain_map.csv."""
        with self.lock:
            map_path = os.path.join(os.getcwd(), "terrain_map.csv")
            logger.info(f"Looking for terrain_map.csv at: {map_path}")
            try:
                data_df = pd.read_csv(map_path)
                required_columns = ["x", "y", "depth", "object_type"]
                if not all(col in data_df.columns for col in required_columns):
                    raise ValueError(f"CSV missing required columns: {required_columns}")
                
                data_df = data_df.dropna()
                points = data_df[["x", "y", "depth"]].to_numpy()
                object_types = data_df["object_type"].to_numpy()

                if len(points) != len(object_types):
                    logger.error(f"Mismatch in CSV: {len(points)} points, {len(object_types)} object types")
                    visualizer.points = []
                    visualizer.object_types = []
                    visualizer.visualization.pcd.points = o3d.utility.Vector3dVector([])
                    visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector([])
                    return
                
                visualizer.points = points.tolist()
                visualizer.object_types = object_types.tolist()
                colors = np.array([self.color_map.get(obj, [0.0, 0.0, 0.0]) for obj in object_types])
                
                if len(colors) != len(points):
                    logger.error(f"Colors ({len(colors)}) and points ({len(points)}) mismatch")
                    visualizer.points = []
                    visualizer.object_types = []
                    visualizer.visualization.pcd.points = o3d.utility.Vector3dVector([])
                    visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector([])
                    return
                
                visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(points)
                visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)

                max_coords = np.max(np.abs(points), axis=0) if len(points) > 0 else np.array([1.0, 1.0, 1.0])
                max_coords = np.maximum(max_coords * 1.2, [1.0, 1.0, 1.0])
                visualizer.visualization.axes.points = o3d.utility.Vector3dVector([
                    [0, 0, 0], [max_coords[0], 0, 0], [0, max_coords[1], 0], [0, 0, max_coords[2]]
                ])
                visualizer.visualization.axes.lines = o3d.utility.Vector2iVector([
                    [0, 1], [0, 2], [0, 3]
                ])
                visualizer.visualization.axes.colors = o3d.utility.Vector3dVector([
                    [1, 0, 0], [0, 1, 0], [0, 0, 1]
                ])
                logger.info(f"Loaded map with {len(points)} points, axis lengths: X={max_coords[0]}, Y={max_coords[1]}, Z={max_coords[2]}")
            
            except FileNotFoundError:
                logger.warning("No terrain_map.csv found, creating empty map")
                visualizer.points = []
                visualizer.object_types = []
                visualizer.visualization.pcd.points = o3d.utility.Vector3dVector([])
                visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector([])

                visualizer.visualization.axes.points = o3d.utility.Vector3dVector([
                    [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
                ])
                visualizer.visualization.axes.lines = o3d.utility.Vector2iVector([
                    [0, 1], [0, 2], [0, 3]
                ])
                visualizer.visualization.axes.colors = o3d.utility.Vector3dVector([
                    [1, 0, 0], [0, 1, 0], [0, 0, 1]
                ])

                with open(map_path, 'w') as f:
                    f.write("x,y,depth,object_type\n")
                logger.info(f"Created empty terrain_map.csv at: {map_path}")

            except ValueError as e:
                logger.error(f"Error loading CSV: {e}")
                visualizer.points = []
                visualizer.object_types = []
                visualizer.visualization.pcd.points = o3d.utility.Vector3dVector([])
                visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector([])

                visualizer.visualization.axes.points = o3d.utility.Vector3dVector([
                    [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
                ])
                visualizer.visualization.axes.lines = o3d.utility.Vector2iVector([
                    [0, 1], [0, 2], [0, 3]
                ])
                visualizer.visualization.axes.colors = o3d.utility.Vector3dVector([
                    [1, 0, 0], [0, 1, 0], [0, 0, 1]
                ])
                logger.info("Initialized empty map due to error")

    def update_3d_map(self, visualizer, sonar_data, imu_data):
        """Оновлення 3D карти з даними сонара та IMU."""
        with self.lock:
            distance = sonar_data.get("distance", 0.0)
            object_type = sonar_data.get("object_type", "empty")
            quaternion = imu_data.get("quaternion", [1.0, 0.0, 0.0, 0.0])
            
            if not isinstance(distance, (int, float)) or not all(isinstance(q, (int, float)) for q in quaternion):
                logger.error(f"Invalid sonar/imu data: distance={distance}, quaternion={quaternion}")
                return
            
            if object_type not in self.color_map:
                logger.warning(f"Invalid object_type: {object_type}, using 'empty'")
                object_type = "empty"
            
            q0, q1, q2, q3 = quaternion
            R = np.array([
                [1 - 2*q2**2 - 2*q3**2, 2*q1*q2 - 2*q0*q3, 2*q1*q3 + 2*q0*q2],
                [2*q1*q2 + 2*q0*q3, 1 - 2*q1**2 - 2*q3**2, 2*q2*q3 - 2*q0*q1],
                [2*q1*q3 - 2*q0*q2, 2*q2*q3 + 2*q0*q1, 1 - 2*q1**2 - 2*q2**2]
            ])
            
            depth_vector = np.array([0, 0, -distance])
            global_point = visualizer.drone_position + R @ depth_vector
            
            if not isinstance(global_point, np.ndarray) or len(global_point) != 3:
                logger.error(f"Invalid global_point: {global_point}")
                return
            
            # Перевірка на дублювання
            if self.last_point is not None and np.allclose(self.last_point, global_point, atol=0.01):
                logger.debug("Duplicate point detected, skipping")
                return
            
            self.last_point = global_point.copy()
            logger.info(f"Adding point with distance={distance}, position={visualizer.drone_position}, object_type={object_type}")
            
            logger.debug(f"Before adding: points={len(visualizer.points)}, object_types={len(visualizer.object_types)}")
            visualizer.points.append(global_point.tolist())
            visualizer.object_types.append(object_type)
            logger.debug(f"After adding: points={len(visualizer.points)}, object_types={len(visualizer.object_types)}")
            
            if len(visualizer.points) != len(visualizer.object_types):
                logger.error(f"Points ({len(visualizer.points)}) and object_types ({len(visualizer.object_types)}) mismatch before truncation")
                visualizer.points.pop()
                visualizer.object_types.pop()
                return
            
            if len(visualizer.points) > 1000000:
                visualizer.points.pop(0)
                visualizer.object_types.pop(0)
            
            points_array = np.array(visualizer.points)
            colors = np.array([self.color_map.get(obj, [0.0, 0.0, 0.0]) for obj in visualizer.object_types])
            
            if len(points_array) != len(colors):
                logger.error(f"Points ({len(points_array)}) and colors ({len(colors)}) mismatch")
                visualizer.points.pop()
                visualizer.object_types.pop()
                return
            
            visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(points_array)
            visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)
            
            if len(points_array) > 0:
                max_coords = np.max(np.abs(points_array), axis=0)
                max_coords = np.maximum(max_coords * 1.1, [1.0, 1.0, 1.0])
                visualizer.visualization.axes.points = o3d.utility.Vector3dVector([
                    [0, 0, 0], [max_coords[0], 0, 0], [0, max_coords[1], 0], [0, 0, max_coords[2]]
                ])
                visualizer.visualization.axes.lines = o3d.utility.Vector2iVector([
                    [0, 1], [0, 2], [0, 3]
                ])
                visualizer.visualization.axes.colors = o3d.utility.Vector3dVector([
                    [1, 0, 0], [0, 1, 0], [0, 0, 1]
                ])
                logger.info(f"Axis lengths: X={max_coords[0]}, Y={max_coords[1]}, Z={max_coords[2]}, Point: {global_point}")
            else:
                visualizer.visualization.axes.points = o3d.utility.Vector3dVector([
                    [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
                ])
                visualizer.visualization.axes.lines = o3d.utility.Vector2iVector([
                    [0, 1], [0, 2], [0, 3]
                ])
                visualizer.visualization.axes.colors = o3d.utility.Vector3dVector([
                    [1, 0, 0], [0, 1, 0], [0, 0, 1]
                ])
            
            # Інкрементальне збереження
            map_path = "/home/miha/Projects/UnderWaterDron/ComputerSide/terrain_map.csv"
            with open(map_path, 'a') as f:
                f.write(f"{global_point[0]},{global_point[1]},{global_point[2]},{object_type}\n")
            logger.info(f"Appended to terrain_map.csv at: {map_path}")
            
            if visualizer.visualization.vis and visualizer.visualization.vis_initialized:
                visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(points_array)
                visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)
                visualizer.visualization.vis.clear_geometries()
                visualizer.visualization.vis.add_geometry(visualizer.visualization.pcd)
                visualizer.visualization.vis.add_geometry(visualizer.visualization.axes)
                visualizer.visualization.vis.poll_events()
                visualizer.visualization.vis.update_renderer()
