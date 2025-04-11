import os
import pandas as pd
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import scipy.interpolate as interp

# Interpolation method used for generating evenly spaced pressure values
INTERPOLATION_TYPE = 'linear'  # Change to 'cubic' if needed

class CSVProcessor:
    def __init__(self, directory):
        self.directory = directory
        self.file_pairs = self.find_csv_pairs()  # Find matching up/down file pairs by weight
    
    def find_csv_pairs(self):
        # List all CSV files in the directory
        files = [f for f in os.listdir(self.directory) if f.endswith('.csv')]
        weights = {}

        # Group files by weight and direction (up/down)
        for file in files:
            parts = file.split('_')
            try:
                weight = int(parts[0][:-2])  # Extract weight from filename (e.g., "13kg_up_..." → 13)
                direction = 'up' if 'up' in file else 'down' if 'down' in file else None
                if direction:
                    weights.setdefault(weight, {})[direction] = file
            except ValueError:
                continue  # Skip files that don't match expected naming format
        
        # Return only complete up/down pairs
        return {w: p for w, p in weights.items() if 'up' in p and 'down' in p}
    
    def process_and_save(self):
        # Process each up/down pair
        for weight, pair in self.file_pairs.items():
            up_file = os.path.join(self.directory, pair['up'])
            down_file = os.path.join(self.directory, pair['down'])

            # Read CSV files
            df_up = pd.read_csv(up_file)
            df_down = pd.read_csv(down_file)
            
            # Extract distance and pressure columns (assumed to be the first two columns)
            distance_up, pressure_up = df_up.iloc[:, 1], df_up.iloc[:, 0]
            distance_down, pressure_down = df_down.iloc[:, 1], df_down.iloc[:, 0]
            
            max_distance = 200  # Maximum distance to interpolate over
            interpolated_distances = np.arange(0, max_distance + 1, 1)  # Step of 1 mm
            print(interpolated_distances)  # Debug print
            
            # Create interpolation functions
            f_up = interp.interp1d(distance_up, pressure_up, kind=INTERPOLATION_TYPE, fill_value='extrapolate')
            f_down = interp.interp1d(distance_down, pressure_down, kind=INTERPOLATION_TYPE, fill_value='extrapolate')
            
            # Interpolate pressure values over the new distance grid
            interpolated_up = f_up(interpolated_distances)
            interpolated_down = f_down(interpolated_distances)

            # Stack both interpolated arrays for saving
            output_data = np.vstack([interpolated_up, interpolated_down])

            # Create output filename with weight info
            output_filename = os.path.join(self.directory, f'DtoP_{weight}.csv')

            # Round and convert to integer
            output_data = np.round(output_data).astype(int)

            # Save to CSV with a header showing weight
            np.savetxt(output_filename, output_data, delimiter=',', header=f'# weight={weight}', comments='', fmt='%d')

            print(f'Saved: {output_filename}')  # Confirmation message

class CSVApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()  # Setup the UI
    
    def initUI(self):
        self.layout = QtWidgets.QVBoxLayout()

        # Button to select input directory
        self.select_dir_btn = QtWidgets.QPushButton('Select Directory')
        self.select_dir_btn.clicked.connect(self.select_directory)

        # Button to start processing
        self.process_btn = QtWidgets.QPushButton('Process CSV Files')
        self.process_btn.clicked.connect(self.process_csv_files)

        # Add buttons to layout
        self.layout.addWidget(self.select_dir_btn)
        self.layout.addWidget(self.process_btn)
        self.setLayout(self.layout)
    
    def select_directory(self):
        # Open folder selection dialog
        dir_name = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if dir_name:
            self.processor = CSVProcessor(dir_name)  # Create processor instance
            QMessageBox.information(self, 'Success', f'Found {len(self.processor.file_pairs)} valid pairs.')
    
    def process_csv_files(self):
        # Trigger processing if a directory was selected
        if hasattr(self, 'processor'):
            self.processor.process_and_save()
            QMessageBox.information(self, 'Success', 'Processing completed!')
        else:
            QMessageBox.warning(self, 'Error', 'No directory selected.')

# Entry point for the PyQt application
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = CSVApp()
    window.show()
    app.exec_()