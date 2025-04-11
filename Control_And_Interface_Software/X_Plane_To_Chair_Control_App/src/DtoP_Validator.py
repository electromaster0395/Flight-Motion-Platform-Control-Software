import sys
import time
import csv
from platform_pose import Platform
from common.serialProcess import SerialProcess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFileDialog, QHBoxLayout, QMessageBox
)

from d_to_p_ver_2 import DistanceToPressure

class ContractionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()  # Initialize the user interface
        self.output_file = ""  # Output file path for saving data
        self.platform = Platform()  # Platform instance for motion control
        self.encoder = SerialProcess()  # Serial connection for encoder
        self.d_to_p = DistanceToPressure("output\\wheelchair_DtoP.csv")  # Distance-to-pressure conversion
        self.d_to_p.set_load(24)  # Set load factor for the conversion

    def initUI(self):
        """Set up the user interface components"""
        self.setWindowTitle("Contraction Distance Generator")

        layout = QVBoxLayout()

        # Output file selection section
        file_layout = QHBoxLayout()
        self.file_label = QLabel("CSV Output File: Not selected")  # Label to show selected file
        file_btn = QPushButton("Choose File")  # Button to select file
        file_btn.clicked.connect(self.choose_file)  # Connect button to choose_file function
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(file_btn)
        layout.addLayout(file_layout)

        # Input fields with default values
        defaults = {
            "Max Contraction Distance (mm)": "200.0",  # Default max contraction distance
            "Step Size (mm)": "5.0",  # Default step size
            "Delay (ms)": "1000",  # Default delay in milliseconds
            "Cycle Count": "1"  # Default cycle count
        }

        self.inputs = {}  # Dictionary to store input fields
        for label, default in defaults.items():
            row = QHBoxLayout()
            lbl = QLabel(label)  # Label for input field
            inp = QLineEdit()  # Input field
            inp.setText(default)  # Set default text
            row.addWidget(lbl)
            row.addWidget(inp)
            layout.addLayout(row)
            self.inputs[label] = inp  # Store input field in dictionary

        # Process Button
        run_btn = QPushButton("Run Process and Save CSV")  # Button to run process
        run_btn.clicked.connect(self.run_process)  # Connect button to run_process function
        layout.addWidget(run_btn)

        self.setLayout(layout)  # Set layout for the window

    def choose_file(self):
        """Open a file dialog to choose output CSV file"""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")  # File dialog
        if file_name:
            self.output_file = file_name  # Set the selected file path
            self.file_label.setText(f"CSV Output File: {file_name}")  # Update label to show selected file

    def GetDistanceAndLoad(self):
        """Retrieve extension and load values from the encoder"""
        data = self.encoder.read()  # Read data from encoder
        print(data)
        if data is None:
            print("function does not function!")
            return (0.0, 0.0)  # Return default values if no data
        array = data.split(",")  # Split the data into components
        return (-float(array[1]), float(array[3]) / 9.81)  # Return extension (mm) and load (kg)

    def run_process(self):
        """Run the contraction process and save the results to CSV"""
        if not self.output_file:
            QMessageBox.warning(self, "No File", "Please select an output CSV file.")  # Warning if no file is selected
            return

        try:
            # Get values from input fields and convert to appropriate types
            max_dist = float(self.inputs["Max Contraction Distance (mm)"].text())
            step_size = float(self.inputs["Step Size (mm)"].text())
            delay_ms = int(self.inputs["Delay (ms)"].text())
            cycles = int(self.inputs["Cycle Count"].text())
        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Please enter valid numeric values.")  # Error if input is invalid
            return
        
        port = "COM10"  # Serial port for encoder connection
        print(port)
        self.encoder.open_port(port, 115200)  # Open serial connection to the encoder
        time.sleep(0.1)  # Wait for the queue to fill up
        self.encoder.write("R".encode())  # Send "R" command to the encoder
        _, load = self.GetDistanceAndLoad()  # Get initial load value
        self.LOAD = round(load)  # Round the load value
        print("THE LOAD IS ", self.LOAD)

        # Build the contraction profile (one rising + falling pass)
        distances = []  # List to store contraction distances
        d = 0.0
        while d <= max_dist:
            distances.append(round(d, 4))  # Add each distance to the list
            d += step_size
        d = max_dist - step_size
        while d >= 0:
            distances.append(round(d, 4))  # Add each distance for the falling pass
            d -= step_size

        # Create data structure to hold results
        results = {dist: {} for dist in distances}

        # Run the cycles
        for cycle in range(1, cycles + 1):
            for dist in distances:
                # Get pressure value based on the contraction distance
                pressure = self.d_to_p.get_pressure(max(int(dist - 2), 0))

                print(f"Pressure at {dist}mm is {pressure}mbar")

                # Send pressure values to the platform
                self.platform.muscle.send_pressures([pressure, 0, 0, 0, 0, 0])
                time.sleep(delay_ms / 1000.0)  # Wait for the delay

                print("Distance: ", dist, "  Cycle: ", cycle)

                # Measure the distance and load after each step
                measured_dist, load = self.GetDistanceAndLoad()

                print(measured_dist, " ", dist)

                # Store the results (error and load) for each distance and cycle
                results[dist][f"error mm cycle {cycle}"] = measured_dist - dist
                results[dist][f"load kg cycle {cycle}"] = load

        # Build headers for the CSV
        headers = ["contraction_distance mm"]
        for cycle in range(1, cycles + 1):
            headers.append(f"error mm cycle {cycle}")
            headers.append(f"load kg cycle {cycle}")

        # Write the results to the CSV file
        with open(self.output_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)  # Write headers
            for dist in distances:
                row = [dist]
                for cycle in range(1, cycles + 1):
                    row.append(results[dist].get(f"error mm cycle {cycle}", ""))  # Add error values
                    row.append(results[dist].get(f"load kg cycle {cycle}", ""))  # Add load values
                writer.writerow(row)  # Write row to CSV

        # Show a message box to indicate the process is complete
        QMessageBox.information(self, "Done", f"Data saved to {self.output_file}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ContractionApp()  # Create an instance of the app
    window.show()  # Show the window
    sys.exit(app.exec_())  # Start the Qt application loop
