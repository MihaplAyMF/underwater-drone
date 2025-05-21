# computer_side.py
import sys
from PyQt5 import QtWidgets
from src.drone_visualizer import DroneVisualizer

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    vis = DroneVisualizer()
    vis.show()
    sys.exit(app.exec_())
