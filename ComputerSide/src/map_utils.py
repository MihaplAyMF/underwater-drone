# map_utils.py
# import numpy as np
# import open3d as o3d
# import os
#
# class MapUtils:
#     def load_map(self, visualizer):
#         map_path = os.path.join(os.getcwd(), "terrain_map.csv")
#         print(f"Looking for terrain_map.csv at: {map_path}")
#         try:
#             data = np.genfromtxt(map_path, delimiter=',')
#             if data.size == 0:
#                 print("Empty terrain map, initializing with default point")
#                 data = np.array([[0.0, 0.0, 0.0]])
#             visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(data)
#             colors = np.zeros_like(data)
#             colors[:, 0] = 1.0
#             visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)
#             visualizer.points = data.tolist()
#             print(f"Loaded terrain map with {len(data)} points")
#         except FileNotFoundError:
#             print("terrain_map.csv not found, initializing with default point")
#             visualizer.points = [np.array([0.0, 0.0, 0.0])]
#             visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(np.array(visualizer.points))
#             colors = np.zeros((1, 3))
#             colors[:, 0] = 1.0
#             visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)
#         except Exception as e:
#             print(f"Error loading terrain map: {e}")
#             visualizer.points = [np.array([0.0, 0.0, 0.0])]
#             visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(np.array(visualizer.points))
#             colors = np.zeros((1, 3))
#             colors[:, 0] = 1.0
#             visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)
#
#     def update_3d_map(self, visualizer, sonar_data, imu_data):
#         try:
#             distance = sonar_data.get("distance", 0.0)
#             quaternion = imu_data.get("quaternion", [1.0, 0.0, 0.0, 0.0])
#             drone_pos = visualizer.drone_position
#             w, x, y, z = quaternion
#             rotation_matrix = np.array([
#                 [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
#                 [2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
#                 [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y]
#             ])
#             sonar_dir = np.array([0.0, 0.0, -1.0])
#             global_sonar_dir = rotation_matrix @ sonar_dir
#             new_point = drone_pos + distance * global_sonar_dir
#             visualizer.points.append(new_point)
#             points_array = np.array(visualizer.points)
#             visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(points_array)
#             colors = np.zeros_like(points_array)
#             colors[:, 0] = 1.0
#             visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)
#             print(f"Updated map with new point: {new_point}")
#         except Exception as e:
#             print(f"Error updating 3D map: {e}")

# map_utils.py 
import numpy as np
import open3d as o3d
import os
import pandas as pd

