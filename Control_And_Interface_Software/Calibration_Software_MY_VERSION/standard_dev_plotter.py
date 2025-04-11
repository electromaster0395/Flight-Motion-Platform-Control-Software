import sys
import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
                             QLabel, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

class StdDevPlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.data_files = {}
        self.colors = plt.cm.tab10.colors  # Color scheme for multiple files
        self.padding_constant = 1.1  # Padding factor for load axis
        self.max_distance_value = 10  # Fixed max scale for distance
        self.max_load_value = 1.5  # Fixed max scale for load
    
    def initUI(self):
        layout = QVBoxLayout()

        self.load_button = QPushButton("Load CSV Files from Directory", self)
        self.load_button.clicked.connect(self.load_csv)
        layout.addWidget(self.load_button)
        
        self.range_label = QLabel("Select Cycle Range:")
        layout.addWidget(self.range_label)

        self.start_cycle_box = QComboBox()
        self.end_cycle_box = QComboBox()
        layout.addWidget(self.start_cycle_box)
        layout.addWidget(self.end_cycle_box)

        self.dist_check = QCheckBox("Plot Distance Cycles", self)
        self.dist_check.setChecked(True)
        layout.addWidget(self.dist_check)

        self.load_check = QCheckBox("Plot Load Cycles", self)
        self.load_check.setChecked(True)
        layout.addWidget(self.load_check)

        self.plot_stddev_button = QPushButton("Plot Standard Deviation", self)
        self.plot_stddev_button.clicked.connect(self.plot_stddev)
        layout.addWidget(self.plot_stddev_button)
        
        self.plot_range_button = QPushButton("Plot Range", self)
        self.plot_range_button.clicked.connect(self.plot_range)
        layout.addWidget(self.plot_range_button)

        self.setLayout(layout)
        self.setWindowTitle("Standard Deviation & Range Plotter")

    def load_csv(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory Containing CSV Files")
        if directory:
            self.data_files.clear()
            for filename in os.listdir(directory):
                if filename.endswith(".csv"):
                    file_path = os.path.join(directory, filename)
                    df = pd.read_csv(file_path)
                    self.data_files[file_path] = df
            
            if self.data_files:
                sample_df = next(iter(self.data_files.values()))
                num_cycles = (sample_df.shape[1] - 1) // 2  # Assuming alternating distance/load cycles
                self.start_cycle_box.clear()
                self.end_cycle_box.clear()
                
                for i in range(1, num_cycles + 1):
                    self.start_cycle_box.addItem(str(i))
                    self.end_cycle_box.addItem(str(i))
                
                self.end_cycle_box.setCurrentIndex(num_cycles - 1)  # Default to max

    def plot_stddev(self):
        self.plot_statistic(np.std, "Standard Deviation")
    
    def plot_range(self):
        self.plot_statistic(lambda x, axis: np.max(x, axis=axis) - np.min(x, axis=axis), "Range")
    
    def plot_statistic(self, stat_func, stat_name):
        if not self.data_files:
            return
        
        start_cycle = int(self.start_cycle_box.currentText())
        end_cycle = int(self.end_cycle_box.currentText())
        
        fig, axes = plt.subplots(nrows=len(self.data_files), ncols=1, figsize=(10, 8 * len(self.data_files)))
        if len(self.data_files) == 1:
            axes = [axes]
        
        for idx, (file, df) in enumerate(self.data_files.items()):
            pressure = df.iloc[:, 0]
            distance_cols = [df.iloc[:, i] for i in range(start_cycle, end_cycle + 1)]
            load_cols = [df.iloc[:, i] for i in range(start_cycle + 5, end_cycle + 6)]  # Adjust for column offset
            
            distance_stat = stat_func(distance_cols, axis=0)
            load_stat = stat_func(load_cols, axis=0)
            
            color = self.colors[idx % len(self.colors)]
            label = os.path.basename(file)
            ax1 = axes[idx]
            ax1.set_xlabel("Pressure (mbar)", fontsize=18)
            ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
            
            if self.dist_check.isChecked() and self.load_check.isChecked():
                ax1.set_ylabel("Distance {} (mm)".format(stat_name), fontsize=18, color='tab:blue')
                ax1.tick_params(axis='y', labelcolor='tab:blue', labelsize=14)
                ax2 = ax1.twinx()
                ax2.set_ylabel("Load {} (kg)".format(stat_name), fontsize=18, color='tab:red')
                ax2.tick_params(axis='y', labelcolor='tab:red', labelsize=14)
                ax2.set_ylim(0, self.max_load_value)
            elif self.dist_check.isChecked():
                ax1.set_ylabel("Distance {} (mm)".format(stat_name), fontsize=18, color='tab:blue')
                ax1.tick_params(axis='y', labelcolor='tab:blue', labelsize=14)
                ax2 = None
            elif self.load_check.isChecked():
                ax1.set_ylabel("Load {} (kg)".format(stat_name), fontsize=18, color='tab:red')
                ax1.tick_params(axis='y', labelcolor='tab:red', labelsize=14)
                ax2 = None
                ax1.set_ylim(0, self.max_load_value)

            if self.dist_check.isChecked():
                ax1.plot(pressure, distance_stat, marker='o', linestyle='-', label=f"Distance {label}", color=color)
                ax1.set_ylim(0, self.max_distance_value)
            
            if self.load_check.isChecked():
                if ax2:
                    ax2.plot(pressure, load_stat, marker='s', linestyle='--', label=f"Load {label}", color=color)
                else:
                    ax1.plot(pressure, load_stat, marker='s', linestyle='--', label=f"Load {label}", color=color)
            
            ax1.set_title(f"{stat_name} - {label}", fontsize=20)
            ax1.legend(fontsize=14)
        
        plt.tight_layout()
        plt.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StdDevPlotter()
    ex.show()
    sys.exit(app.exec_())
