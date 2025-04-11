import sys
import socket
import struct
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton
from PyQt5.QtCore import QTimer
from udp_tx_rx import UdpSend

# Define UDP IP and port for sending telemetry data
UDP_IP = "127.0.0.1"
TELEMETRY_UDP_PORT = 4005

class CheckboxControl(QWidget):
    def __init__(self):
        super().__init__()
        
        # Set up the window properties
        self.setWindowTitle("Checkbox Control")
        self.setGeometry(100, 100, 300, 200)
        
        # Create a vertical layout
        self.layout = QVBoxLayout()
        
        # Define checkbox for sending data
        self.checkbox = QCheckBox("Send Value")
        self.checkbox.stateChanged.connect(self.send_udp_data)
        self.layout.addWidget(self.checkbox)
        
        # Define reset button to uncheck the checkbox
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_checkbox)
        self.layout.addWidget(self.reset_button)
        
        # Set layout for the window
        self.setLayout(self.layout)
        
        # Initialize UDP sender object
        self.udp_sender = UdpSend()
        
        # Define a timer to send UDP messages every 100ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_udp_data)
        self.timer.start(100)  # Send data every 100 ms

    def reset_checkbox(self):
        """Resets checkbox to unchecked state."""
        self.checkbox.setChecked(False)
    
    def send_udp_data(self):
        """Sends UDP data based on checkbox state."""
        data = int(self.checkbox.isChecked())  # Convert checkbox state to integer (0 or 1)
        data_str = str(data)  # Convert to string format for sending
        self.udp_sender.send(data_str, (UDP_IP, TELEMETRY_UDP_PORT))  # Send data via UDP
        #print("Sent data:", data_str)  # Uncomment for debugging

# Run the application if this script is executed directly
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CheckboxControl()
    window.show()
    sys.exit(app.exec_())