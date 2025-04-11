from PyQt5 import QtWidgets
from gui import Ui_MainWindow  # Import the generated UI class
from PyQt5.QtCore import QThread
import sys
import socket
import threading
import numpy as np
import struct
import time
from udp_tx_rx import UdpReceive, UdpSend

# Set up UDP ports for communication
UDP_IP = "127.0.0.1"  # IP address for local communication
CMD_UDP_PORT = 6005  # Port for sending control commands
STATUS_UDP_PORT = 7005  # Port for receiving system status updates
MANUAL_POSE_UDP_PORT = 9005  # Port for sending manual control data

# Thread class to continuously listen for status updates from the state machine
class SM_Status_QThread(QThread):
    def __init__(self, callback, udp_object):
        super().__init__()
        self.callback = callback  # Store the callback function
        self.isRunning = True  # Control flag to manage thread execution
        self.UdpListener = udp_object  # UDP listener object

    def run(self):
        # Continuously check for new status messages while thread is running
        while self.isRunning:
            self.callback(self.UdpListener.get())

    def stop(self):
        """Stop the thread gracefully"""
        self.isRunning = False
        self.quit()
        self.wait()

# Main application class that integrates the GUI and logic
class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Load the UI layout from the imported UI class

        # Initialize UDP communication objects
        self.cmd_sender = UdpSend()
        self.manual_pose_sender = UdpSend()
        self.status_receiver = UdpReceive(STATUS_UDP_PORT, blocking=False)

        self.worker = None  # Background thread for receiving system status

        # Start background thread to continuously update GUI status
        if self.worker is None or not self.worker.isRunning:
            self.worker = SM_Status_QThread(self.update_status_label, self.status_receiver)
            self.worker.start()

        # Connect slider signals to labels for displaying gain values
        self.master.valueChanged.connect(lambda value, lbl=self.master_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.xaccel.valueChanged.connect(lambda value, lbl=self.xaccel_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.yaccel.valueChanged.connect(lambda value, lbl=self.yaccel_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.zaccel.valueChanged.connect(lambda value, lbl=self.zaccel_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.roll.valueChanged.connect(lambda value, lbl=self.roll_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.pitch.valueChanged.connect(lambda value, lbl=self.pitch_label, mode="sim_gains": self.update_label(value, lbl, mode))
        self.yaw.valueChanged.connect(lambda value, lbl=self.yaw_label, mode="sim_gains": self.update_label(value, lbl, mode))

        self.xaccel_manual.valueChanged.connect(lambda value, lbl=self.xaccel_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.yaccel_manual.valueChanged.connect(lambda value, lbl=self.yaccel_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.zaccel_manual.valueChanged.connect(lambda value, lbl=self.zaccel_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.roll_manual.valueChanged.connect(lambda value, lbl=self.roll_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.pitch_manual.valueChanged.connect(lambda value, lbl=self.pitch_label_2, mode="manual_gains": self.update_label(value, lbl, mode))
        self.yaw_manual.valueChanged.connect(lambda value, lbl=self.yaw_label_2, mode="manual_gains": self.update_label(value, lbl, mode))

        # Connect button clicks to sending control commands
        self.start.clicked.connect(lambda value, command="running": self.send_control_command(command)) 
        self.stop.clicked.connect(lambda value, command="stop": self.send_control_command(command))
        self.reset.clicked.connect(lambda value, command="idle": self.send_control_command(command))
        self.manual_mode_button.clicked.connect(lambda value, command="manual": self.send_control_command(command))
        self.simulation_mode_button.clicked.connect(lambda value, command="ready": self.send_control_command(command))

        # Reset sliders when reset buttons are clicked
        self.reset_gains.clicked.connect(self.reset_sliders)
        self.reset_gain_manual.clicked.connect(self.reset_sliders)

        # Ensure the first tab (main control) is selected by default
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.tabBar().hide()

    # Update label text with the current slider value based on the mode (simulation/manual)
    def update_label(self, value, label, mode):
        if mode == "sim_gains":
            label.setText(f"Gain: {value/5}")
        elif mode == "manual_gains":
            label.setText(f"Gain: {(value*20)-100}")

    # Send control command with the selected state and gain values
    def send_control_command(self, state):
        data_array = np.array([self.master.value(), self.xaccel.value(), self.yaccel.value(), self.zaccel.value(), 
                               self.roll.value(), self.pitch.value(), self.yaw.value()])
        data_array = data_array/5  # Normalize gain values

        data_str = ",".join(map(str, data_array))  # Convert array to comma-separated string
        message = f"{state}|{data_str}"  # Format message
        print(message)
        self.cmd_sender.send(message, (UDP_IP, CMD_UDP_PORT))  # Send command via UDP

    # Update the GUI status label with the latest state information
    def update_status_label(self, data):
        if data is None:
            return
        
        message, flag = data[1].split("|")
        self.SM_STATUS.setText(f"Message: {message}, Boolean: {flag}")

        # Update start button text based on safety status
        if flag:
            self.start.setText("START SIMULATION")
        else:
            self.start.setText("CHECK SAFETY SENSORS")

        # Automatically switch to manual control tab if in MANUAL_CONTROL state
        if message == "MANUAL_CONTROL":
            self.tabWidget.setCurrentIndex(1)
        else:
            self.tabWidget.setCurrentIndex(0)
    
    # Handle window close event to properly stop background threads
    def closeEvent(self, event):
        pass  # Placeholder for cleanup logic if needed
    
    # Reset all sliders to their default middle position
    def reset_sliders(self):
        sliders = [self.master, self.xaccel, self.yaccel, self.zaccel, self.roll, self.pitch, self.yaw,
                   self.xaccel_manual, self.yaccel_manual, self.zaccel_manual, self.roll_manual, self.pitch_manual, self.yaw_manual]
        for slider in sliders:
            slider.setValue(5)

# Initialize and run the PyQt application
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())