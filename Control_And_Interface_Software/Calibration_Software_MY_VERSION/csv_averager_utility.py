import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QLabel, QCheckBox, QHBoxLayout, QMessageBox
)

class CSVProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_cycles = []        # List to store selected cycle numbers
        self.output_directory = ""       # Path for output directory

    def initUI(self):
        layout = QVBoxLayout()
        
        # Label and button to select input directory
        self.label = QLabel("Select a directory to process CSV files:")
        layout.addWidget(self.label)
        
        self.btnBrowse = QPushButton("Browse Input Folder")
        self.btnBrowse.clicked.connect(self.browseFolder)
        layout.addWidget(self.btnBrowse)
        
        # Label and button to select output directory
        self.output_label = QLabel("Select an output directory:")
        layout.addWidget(self.output_label)
        
        self.btnOutputBrowse = QPushButton("Browse Output Folder")
        self.btnOutputBrowse.clicked.connect(self.browseOutputFolder)
        layout.addWidget(self.btnOutputBrowse)
        
        # Create checkboxes for selecting cycles 1 to 5
        self.checkboxes = []
        self.checkbox_layout = QHBoxLayout()
        for i in range(1, 6):
            checkbox = QCheckBox(f"Cycle {i}")
            checkbox.stateChanged.connect(self.updateSelectedCycles)
            self.checkboxes.append(checkbox)
            self.checkbox_layout.addWidget(checkbox)
        layout.addLayout(self.checkbox_layout)
        
        # Button to process CSV files
        self.btnProcess = QPushButton("Process CSV Files")
        self.btnProcess.clicked.connect(self.processFiles)
        layout.addWidget(self.btnProcess)
        
        self.setLayout(layout)
        self.setWindowTitle("CSV Processing Tool")

    def updateSelectedCycles(self):
        # Update the list of selected cycles based on checkbox states
        self.selected_cycles = [i+1 for i, cb in enumerate(self.checkboxes) if cb.isChecked()]
        
    def browseFolder(self):
        # Prompt user to select input folder
        folder = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if folder:
            self.label.setText(f"Selected Input Directory: {folder}")
            self.directory = folder
    
    def browseOutputFolder(self):
        # Prompt user to select output folder
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_label.setText(f"Selected Output Directory: {folder}")
            self.output_directory = folder
    
    def processFiles(self):
        # Validate input and output folder selections
        if not hasattr(self, 'directory') or not self.directory:
            QMessageBox.warning(self, "Warning", "Please select an input directory first.")
            return

        if not self.output_directory:
            QMessageBox.warning(self, "Warning", "Please select an output directory.")
            return

        if not self.selected_cycles:
            QMessageBox.warning(self, "Warning", "Please select at least one cycle to average.")
            return
        
        # Walk through all CSV files in input directory and process them
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith(".csv"):
                    file_path = os.path.join(root, file)
                    self.processCSV(file_path)
        
        QMessageBox.information(self, "Success", "CSV files have been processed and saved to the output folder.")
    
    def processCSV(self, file_path):
        df = pd.read_csv(file_path)
        pressure_col = "Pressure (mbar)"
        
        # Build column names for selected cycles
        distance_cols = [f"Distance Cycle {i} (mm)" for i in self.selected_cycles]
        load_cols = [f"Load Cycle {i} (kg)" for i in self.selected_cycles]
        
        # Calculate averages across selected cycles
        df["Distance (mm)"] = df[distance_cols].mean(axis=1)
        df["Load(kg)"] = df[load_cols].mean(axis=1)
        
        # Keep only pressure, averaged distance and averaged load columns
        df = df[[pressure_col, "Distance (mm)", "Load(kg)"]]
        
        # Construct new filename with selected cycle range
        start_cycle = min(self.selected_cycles)
        end_cycle = max(self.selected_cycles)
        
        new_file_name = os.path.basename(file_path).replace(".csv", f"_averaged_{start_cycle}__{end_cycle}.csv")
        new_file_path = os.path.join(self.output_directory, new_file_name)
        df.to_csv(new_file_path, index=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVProcessor()
    window.show()
    sys.exit(app.exec_())
