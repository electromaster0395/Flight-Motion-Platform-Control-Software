import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout, QPushButton, QLineEdit, QLabel, QSpinBox
from platform_pose import Platform
import time
import numpy as np

target_time = 0

global values
values = [0,0,0,0,0,0]

class PressureApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.platform = Platform()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Label
        self.label = QLabel("Enter Distance (0-200 mm):")
        layout.addWidget(self.label)
        
        # Spin Box for entering pressure value
        self.pressure_input = QSpinBox()
        self.pressure_input.setRange(0, 200)  # Limit input between 0 and 6000
        self.pressure_input.setSingleStep(1)  # Increment step
        layout.addWidget(self.pressure_input)
        
        # Send Button
        self.send_button = QPushButton("Send Distance")
        self.send_button.clicked.connect(self.set_distance_value)
        layout.addWidget(self.send_button)
        
        self.setLayout(layout)

    def set_distance_value(self):
        distance = self.pressure_input.value()
        self.send_distance(distance)
        #QMessageBox.information(self, "Success", f"Sent distance: {distance} mbar")
    
    def send_distance(self, distance):
        # Simulated function to send pressure values
        values = [0] * 10  # Example list of values
        values[0] = distance # Modify only the first value
        print(f"Sending distance: {values}")
        self.platform.muscle.send_pressures(values)
    
    def distance_to_pressure(self, distances):
        #Refer to a selected pressure to distance table and return the worked out pressure for the distance. 

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = PressureApp()
    window.setWindowTitle("Pressure Sender")
    window.setGeometry(100, 100, 300, 150)
    window.show()
    sys.exit(app.exec_())