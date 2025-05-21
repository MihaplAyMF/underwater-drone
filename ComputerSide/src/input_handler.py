# input_handler.py
from PyQt5 import QtCore, QtGui
import numpy as np

class InputHandler:
    def __init__(self, parent):
        self.parent = parent
        self.mouse_pressed = False
        self.last_mouse_pos = None

    def keyPressEvent(self, event):
        print(f"Window has focus: {self.parent.hasFocus()}")
        self.parent.setFocus()
        self.parent.thruster_speeds = [0.0] * 6
        key = event.key()
        key_name = QtGui.QKeySequence(key).toString() or f"Unknown({key})"
        print(f"Key pressed: {key_name} ({key})")
        if key == QtCore.Qt.Key_W:
            self.parent.thruster_speeds[0] = 0.5
            self.parent.thruster_speeds[1] = 0.5
        elif key == QtCore.Qt.Key_S:
            self.parent.thruster_speeds[0] = -0.5
            self.parent.thruster_speeds[1] = -0.5
        elif key == QtCore.Qt.Key_A:
            self.parent.thruster_speeds[0] = -0.5
            self.parent.thruster_speeds[1] = 0.5
        elif key == QtCore.Qt.Key_D:
            self.parent.thruster_speeds[0] = 0.5
            self.parent.thruster_speeds[1] = -0.5
        elif key == QtCore.Qt.Key_Q:
            self.parent.thruster_speeds[4] = 0.5
            self.parent.thruster_speeds[5] = 0.5
        elif key == QtCore.Qt.Key_E:
            self.parent.thruster_speeds[4] = -0.5
            self.parent.thruster_speeds[5] = -0.5
        elif key == QtCore.Qt.Key_1:
            self.parent.mode_combo.setCurrentText("Camera")
        elif key == QtCore.Qt.Key_2:
            self.parent.mode_combo.setCurrentText("Sonar")
        elif key == QtCore.Qt.Key_3:
            self.parent.mode_combo.setCurrentText("Both")
        elif key == QtCore.Qt.Key_Space:
            if not self.parent.auto_mode:
                self.parent.navigation.start_default_route(self.parent)
            else:
                self.parent.auto_mode = False
        elif key == QtCore.Qt.Key_Escape:
            self.parent.close()
        print(f"Sending thruster_speeds: {self.parent.thruster_speeds}")
        self.parent.network.send_command(self.parent.thruster_speeds)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.mouse_pressed = True
            self.last_mouse_pos = event.pos()
            self.parent.navigation.on_map_click(self.parent, event)

    def mouseMoveEvent(self, event):
        if self.mouse_pressed and self.parent.display_mode in ["sonar", "both"] and self.parent.visualization.vis_initialized:
            delta = event.pos() - self.last_mouse_pos
            view_control = self.parent.visualization.vis.get_view_control()
            center = np.array([0, 0, 0])
            view_control.set_lookat(center)
            view_control.rotate(delta.x() * 0.5, delta.y() * 0.5)
            view_control.set_zoom(self.parent.visualization.zoom_factor)
            self.parent.visualization.camera_params = view_control.convert_to_pinhole_camera_parameters()
            print(f"Mouse move: delta_x={delta.x()}, delta_y={delta.y()}, center={center}, zoom={self.parent.visualization.zoom_factor}")
            self.parent.visualization.update_open3d_image(self.parent.sonar_label if self.parent.display_mode == "sonar" else self.parent.both_sonar_label)
            self.last_mouse_pos = event.pos()
        elif self.mouse_pressed:
            self.parent.navigation.on_map_drag(self.parent, event)
            self.last_mouse_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.mouse_pressed = False

    def wheelEvent(self, event):
        if self.parent.display_mode in ["sonar", "both"] and self.parent.visualization.vis_initialized:
            delta = event.angleDelta().y() / 120
            self.parent.visualization.zoom_factor *= (1.0 - delta * 0.2)
            self.parent.visualization.zoom_factor = max(0.5, min(self.parent.visualization.zoom_factor, 3.0))
            print(f"Wheel event: zoom_factor={self.parent.visualization.zoom_factor}, delta={delta}")
            view_control = self.parent.visualization.vis.get_view_control()
            center = np.array([0, 0, 0])
            view_control.set_lookat(center)
            view_control.set_zoom(self.parent.visualization.zoom_factor)
            self.parent.visualization.camera_params = view_control.convert_to_pinhole_camera_parameters()
            self.parent.visualization.update_open3d_image(self.parent.sonar_label if self.parent.display_mode == "sonar" else self.parent.both_sonar_label)
