import sys
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class PlotterApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QtWidgets.QVBoxLayout()

        # Button for selecting CSV file
        self.browse_file_btn = QtWidgets.QPushButton('Browse for CSV File')
        self.browse_file_btn.clicked.connect(self.browse_file)

        # Button for plotting the data
        self.plot_btn = QtWidgets.QPushButton('Plot CSV Data')
        self.plot_btn.clicked.connect(self.plot_data)

        # Add buttons to the layout
        self.layout.addWidget(self.browse_file_btn)
        self.layout.addWidget(self.plot_btn)

        # Set layout
        self.setLayout(self.layout)

        self.selected_file = None

    def browse_file(self):
        # Open file dialog to select a CSV file
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select CSV File', '', 'CSV Files (*.csv)')
        if file_name:
            self.selected_file = file_name
            QMessageBox.information(self, 'File Selected', f'Selected file: {file_name}')

    def plot_data(self):
        # Check if file is selected
        if self.selected_file:
            try:
                # Read CSV file (skip the first row which contains weight info)
                df = pd.read_csv(self.selected_file, skiprows=1, header=None)

                # Ensure we have at least two rows
                if df.shape[0] < 2:
                    raise ValueError("CSV file doesn't contain enough data for plotting.")

                # Extract the second and third rows for plotting (pressure values)
                pressure_up = df.iloc[0, :].values  # First row of pressures
                pressure_down = df.iloc[1, :].values  # Second row of pressures

                print(pressure_up)

                # The x-axis (distance) is just the index of the values, starting from 1
                distance = list(range(1, len(pressure_up) + 1))

                # Plot the data
                plt.figure(figsize=(8, 6))
                
                plt.plot(distance, pressure_up, label="Pressure Up", 
                         color='b', linestyle='-', marker='o')  # Line with points for Pressure Up
                
                plt.plot(distance, pressure_down, label="Pressure Down", 
                         color='r', linestyle='-', marker='x')  # Line with points for Pressure Down

                # Add scatter for individual points (optional, as we already added markers to the plot)
                plt.scatter(distance, pressure_up, color='b', zorder=5)
                plt.scatter(distance, pressure_down, color='r', zorder=5)

                plt.xlabel('Distance (mm)')
                plt.ylabel('Pressure (mbar)')
                plt.title('Pressure vs Distance Plot')
                plt.legend()
                plt.grid(True)
                plt.show()

            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to read and plot the CSV file.\n{str(e)}')
        else:
            QMessageBox.warning(self, 'Error', 'No file selected. Please select a CSV file first.')

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = PlotterApp()
    window.setWindowTitle("CSV Plotter")
    window.setGeometry(100, 100, 300, 150)  # Set window size and position
    window.show()
    sys.exit(app.exec_())
