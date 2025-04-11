import keyboard
import time
import socket
import struct
import select
import numpy as np
from udp_tx_rx import UdpReceive, UdpSend
from platform_kinematics_module import PoseToDistances
from platform_pose import Platform

# This script handles the core logic of the software, managing the state machine
# responsible for receiving airplane telemetry (linear acceleration & rotational pose),
# computing inverse kinematics for the mechanical chair, and sending commands via UDP.

# Define IP address and port numbers for receiving and sending data
UDP_IP = "127.0.0.1"  # Change if needed
SAFE_STATE_UDP_PORT = 4005
TELEMETRY_UDP_PORT = 10022
CMD_UDP_PORT = 6005
STATUS_UDP_PORT = 7005
POSE_DISPLAY_PORT = 10020
MANUAL_POSE_UDP_PORT = 9005

# Define update frequency (ensuring execution happens at 100Hz cycle time)
CYCLE_TIME = 1/100

# Initialize UDP receiver objects
safe_state_listener = UdpReceive(SAFE_STATE_UDP_PORT)
telemetry_listener = UdpReceive(TELEMETRY_UDP_PORT)
manual_telemetry_listener = UdpReceive(MANUAL_POSE_UDP_PORT)
command_listener = UdpReceive(CMD_UDP_PORT)

# Initialize UDP sender objects
display_sender = UdpSend()
status_sender = UdpSend()

# Global variables to retain values between cycles
global values
values = "0,0,0,0,0,0,0,0"  # Default telemetry data

global user_command
user_command = ""  # Command from user input

global user_gains
user_gains = []  # User-defined gain values

global safe_state
safe_state = False  # Safe state of the system

# Base class for different states within the state machine
class State:
    def __init__(self):
        pass
    def execute(self):
        pass

# IDLE state: Waits until the chair is in a safe state
class IDLE(State):
    def execute(self):
        global safe_state
        if safe_state:
            return "ready"

# READY state: Waits for user command to transition to MANUAL or RUNNING state
class READY(State):
    def execute(self):
        global safe_state, user_command
        if not safe_state:
            return "idle"
        elif user_command == "manual":
            return "manual"
        elif user_command == "running":
            return "running"

# RUNNING state: Processes airplane telemetry, calculates inverse kinematics,
# and sends commands to the display. Transitions to STOP if chair is unsafe.
class RUNNING(State):
    def __init__(self):
        super().__init__()
        self.pose_to_distances = PoseToDistances()
        self.prev_values = values  # Optimization to reduce redundant UDP messages
        self.platform = Platform()

    def execute(self):
        global safe_state, user_command, values
        if not safe_state or user_command == "stop":
            self.platform.muscle.send_pressures([0,0,0,0,0,0])
            return "stop"
        
        # Only send messages if telemetry values have changed
        elif values != self.prev_values:
            xyzrpy = ",".join(values.split(",")[:3]) + "," + ",".join(values.split(",")[-3:])
            xyzrpy_float = [float(num) for num in xyzrpy.split(",")]
            new_values = "request" + "," + xyzrpy + "," + ",".join(map(str, self.pose_to_distances.move_platform(xyzrpy_float)))
            print(new_values)
            display_sender.send(new_values, (UDP_IP, POSE_DISPLAY_PORT))
            self.prev_values = values
            self.platform.set_pose(xyzrpy_float)

# STOP state: Waits for user command and safe state before transitioning back to IDLE
class STOP(State):
    def execute(self):
        global safe_state, user_command
        if safe_state and user_command == "idle":
            return "idle"

# MANUAL_CONTROL state: Allows manual control of the chair through UDP commands
class MANUAL_CONTROL(State):
    def execute(self):
        global user_command
        if user_command == "ready":
            return "ready"

# State machine class: Manages state execution and transitions
class StateMachine:
    def __init__(self):
        self.state = None
    
    def set_state(self, state: State):
        self.state = state
        print(f"State changed to {self.GetCurrentState()}")
    
    def execute(self):
        if self.state:
            transition = self.state.execute()
            if transition == "idle":
                self.set_state(IDLE())
            elif transition == "ready":
                self.set_state(READY())
            elif transition == "running":
                self.set_state(RUNNING())
            elif transition == "stop":
                self.set_state(STOP())
            elif transition == "manual":
                self.set_state(MANUAL_CONTROL())
        else:
            print("No state set")
    
    def GetCurrentState(self):
        return self.state.__class__.__name__

# Main loop: Runs state machine until 'q' is pressed
if __name__ == "__main__":
    sm = StateMachine()
    sm.set_state(IDLE())

    target_time = time.time()

    while not keyboard.is_pressed("q"):
        current_time = time.time()
        
        # Ensure state machine runs at defined CYCLE_TIME
        if current_time >= target_time:
            
            temp_values = None
            while telemetry_listener.available() > 0:
                temp_values = telemetry_listener.get()
            
            if temp_values:
                values = temp_values[1].split(",", 1)[1]  # Remove "xplane_telemetry" prefix
            
            temp_safe_state = safe_state_listener.get()
            if temp_safe_state:
                safe_state = int(temp_safe_state[1])
            
            cmd_message = command_listener.get()
            if cmd_message:
                user_command, user_gains = cmd_message[1].split("|")
                user_gains = user_gains.split(",")
            else:
                user_command = None
            
            status = f"{sm.GetCurrentState()}|{safe_state}"
            status_sender.send(status, (UDP_IP, STATUS_UDP_PORT))
            
            sm.execute()
            target_time = current_time + CYCLE_TIME