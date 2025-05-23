# navigation.py
import numpy as np

class Navigation:
    def __init__(self, network):
        self.network = network
        self.route = []
        self.current_route_index = 0
        self.thruster_speeds = [0.0] * 6

    def on_map_click(self, visualizer, event):
        if visualizer.display_mode in ["sonar", "both"] and len(visualizer.points) > 0:
            last_point = visualizer.points[-1]
            self.route.append(last_point)
            print(f"Added route point via click: {last_point}")

    def on_map_drag(self, visualizer, event):
        pass

    def start_default_route(self, visualizer):
        visualizer.auto_mode = True
        print("Started default route")

    def update_auto_route(self, visualizer):
        if not self.route:
            self.thruster_speeds = [0.0] * 6
            visualizer.network.send_command(self.thruster_speeds)
            print("No route defined")
            return
        if self.current_route_index >= len(self.route):
            self.current_route_index = 0
        target_point = self.route[self.current_route_index]
        error = target_point - visualizer.drone_position
        if np.linalg.norm(error) < 0.1:
            print("Target point reached, moving to next point")
            self.current_route_index += 1
        else:
            max_speed = 0.5
            norm = np.linalg.norm(error)
            if norm > 0:
                velocity = max_speed * error / norm
                self.thruster_speeds[0] = velocity[0]
                self.thruster_speeds[1] = velocity[1]
                self.thruster_speeds[4] = velocity[2]
            else:
                self.thruster_speeds = [0.0] * 6
            visualizer.network.send_command(self.thruster_speeds)
            print(f"Auto route: error={error}, thruster_speeds={self.thruster_speeds}")

    def add_route_point(self, visualizer, point):
        self.route.append(point)
        print(f"Added route point via input: {point}")