class MapUtils:
    def __init__(self):
        # Визначення кольорів для типів об'єктів (RGB у діапазоні [0, 1])
        self.color_map = {
            "sand": [0.957, 0.894, 0.678],   # Бежевий
            "rock": [0.502, 0.502, 0.502],   # Сірий
            "coral": [1.0, 0.412, 0.706],    # Рожевий
            "reef": [0.0, 0.502, 0.0],       # Зелений
            "empty": [0.0, 0.0, 0.0]         # Чорний
        }

    def load_map(self, visualizer):
        map_path = os.path.join(os.getcwd(), "terrain_map.csv")
        print(f"Looking for terrain_map.csv at: {map_path}")
        try:
            # Зчитування CSV за допомогою pandas для правильної обробки стовпців
            data_df = pd.read_csv(map_path)
            # Витягуємо координати (x, y, depth)
            points = data_df[["x", "y", "depth"]].to_numpy()
            object_types = data_df["object_type"].to_numpy()
            visualizer.points = points.tolist()
            visualizer.object_types = object_types.tolist()  # Зберігаємо типи об'єктів
            visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(points)
            
            # Присвоєння кольорів залежно від типу об'єкта
            colors = np.array([self.color_map.get(obj, [0.0, 0.0, 0.0]) for obj in object_types])
            visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)

            # Ініціалізація осей на основі завантажених точок
            max_coords = np.max(np.abs(points), axis=0) if len(points) > 0 else np.array([1.0, 1.0, 1.0])
            max_coords = np.maximum(max_coords * 1.2, [1.0, 1.0, 1.0])  # 10% запас
            visualizer.visualization.axes.points = o3d.utility.Vector3dVector([
                [0, 0, 0], [max_coords[0], 0, 0], [0, max_coords[1], 0], [0, 0, max_coords[2]]
            ])
            visualizer.visualization.axes.lines = o3d.utility.Vector2iVector([
                [0, 1], [0, 2], [0, 3]
            ])
            visualizer.visualization.axes.colors = o3d.utility.Vector3dVector([
                [1, 0, 0], [0, 1, 0], [0, 0, 1]
            ])
            print(f"Loaded map with {len(points)} points, axis lengths: X={max_coords[0]}, Y={max_coords[1]}, Z={max_coords[2]}")
     
        except FileNotFoundError:
            print("No terrain_map.csv found, creating empty map")
            # Ініціалізація порожньої хмари точок
            visualizer.points = []
            visualizer.object_types = []  # Порожній список для типів об'єктів
            visualizer.visualization.pcd.points = o3d.utility.Vector3dVector([])
            visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector([])

            # Ініціалізація стандартних осей
            visualizer.visualization.axes.points = o3d.utility.Vector3dVector([
                [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
            ])
            visualizer.visualization.axes.lines = o3d.utility.Vector2iVector([
                [0, 1], [0, 2], [0, 3]
            ])
            visualizer.visualization.axes.colors = o3d.utility.Vector3dVector([
                [1, 0, 0], [0, 1, 0], [0, 0, 1]
            ])

            # Створення порожнього CSV файлу
            with open(map_path, 'w') as f:
                f.write("x,y,depth,object_type\n")  # Додаємо заголовки
            print(f"Created empty terrain_map.csv at: {map_path}")

    def update_3d_map(self, visualizer, sonar_data, imu_data):
        distance = sonar_data.get("distance", 0.0)
        object_type = sonar_data.get("object_type", "empty")  # Тип об'єкта з sonar_data
        quaternion = imu_data.get("quaternion", [1.0, 0.0, 0.0, 0.0])
        
        if not isinstance(distance, (int, float)) or not all(isinstance(q, (int, float)) for q in quaternion):
            print(f"Invalid sonar/imu data: distance={distance}, quaternion={quaternion}")
            return
        
        print(f"Adding point with distance={distance}, position={visualizer.drone_position}, object_type={object_type}")
        
        q0, q1, q2, q3 = quaternion
        R = np.array([
            [1 - 2*q2**2 - 2*q3**2, 2*q1*q2 - 2*q0*q3, 2*q1*q3 + 2*q0*q2],
            [2*q1*q2 + 2*q0*q3, 1 - 2*q1**2 - 2*q3**2, 2*q2*q3 - 2*q0*q1],
            [2*q1*q3 - 2*q0*q2, 2*q2*q3 + 2*q0*q1, 1 - 2*q1**2 - 2*q2**2]
        ])
        
        depth_vector = np.array([0, 0, -distance])
        global_point = visualizer.drone_position + R @ depth_vector
        
        visualizer.points.append(global_point)
        visualizer.object_types.append(object_type)  # Додаємо тип об'єкта
        
        # Обмеження кількості точок
        if len(visualizer.points) > 1000000:
            visualizer.points.pop(0)
            visualizer.object_types.pop(0)
        
        points_array = np.array(visualizer.points)
        visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(points_array)
        
        # Присвоєння кольорів на основі типів об'єктів
        colors = np.array([self.color_map.get(obj, [0.0, 0.0, 0.0]) for obj in visualizer.object_types])
        visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)
        
        # Оновлення осей з урахуванням меж хмари точок
        if len(points_array) > 0:
            max_coords = np.max(np.abs(points_array), axis=0)
            max_coords = np.maximum(max_coords * 1.1, [1.0, 1.0, 1.0])  # 10% запас
            visualizer.visualization.axes.points = o3d.utility.Vector3dVector([
                [0, 0, 0], [max_coords[0], 0, 0], [0, max_coords[1], 0], [0, 0, max_coords[2]]
            ])
            visualizer.visualization.axes.lines = o3d.utility.Vector2iVector([
                [0, 1], [0, 2], [0, 3]
            ])
            visualizer.visualization.axes.colors = o3d.utility.Vector3dVector([
                [1, 0, 0], [0, 1, 0], [0, 0, 1]
            ])
            print(f"Axis lengths: X={max_coords[0]}, Y={max_coords[1]}, Z={max_coords[2]}, Point: {global_point}")
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
        
        if visualizer.visualization.vis and visualizer.visualization.vis_initialized:
            visualizer.visualization.pcd.points = o3d.utility.Vector3dVector(points_array)
            visualizer.visualization.pcd.colors = o3d.utility.Vector3dVector(colors)
            visualizer.visualization.vis.clear_geometries()
            visualizer.visualization.vis.add_geometry(visualizer.visualization.pcd)
            visualizer.visualization.vis.add_geometry(visualizer.visualization.axes)
            visualizer.visualization.vis.poll_events()
            visualizer.visualization.vis.update_renderer()
