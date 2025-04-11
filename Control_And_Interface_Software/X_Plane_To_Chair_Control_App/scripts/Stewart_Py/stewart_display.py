import socket
import struct
import select
from src.stewart_controller import Stewart_Platform
import matplotlib.pyplot as plt
import numpy as np
import time
import matplotlib.animation as animation
from udp_tx_rx import UdpReceive

# Define UDP port to listen for pose data, which will be sent from the state_machine.py node
UDP_IP = "127.0.0.1"
TELEMETRY_UDP_PORT = 8005

# Set up UDP socket to listen for pose data (Non-blocking)
telemetry_listener = UdpReceive(TELEMETRY_UDP_PORT)

# Initialize Stewart Platform parameters (Hardcoded for now, will be configurable later)
# This setup is temporary and serves as a debug visualization of platform movement.
platform = Stewart_Platform(132/2, 100/2, 30, 130, 0.2269, 0.82, 5*np.pi/6)

# Function to listen for incoming airplane telemetry and update pose data.
# Inverse kinematics is handled using the "Stewart_Py" repository.
# Eventually, inverse kinematics calculations will be moved to state_machine.py,
# and the chair will only receive muscle pressure values.
def listen_for_telemetry():
    """Reads the latest UDP message, discarding old ones."""
    data = None

    # Retrieve the most recent telemetry data from the UDP buffer
    while telemetry_listener.available() > 0:
        data = telemetry_listener.get()

    if data is None:
        return [], []  # Return empty lists if no data is received

    # Parse incoming pose data
    pose_data = data[1].split(",")
    pose_data = [int(float(r)) for r in pose_data]  # Convert string values to integers
    rotation = pose_data[5:9]  # Extract rotation values from the data

    # Flip roll and pitch for debugging purposes
    rotation[0], rotation[1] = -rotation[1], rotation[0]
    
    trans, rot = [0, 0, 0], rotation  # Translation is set to zero (for now)
    return trans, rot

# Initialize figure and axis for real-time 3D plotting
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Function to update the Stewart platform's position and orientation based on telemetry data
def update(frame):
    """Update function for real-time plotting."""
    trans, rot = listen_for_telemetry()
    if trans and rot:  # Ensure valid data exists
        servo_angles = platform.calculate(np.array(trans), np.array(rot) * (np.pi / 180))  # Convert degrees to radians
        platform.plot_platform(ax=ax)  # Update the 3D plot

# Start real-time animation (100ms update rate)
ani = animation.FuncAnimation(fig, update, interval=100)

# Display the 3D plot
plt.show()