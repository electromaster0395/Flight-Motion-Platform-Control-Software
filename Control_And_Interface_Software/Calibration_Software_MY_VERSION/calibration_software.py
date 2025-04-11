from common.serialProcess import SerialProcess  # Import SerialProcess for handling serial communication
from fluidic_muscle import FluidicMuscle  # Import FluidicMuscle module
import csv  # Import CSV for file handling
import pandas as pd  # Import pandas for data manipulation
import sys  # Import sys for system-specific parameters and functions
from PyQt5.QtWidgets import QApplication  # Import PyQt5 for GUI functionality
from GUI import CalibrationApp  # Import the base CalibrationApp class from GUI module
import os  # Import OS for file path handling
from platform_pose import Platform  # Import Platform for controlling the platform
import time  # Import time for delays and timing operations

# Define a new class that extends CalibrationApp
class NewCalibrationApp(CalibrationApp):
    def __init__(self):
        # Call the parent class constructor to inherit properties and UI components
        super().__init__()

        # Define calibration parameters
        self.LOAD = 10  # Default load in kg
        self.STEP_COUNT = 30  # Number of pressure steps
        self.CYCLE_COUNT = 1  # Number of calibration cycles
        self.CURRENT_CYCLE = 0  # Current cycle index
        self.DELAY_PER_STEP_MS = 500  # Delay per step in milliseconds

        # Define pressure settings
        self.MAX_PRESSURE_MBAR = 6000  # Maximum pressure in mbar
        self.PRESSURE_INCREMENT = self.MAX_PRESSURE_MBAR / self.STEP_COUNT  # Pressure increment per step
        self.CURRENT_PRESSURE = self.PRESSURE_INCREMENT  # Start pressure

        # Initialize serial encoder and platform objects
        self.encoder = SerialProcess()
        self.platform = Platform()

        # Create empty DataFrames for calibration curves
        self.P_to_D_up_curve_table = pd.DataFrame(columns=["Pressure (mbar)", "Distance (mm)", "Load(kg)"])
        self.P_to_D_down_curve_table = pd.DataFrame(columns=["Pressure (mbar)", "Distance (mm)", "Load(kg)"])

        # Modify UI button functionality
        self.pushButton_start.setText("Begin Calibration")  # Change button text
        self.pushButton_start.clicked.connect(self.on_start_button_clicked)  # Connect button to custom method

        # Refresh available COM ports
        self.refresh_COM_ports()
        self.pushButton_refresh.clicked.connect(self.refresh_COM_ports)

        # Set default values for UI elements
        self.spinBox_step_count.setValue(self.STEP_COUNT)
        self.spinBox_cycle_count.setValue(self.CYCLE_COUNT)
        self.spinBox_delay.setValue(self.DELAY_PER_STEP_MS)

        # Connect spinbox changes to update methods
        self.spinBox_step_count.valueChanged.connect(self.update_step_count)
        self.spinBox_cycle_count.valueChanged.connect(self.update_cycle_count)
        self.spinBox_delay.valueChanged.connect(self.update_delay)

        # Set default output path
        self.lineEdit_output_path.setText(os.getcwd())
    
    # Update functions for UI inputs
    def update_step_count(self):
        """Updates the step count and recalculates pressure increment."""
        self.STEP_COUNT = self.spinBox_step_count.value()
        self.PRESSURE_INCREMENT = self.MAX_PRESSURE_MBAR / self.STEP_COUNT
        print(self.PRESSURE_INCREMENT)

    def update_cycle_count(self):
        """Updates the cycle count when changed in UI."""
        self.CYCLE_COUNT = self.spinBox_cycle_count.value()

    def update_delay(self):
        """Updates the delay per step when changed in UI."""
        self.DELAY_PER_STEP_MS = self.spinBox_delay.value()

    def on_start_button_clicked(self):
        """Handles the start button click event."""
        print("Start button pressed in new app!")
        print(f"Load: {self.LOAD} kg")
        print(f"Delay: {self.DELAY_PER_STEP_MS} ms")
        print(f"Step Count: {self.STEP_COUNT}")
        print(f"Cycle Count: {self.CYCLE_COUNT}")

        self.label_output_path.setText("Processing...")

        self.platform.muscle.send_pressures([0,0,0,0,0,0])
        time.sleep(self.DELAY_PER_STEP_MS / 1000)

        # Open the selected COM port and retrieve initial load value
        port = self.comboBox_com_port.currentText()
        if port:
            print(port)
            self.encoder.open_port(port, 115200)
            time.sleep(0.1)  # Wait for queue to fill up
            self.encoder.write("R".encode())
            _, load = self.GetDistanceAndLoad()
            self.LOAD = round(load)

        # Start calibration process
        self.Calibrate_Cycles()

    def refresh_COM_ports(self):
        """Refresh the list of available COM ports."""
        self.comboBox_com_port.clear()
        ports = self.encoder.list_ports()
        for p in ports:
            self.comboBox_com_port.addItem(str(p.device))

    def Calibrate(self):
        #Reset muscle pressure
        """Performs the calibration process over multiple cycles."""
        for cycle in range(self.CYCLE_COUNT):
            self.CURRENT_PRESSURE = self.PRESSURE_INCREMENT
            print(f"Cycle {cycle + 1}/{self.CYCLE_COUNT}")

            # Increasing pressure phase
            while self.CURRENT_PRESSURE <= self.MAX_PRESSURE_MBAR:
                time.sleep(self.DELAY_PER_STEP_MS / 2000)
                extension, load = self.GetDistanceAndLoad()
                time.sleep(self.DELAY_PER_STEP_MS / 2000)
                self.P_to_D_up_curve_table = pd.concat(
                    [self.P_to_D_up_curve_table, pd.DataFrame([{ "Pressure (mbar)": self.CURRENT_PRESSURE, "Distance (mm)": extension, 
                                                                "Load(kg)": load }])], ignore_index=True)
                self.platform.muscle.send_pressures([int(self.CURRENT_PRESSURE), 0, 0, 0, 0, 0])
                self.CURRENT_PRESSURE += self.PRESSURE_INCREMENT

            # Decreasing pressure phase
            self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT  # Avoid duplicate max pressure reading
            while self.CURRENT_PRESSURE >= self.PRESSURE_INCREMENT:
                time.sleep(self.DELAY_PER_STEP_MS / 2000)
                extension, load = self.GetDistanceAndLoad()
                time.sleep(self.DELAY_PER_STEP_MS / 2000)
                self.P_to_D_down_curve_table = pd.concat(
                    [self.P_to_D_down_curve_table, pd.DataFrame([{ "Pressure (mbar)": self.CURRENT_PRESSURE, "Distance (mm)": extension, 
                                                                  "Load(kg)": load }])], ignore_index=True)
                self.platform.muscle.send_pressures([int(self.CURRENT_PRESSURE), 0, 0, 0, 0, 0])
                self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT

        # Save averaged results to CSV
        P_to_D_up_curve_table_avg = self.P_to_D_up_curve_table.groupby("Pressure (mbar)").mean().reset_index()
        P_to_D_down_curve_table_avg = self.P_to_D_down_curve_table.groupby("Pressure (mbar)").mean().reset_index()

        if(self.checkbox_csv_output.isChecked()):
            P_to_D_up_curve_table_avg.to_csv(f"{self.lineEdit_output_path.text()}/{self.LOAD}kg_up_curve.csv", index=False)
            P_to_D_down_curve_table_avg.to_csv(f"{self.lineEdit_output_path.text()}/{self.LOAD}kg_down_curve.csv", index=False)
            print("SAVED CSV FILES TO OUTPUT FOLDER")
        
    def Calibrate_Cycles(self):
        """Performs the calibration process over multiple cycles and stores distinct distance/load data for each cycle."""

        # Reset muscle pressure
        column_names = ["Pressure (mbar)"] + [
            f"Distance Cycle {i+1} (mm)" for i in range(self.CYCLE_COUNT)
        ] + [
            f"Load Cycle {i+1} (kg)" for i in range(self.CYCLE_COUNT)
        ]

        # Initialize DataFrames
        self.P_to_D_up_curve_table = pd.DataFrame(columns=column_names)
        self.P_to_D_down_curve_table = pd.DataFrame(columns=column_names)

        for cycle in range(self.CYCLE_COUNT):
            self.CURRENT_PRESSURE = self.PRESSURE_INCREMENT
            print(f"Cycle {cycle + 1}/{self.CYCLE_COUNT}")

            # Increasing pressure phase
            while self.CURRENT_PRESSURE <= self.MAX_PRESSURE_MBAR:
                time.sleep(self.DELAY_PER_STEP_MS / 2000)
                extension, load = self.GetDistanceAndLoad()
                time.sleep(self.DELAY_PER_STEP_MS / 2000)

                if self.CURRENT_PRESSURE in self.P_to_D_up_curve_table["Pressure (mbar)"].values:
                    row_index = self.P_to_D_up_curve_table.index[self.P_to_D_up_curve_table["Pressure (mbar)"] == self.CURRENT_PRESSURE][0]
                    self.P_to_D_up_curve_table.at[row_index, f"Distance Cycle {cycle+1} (mm)"] = extension
                    self.P_to_D_up_curve_table.at[row_index, f"Load Cycle {cycle+1} (kg)"] = load
                else:
                    new_row = {col: None for col in column_names}
                    new_row["Pressure (mbar)"] = self.CURRENT_PRESSURE
                    new_row[f"Distance Cycle {cycle+1} (mm)"] = extension
                    new_row[f"Load Cycle {cycle+1} (kg)"] = load
                    self.P_to_D_up_curve_table = pd.concat(
                        [self.P_to_D_up_curve_table, pd.DataFrame([new_row])], ignore_index=True
                    )

                self.platform.muscle.send_pressures([int(self.CURRENT_PRESSURE), 0, 0, 0, 0, 0])
                self.CURRENT_PRESSURE += self.PRESSURE_INCREMENT

            # Decreasing pressure phase
            self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT  # Avoid duplicate max pressure reading
            while self.CURRENT_PRESSURE >= self.PRESSURE_INCREMENT:
                time.sleep(self.DELAY_PER_STEP_MS / 2000)
                extension, load = self.GetDistanceAndLoad()
                time.sleep(self.DELAY_PER_STEP_MS / 2000)

                if self.CURRENT_PRESSURE in self.P_to_D_down_curve_table["Pressure (mbar)"].values:
                    row_index = self.P_to_D_down_curve_table.index[self.P_to_D_down_curve_table["Pressure (mbar)"] == self.CURRENT_PRESSURE][0]
                    self.P_to_D_down_curve_table.at[row_index, f"Distance Cycle {cycle+1} (mm)"] = extension
                    self.P_to_D_down_curve_table.at[row_index, f"Load Cycle {cycle+1} (kg)"] = load
                else:
                    new_row = {col: None for col in column_names}
                    new_row["Pressure (mbar)"] = self.CURRENT_PRESSURE
                    new_row[f"Distance Cycle {cycle+1} (mm)"] = extension
                    new_row[f"Load Cycle {cycle+1} (kg)"] = load
                    self.P_to_D_down_curve_table = pd.concat(
                        [self.P_to_D_down_curve_table, pd.DataFrame([new_row])], ignore_index=True
                    )

                self.platform.muscle.send_pressures([int(self.CURRENT_PRESSURE), 0, 0, 0, 0, 0])
                self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT

        # Compute the averaged results across cycles
        #P_to_D_up_curve_table_avg = self.P_to_D_up_curve_table.groupby("Pressure (mbar)").mean().reset_index()
        #P_to_D_down_curve_table_avg = self.P_to_D_down_curve_table.groupby("Pressure (mbar)").mean().reset_index()

        # Save CSV files if checkbox is checked
        if self.checkbox_csv_output.isChecked():
            self.P_to_D_up_curve_table.to_csv(f"{self.lineEdit_output_path.text()}/{self.LOAD}kg_up_curve.csv", index=False)
            self.P_to_D_down_curve_table.to_csv(f"{self.lineEdit_output_path.text()}/{self.LOAD}kg_down_curve.csv", index=False)
            print("SAVED CSV FILES TO OUTPUT FOLDER")

    def GetDistanceAndLoad(self):
        """Retrieves extension and load values from the encoder."""
        data = self.encoder.read()
        print(data)
        if data is None:
            print("function does not function!")
            return (0.0,0.0)
        array = data.split(",")
        return (-float(array[1]), float(array[3]) / 9.81) #extension (mm) and load (kg)
    
    def Calibrate_With_Noise(self):
        """Performs calibration with multiple snapshots for noise analysis."""
        SNAPSHOT_COUNT = 100  # Hardcoded number of snapshots per step
        
        for cycle in range(self.CYCLE_COUNT):
            self.CURRENT_PRESSURE = self.PRESSURE_INCREMENT
            print(f"Cycle {cycle + 1}/{self.CYCLE_COUNT}")

            # Increasing pressure phase
            while self.CURRENT_PRESSURE <= self.MAX_PRESSURE_MBAR:
                time.sleep(self.DELAY_PER_STEP_MS / 1000)
                
                # Capture multiple snapshots
                snapshots = [self.GetDistanceAndLoad() for _ in range(SNAPSHOT_COUNT)]
                distances, loads = zip(*snapshots)
                avg_distance = sum(distances) / SNAPSHOT_COUNT
                avg_load = sum(loads) / SNAPSHOT_COUNT
                
                # Calculate snapshot ranges
                distance_range = max(distances) - min(distances)
                load_range = max(loads) - min(loads)
                
                # Store data in DataFrame
                row_data = {"Pressure (mbar)": self.CURRENT_PRESSURE, 
                            "Distance (mm)": avg_distance, 
                            "Load(kg)": avg_load, 
                            "Distance Range (mm)": distance_range,  # Add snapshot range for Distance
                            "Load Range (kg)": load_range}  # Add snapshot range for Load
                
                # Adding individual snapshot values to row data
                for i in range(SNAPSHOT_COUNT):
                    row_data[f"Distance Snapshot {i+1}"] = distances[i]
                    row_data[f"Load Snapshot {i+1}"] = loads[i]
                
                self.P_to_D_up_curve_table = pd.concat([self.P_to_D_up_curve_table, pd.DataFrame([row_data])], ignore_index=True)
                
                self.platform.muscle.send_pressures([int(self.CURRENT_PRESSURE), 0, 0, 0, 0, 0])
                self.CURRENT_PRESSURE += self.PRESSURE_INCREMENT

            # Decreasing pressure phase
            self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT  # Avoid duplicate max pressure reading
            while self.CURRENT_PRESSURE >= self.PRESSURE_INCREMENT:
                time.sleep(self.DELAY_PER_STEP_MS / 1000)
                
                snapshots = [self.GetDistanceAndLoad() for _ in range(SNAPSHOT_COUNT)]
                distances, loads = zip(*snapshots)
                avg_distance = sum(distances) / SNAPSHOT_COUNT
                avg_load = sum(loads) / SNAPSHOT_COUNT
                
                # Calculate snapshot ranges
                distance_range = max(distances) - min(distances)
                load_range = max(loads) - min(loads)
                
                row_data = {"Pressure (mbar)": self.CURRENT_PRESSURE, 
                            "Distance (mm)": avg_distance, 
                            "Load(kg)": avg_load, 
                            "Distance Range (mm)": distance_range,  # Add snapshot range for Distance
                            "Load Range (kg)": load_range}  # Add snapshot range for Load
                
                # Adding individual snapshot values to row data
                for i in range(SNAPSHOT_COUNT):
                    row_data[f"Distance Snapshot {i+1}"] = distances[i]
                    row_data[f"Load Snapshot {i+1}"] = loads[i]
                
                self.P_to_D_down_curve_table = pd.concat([self.P_to_D_down_curve_table, pd.DataFrame([row_data])], ignore_index=True)
                
                self.platform.muscle.send_pressures([int(self.CURRENT_PRESSURE), 0, 0, 0, 0, 0])
                self.CURRENT_PRESSURE -= self.PRESSURE_INCREMENT

        # Save averaged results to CSV
        P_to_D_up_curve_table_avg = self.P_to_D_up_curve_table.groupby("Pressure (mbar)").mean().reset_index()
        P_to_D_down_curve_table_avg = self.P_to_D_down_curve_table.groupby("Pressure (mbar)").mean().reset_index()

        if self.checkbox_csv_output.isChecked():
            P_to_D_up_curve_table_avg.to_csv(f"{self.lineEdit_output_path.text()}/{self.LOAD}kg_up_curve_with_noise.csv", index=False)
            P_to_D_down_curve_table_avg.to_csv(f"{self.lineEdit_output_path.text()}/{self.LOAD}kg_down_curve_with_noise.csv", index=False)
            print("SAVED CSV FILES WITH NOISE DATA TO OUTPUT FOLDER")

if __name__ == "__main__":
    app = QApplication([])
    window = NewCalibrationApp()
    window.show()
    app.exec_()