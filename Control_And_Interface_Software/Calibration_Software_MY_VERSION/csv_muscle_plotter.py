import sys  # System-specific parameters and functions
import os  # Provides functions for interacting with the operating system
import pandas as pd  # Library for data manipulation and analysis
import matplotlib.pyplot as plt  # Library for creating static, animated, and interactive visualizations
import matplotlib.cm as cm
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTextEdit  # PyQt5 modules for GUI development
import re

class CSVPlotter(QWidget):  # Defines a class that inherits from QWidget for creating a GUI application
    def __init__(self):
        super().__init__()  # Calls the parent class constructor
        self.initUI()  # Initializes the user interface

    def initUI(self):
        self.CMAP = "viridis"
        layout = QVBoxLayout()  # Creates a vertical box layout
        
        self.label = QLabel("Select a CSV file or folder")  # Label to display selected file/folder
        layout.addWidget(self.label)  # Adds label to layout
        
        self.btn_browse = QPushButton("Browse", self)  # Button for browsing files/folders
        self.btn_browse.clicked.connect(self.browse)  # Connects button click event to browse method
        layout.addWidget(self.btn_browse)  # Adds button to layout
        
        self.btn_plot = QPushButton("Plot", self)  # Button for plotting data
        self.btn_plot.clicked.connect(self.plot_data)  # Connects button click event to plot_data method
        layout.addWidget(self.btn_plot)  # Adds button to layout
        
        self.btn_stddev = QPushButton("Show Load Standard Deviation", self)  # Button to show standard deviation for Load
        self.btn_stddev.clicked.connect(self.show_stddev)  # Connects button click event to show_stddev method
        layout.addWidget(self.btn_stddev)  # Adds button to layout
        
        self.btn_plot_stddev = QPushButton("Plot Load Standard Deviation", self)  # Button to plot standard deviation for Load
        self.btn_plot_stddev.clicked.connect(self.plot_stddev)  # Connects button click event to plot_stddev method
        layout.addWidget(self.btn_plot_stddev)  # Adds button to layout

        self.btn_plot_range = QPushButton("Plot Load Range", self)  # Button to plot load range
        self.btn_plot_range.clicked.connect(self.plot_load_range)  # Connect to method
        layout.addWidget(self.btn_plot_range)  # Add button to layout

        self.btn_plot_noise = QPushButton("Plot Distance Range Per Pressure", self)  # Button to plot noise data
        self.btn_plot_noise.clicked.connect(self.plot_noise)  # Connect to method
        layout.addWidget(self.btn_plot_noise)  # Add button to layout

        self.btn_plot_noise = QPushButton("Plot Cycles", self)  # Button to plot noise data
        self.btn_plot_noise.clicked.connect(self.plot_cycle_data)  # Connect to method
        layout.addWidget(self.btn_plot_noise)  # Add button to layout

        self.btn_plot_stddev_cycles = QPushButton("Plot StdDev of Distance & Load Cycles", self)
        self.btn_plot_stddev_cycles.clicked.connect(self.plot_standard_deviation_cycles)
        layout.addWidget(self.btn_plot_stddev_cycles)

        self.btn_plot_range_cycles = QPushButton("Plot Range of Distance & Load Cycles", self)
        self.btn_plot_range_cycles.clicked.connect(self.plot_range_cycles)
        layout.addWidget(self.btn_plot_range_cycles)

        self.text_output = QTextEdit(self)  # Text box to display standard deviation results
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output)
        
        self.setLayout(layout)  # Sets the layout for the window
        self.setWindowTitle("CSV Data Plotter")  # Sets the window title
        self.setGeometry(200, 200, 500, 300)  # Defines the size and position of the window
        
        self.file_paths = []  # Initializes an empty list to store selected file(s)

    def browse(self):
        options = QFileDialog.Options()  # File dialog options
        path = QFileDialog.getExistingDirectory(self, "Select Folder", "", options=options)  # Opens a folder selection dialog
        
        if path:  # If a folder is selected
            self.file_paths = self.find_csv_files(path)  # Finds all CSV files in the selected folder
            self.label.setText(f"Selected Folder: {path}")  # Updates label text
        else:  # If a file is selected
            file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)", options=options)  # Opens a file selection dialog
            if file_path:
                self.file_paths = self.find_csv_pairs(file_path)  # Finds corresponding up/down curve pairs
                self.label.setText(f"Selected File: {file_path}")  # Updates label text

    def find_csv_files(self, folder_path):
        """Find all valid CSV files in the folder."""
        csv_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".csv")]  # Gets all CSV files in the folder
        return csv_files  # Returns the list of CSV file paths

    def find_csv_pairs(self, file_path):
        """Find the corresponding up/down curve pair if a single file is selected."""
        base_name = os.path.basename(file_path)  # Extracts the file name
        folder = os.path.dirname(file_path)  # Extracts the folder path
        
        if "up_curve" in base_name:  # Checks if the file is an up curve file
            paired_file = base_name.replace("up_curve", "down_curve")  # Finds corresponding down curve file
        elif "down_curve" in base_name:  # Checks if the file is a down curve file
            paired_file = base_name.replace("down_curve", "up_curve")  # Finds corresponding up curve file
        else:
            return [file_path]  # Returns the selected file if no pair is found
        
        paired_path = os.path.join(folder, paired_file)  # Constructs the full path of the paired file
        return [file_path, paired_path] if os.path.exists(paired_path) else [file_path]  # Returns both files if the pair exists

    def show_stddev(self):
        if not self.file_paths:
            self.text_output.setText("No valid CSV files selected!")
            return
        
        result_text = "Standard Deviation of Load Column:\n"
        
        for file in self.file_paths:
            try:
                df = pd.read_csv(file)
                if "Load(kg)" in df.columns:
                    stddev = df["Load(kg)"].std()
                    result_text += f"\nFile: {os.path.basename(file)}\nLoad Standard Deviation: {stddev:.4f}\n"
                else:
                    result_text += f"\nFile: {os.path.basename(file)}\nLoad column not found!\n"
            except Exception as e:
                result_text += f"\nError reading {file}: {e}\n"
        
        self.text_output.setText(result_text)

    def plot_stddev(self):
        if not self.file_paths:
            self.text_output.setText("No valid CSV files selected!")
            return

        file_names = []
        stddev_values = []
        base_names = []  # Stores unique load identifiers
        color_map = {}  # Maps base names to colors

        # Extract base names and compute standard deviations
        for file in self.file_paths:
            try:
                df = pd.read_csv(file)
                if "Load(kg)" in df.columns:
                    stddev = df["Load(kg)"].std()
                    file_name = os.path.basename(file)
                    
                    # Extract base name (removing "up_curve" or "down_curve")
                    base_name = file_name.replace("up_curve", "").replace("down_curve", "").replace(".csv", "")
                    
                    file_names.append(file_name)
                    stddev_values.append(stddev)
                    base_names.append(base_name)
            except Exception as e:
                print(f"Error reading {file}: {e}")

        if not file_names:
            self.text_output.setText("No valid CSV files found!")
            return

        # Generate unique colors for each base name
        unique_base_names = list(set(base_names))
        cmap = cm.get_cmap(self.CMAP, len(unique_base_names))  # Use a colormap
        colors = {name: cmap(i) for i, name in enumerate(unique_base_names)}  # Assign colors

        # Plot bars with shared colors for each base name
        plt.figure(figsize=(10, 6))
        bars = [plt.bar(file_names[i], stddev_values[i], color=colors[base_names[i]]) for i in range(len(file_names))]

        # Create a legend mapping base names to colors
        legend_handles = [plt.Rectangle((0, 0), 1, 1, color=colors[name]) for name in unique_base_names]
        plt.legend(legend_handles, unique_base_names, title="Load Groups", loc="upper left")

        plt.xlabel("CSV Files")
        plt.ylabel("Standard Deviation of Load (kg)")
        plt.title("Load Standard Deviation for Each CSV File")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()

    def plot_cycle_data(self):
        """Plots all Distance and Load Cycles vs Pressure for multiple CSV files."""

        if not self.file_paths:
            self.label.setText("No valid CSV files selected!")
            return

        plt.figure()

        # Create figure and primary axis for Pressure vs Distance Cycles
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()  # Secondary y-axis for Load Cycles

        base_names = []
        data = {}

        # Extract base names and group files
        for file in self.file_paths:
            try:
                file_name = os.path.basename(file)
                base_name = file_name.replace("up_curve", "").replace("down_curve", "").replace(".csv", "").strip()

                if base_name not in data:
                    data[base_name] = []
                data[base_name].append(file)

                if base_name not in base_names:
                    base_names.append(base_name)
            except Exception as e:
                print(f"Error processing {file}: {e}")

        # Define explicit contrasting colors for up/down curves
        color_pairs = {
            "12kg_": ("red", "blue"),
            "13kg_": ("green", "purple"),
            "24kg_": ("orange", "cyan"),
            "33kg_": ("brown", "magenta"),
            "43kg_": ("yellow", "purple")
        }

        max_load_value = 0  # Track max load value for scaling

        name = ""
        # Loop through grouped data
        for base_name, files in data.items():
            name = base_name
            if base_name not in color_pairs:
                print(f"Warning: No predefined color pair for {base_name}, skipping.")
                continue

            up_color, down_color = color_pairs[base_name]

            for file in files:
                try:
                    df = pd.read_csv(file)
                    label_suffix = "Up" if "up_curve" in file else "Down"
                    base_color = up_color if "up_curve" in file else down_color

                    # Extract Distance and Load cycle columns dynamically
                    distance_cols = sorted(
                        [col for col in df.columns if "Distance Cycle" in col],
                        key=lambda x: int(x.split("Cycle ")[-1].split(" ")[0]),
                        reverse=True  # Ensure Cycle 5 is first (darkest)
                    )
                    load_cols = sorted(
                        [col for col in df.columns if "Load Cycle" in col],
                        key=lambda x: int(x.split("Cycle ")[-1].split(" ")[0]),
                        reverse=True
                    )

                    # Update max load value
                    max_load_value = max(max_load_value, df[load_cols].values.max())

                    # Generate shades of base color for cycles (lightest to darkest)
                    distance_shades = [plt.cm.Reds(i / len(distance_cols) + 0.2) if "up_curve" in file else plt.cm.Blues(i / len(distance_cols) + 0.2) 
                                       for i in range(len(distance_cols))]
                    load_shades = [plt.cm.Reds(i / len(load_cols) + 0.2) if "up_curve" in file else plt.cm.Blues(i / len(load_cols) + 0.2) 
                                   for i in range(len(load_cols))]

                    # Plot each Distance cycle on the primary y-axis
                    for i, cycle_col in enumerate(distance_cols):
                        ax1.plot(df["Pressure (mbar)"], df[cycle_col],
                                 label=f"{base_name} {cycle_col} ({label_suffix})",
                                 marker="o", linestyle="-", color=distance_shades[len(distance_shades)-i-1], alpha=0.8)

                    # Plot each Load cycle on the secondary y-axis
                    for i, cycle_col in enumerate(load_cols):
                        ax2.plot(df["Pressure (mbar)"], df[cycle_col],
                                 label=f"{base_name} {cycle_col} ({label_suffix})",
                                 marker="x", linestyle=(0, (1, 1)), color=load_shades[len(load_shades)-i-1], alpha=0.8)  # Fine dotted line

                except Exception as e:
                    print(f"Error reading {file}: {e}")
        
        name = name.replace("_", "")
        # Configure axis labels and title
        ax1.set_xlabel("Pressure (mbar)", fontsize=20)
        ax1.set_ylabel("Distance (mm)", color="tab:blue", fontsize=20)
        ax2.set_ylabel("Load (kg)", color="tab:red", fontsize=20)
        ax1.set_title(f"Pressure vs Distance and Load Cycles {name}", fontsize=30)

        # Set load axis limit with a margin
        ax2.set_ylim(0, max_load_value * 1.1)  # 10% margin above max load

        # Combine legends from both axes
        ax1_handles, ax1_labels = ax1.get_legend_handles_labels()
        ax2_handles, ax2_labels = ax2.get_legend_handles_labels()
        ax1.legend(ax1_handles + ax2_handles, ax1_labels + ax2_labels, loc="upper left", fontsize="small", bbox_to_anchor=(-0.2, 1))

        # Show grid for better readability
        ax1.grid(True)

        # Show the plot
        plt.tight_layout()
        plt.show()



    def plot_load_range(self):
        if not self.file_paths:
            self.text_output.setText("No valid CSV files selected!")
            return

        file_names = []
        load_ranges = []
        file_base_names = []  # List to track base names for each file

        data = {}

        # Extract base names and group files
        for file in self.file_paths:
            try:
                file_name = os.path.basename(file)
                base_name = file_name.replace("up_curve", "").replace("down_curve", "").replace(".csv", "")

                if base_name not in data:
                    data[base_name] = []
                data[base_name].append(file)
            except Exception as e:
                print(f"Error processing {file}: {e}")

        # Generate unique colors for each base name
        base_names = list(data.keys())  # Get all unique base names
        cmap = cm.get_cmap(self.CMAP, len(base_names))  # Assign unique colors
        colors = {name: cmap(i) for i, name in enumerate(base_names)}

        # Extract load ranges
        for base_name, files in data.items():
            for file in files:
                try:
                    df = pd.read_csv(file)
                    if "Load(kg)" in df.columns:
                        load_range = df["Load(kg)"].max() - df["Load(kg)"].min()
                        file_names.append(os.path.basename(file))  # Store filename
                        load_ranges.append(load_range)  # Store load range
                        file_base_names.append(base_name)  # Track base name for color mapping
                except Exception as e:
                    print(f"Error reading {file}: {e}")

        if not file_names:
            self.text_output.setText("No valid CSV files found!")
            return

        # Plot bars with shared colors for each base name
        plt.figure(figsize=(10, 6))
        bars = [plt.bar(file_names[i], load_ranges[i], color=colors[file_base_names[i]]) for i in range(len(file_names))]

        # Create a legend mapping base names to colors
        legend_handles = [plt.Rectangle((0, 0), 1, 1, color=colors[name]) for name in base_names]
        plt.legend(legend_handles, base_names, title="Load Groups", loc="upper left")

        plt.xlabel("CSV Files")
        plt.ylabel("Load Range (kg)")
        plt.title("Load Range for Each CSV File")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()

    def plot_data(self):
        if not self.file_paths:
            self.label.setText("No valid CSV files selected!")
            return

        plt.figure()

        # Create figure and primary axis for Pressure vs Distance
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()  # Secondary y-axis for Load

        base_names = []
        data = {}

        # Extract base names and group files
        for file in self.file_paths:
            try:
                file_name = os.path.basename(file)

                # Remove "_up_curve_averaged_x__y" and "_down_curve_averaged_x__y" portions
                base_name = re.sub(r"_(up_curve|down_curve)_averaged_\d+__\d+", "", file_name)
                base_name = base_name.replace(".csv", "").strip()

                if base_name not in data:
                    data[base_name] = []
                data[base_name].append(file)

                if base_name not in base_names:
                    base_names.append(base_name)
            except Exception as e:
                print(f"Error processing {file}: {e}")

        # Define explicit contrasting colors for up/down curves
        color_pairs = {
            "13kg": ("red", "red"),
            "24kg": ("blue", "blue"),
            "33kg": ("yellow", "yellow"),
            "43kg": ("black", "black")
        }

        # Loop through grouped data
        for base_name, files in data.items():
            if base_name not in color_pairs:
                print(f"Warning: No predefined color pair for {base_name}, skipping.")
                continue

            up_color, down_color = color_pairs[base_name]

            for file in files:
                try:
                    df = pd.read_csv(file)
                    is_up_curve = "up_curve" in file
                    label_suffix = "Up" if is_up_curve else "Down"
                    base_color = up_color if is_up_curve else down_color

                    # Plot Pressure vs Distance on primary y-axis (solid line)
                    ax1.plot(df["Pressure (mbar)"], df["Distance (mm)"],
                            label=f"{base_name} Distance ({label_suffix})",
                            marker="o", linestyle="-", color=base_color, alpha=0.8)

                    # Plot Pressure vs Load on secondary y-axis (dashed line with x markers)
                    ax2.plot(df["Pressure (mbar)"], df["Load(kg)"],
                            label=f"{base_name} Load ({label_suffix})",
                            marker="x", linestyle="--", color=base_color, alpha=0.8)

                except Exception as e:
                    print(f"Error reading {file}: {e}")

        # Configure axis labels and title
        ax1.set_xlabel("Pressure (mbar)", fontsize=20)
        ax1.set_ylabel("Distance (mm)", color="tab:blue", fontsize=20)
        ax2.set_ylabel("Load (kg)", color="tab:red", fontsize=20)
        ax1.set_title("Pressure vs Distance and Load (Up and Down Curves for Cycles 3 to 5)", fontsize=30)

        # Set load axis limit with a margin
        ax2.set_ylim(0, 50)

        # Combine legends from both axes
        ax1_handles, ax1_labels = ax1.get_legend_handles_labels()
        ax2_handles, ax2_labels = ax2.get_legend_handles_labels()
        ax1.legend(ax1_handles + ax2_handles, ax1_labels + ax2_labels, loc="upper left", fontsize=14, bbox_to_anchor=(-0.2, 1))

        # Show grid for better readability
        ax1.grid(True)

        # Show the plot
        plt.tight_layout()
        plt.show()
                
    def plot_noise(self):
        if not self.file_paths:
            self.text_output.setText("No valid CSV files selected!")
            return

        plt.figure(figsize=(10, 6))  # Create a new figure for plotting
        colors = cm.get_cmap(self.CMAP, len(self.file_paths))  # Generate colors per file
        file_colors = {}  # Dictionary to track colors assigned per file

        for i, file in enumerate(self.file_paths):
            try:
                df = pd.read_csv(file)

                # Ensure that the necessary columns are present
                if "Pressure (mbar)" in df.columns and "Distance Range (mm)" in df.columns:
                    pressure = df["Pressure (mbar)"].values
                    distance_range = df["Distance Range (mm)"].values

                    # Assign a unique color per file
                    color = colors(i)
                    file_name = os.path.basename(file)

                    # Determine if it's an "Up Curve" or "Down Curve"
                    curve_type = "Up Curve" if "up_curve" in file_name else "Down Curve"

                    # Avoid duplicate legend labels (one per file)
                    if file_name not in file_colors:
                        plt.plot(pressure, distance_range, 'o-', color=color, label=curve_type)
                        file_colors[file_name] = color  # Store assigned color
                    else:
                        plt.plot(pressure, distance_range, 'o-', color=color)  # No label to avoid duplicate

            except Exception as e:
                print(f"Error reading {file}: {e}")

        # Set plot labels and title
        plt.xlabel("Pressure (mbar)")
        plt.ylabel("Distance Range (mm)")
        plt.title("Distance Range vs Pressure for Each Curve")

        # Display the legend with only "Up Curve" and "Down Curve" once
        plt.legend(loc="upper left")

        # Add grid for better readability
        plt.grid(True)
        
        # Adjust layout to avoid clipping
        plt.tight_layout()

        # Show the plot
        plt.show()

    def plot_range_cycles(self):
        """Plots the standard deviation of Distance and Load across 5 cycles for each pressure setting."""
        if not self.file_paths:
            self.text_output.setText("No valid CSV files selected!")
            return

        plt.figure(figsize=(10, 6))

        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()  # Secondary y-axis for Load Standard Deviation


        # Extract unique base filenames
        base_names = [os.path.basename(file) for file in self.file_paths]

        # Generate unique colors for each base name using a colormap
        cmap = cm.get_cmap(self.CMAP, len(base_names))  # Use the specified colormap
        colors = {name: cmap(i) for i, name in enumerate(base_names)}

        for file in self.file_paths:
            try:
                df = pd.read_csv(file)
                file_name = os.path.basename(file)

                # Identify distance and load cycle columns
                distance_cols = [col for col in df.columns if "Distance Cycle" in col]
                load_cols = [col for col in df.columns if "Load Cycle" in col]

                # Ensure there are exactly 5 cycles
                if len(distance_cols) != 5 or len(load_cols) != 5:
                    print(f"Skipping {file_name}: Expected 5 cycles, found {len(distance_cols)} distance and {len(load_cols)} load cycles.")
                    continue

                # Compute range for each pressure setting
                distance_range = df[distance_cols].max(axis=1) - df[distance_cols].min(axis=1)
                load_range = df[load_cols].max(axis=1) - df[load_cols].min(axis=1)

                # Extract Pressure column
                pressure = df["Pressure (mbar)"]

                # Assign a unique color to this file
                color = colors[file_name]

                # Plot Range of Distance
                ax1.plot(pressure, distance_range, marker="o", linestyle="-", label=f"{file_name} Distance Range", color=color)

                # Plot Range of Load
                ax2.plot(pressure, load_range, marker="x", linestyle="--", label=f"{file_name} Load Range", color=color)

            except Exception as e:
                print(f"Error processing {file_name}: {e}")

        # Configure axes labels and title
        ax1.set_xlabel("Pressure (mbar)")
        ax1.set_ylabel("Distance Range (mm)", color="blue")
        ax2.set_ylabel("Load Range (kg)", color="red")
        ax1.set_title("Range of Distance & Load across 5 Cycles")

        # Combine legends from both axes
        ax1_handles, ax1_labels = ax1.get_legend_handles_labels()
        ax2_handles, ax2_labels = ax2.get_legend_handles_labels()
        ax1.legend(ax1_handles + ax2_handles, ax1_labels + ax2_labels, loc="upper left")

        ax1.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_standard_deviation_cycles(self):
        """Plots the standard deviation of Distance and Load across 5 cycles for each pressure setting."""
        if not self.file_paths:
            self.text_output.setText("No valid CSV files selected!")
            return

        plt.figure(figsize=(10, 6))

        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()  # Secondary y-axis for Load Standard Deviation

        # Extract unique base filenames
        base_names = [os.path.basename(file) for file in self.file_paths]

        # Generate unique colors for each base name using a colormap
        cmap = cm.get_cmap(self.CMAP, len(base_names))  # Use the specified colormap
        colors = {name: cmap(i) for i, name in enumerate(base_names)}

        for file in self.file_paths:
            try:
                df = pd.read_csv(file)
                file_name = os.path.basename(file)

                # Identify distance and load cycle columns
                distance_cols = [col for col in df.columns if "Distance Cycle" in col]
                load_cols = [col for col in df.columns if "Load Cycle" in col]

                # Ensure there are exactly 5 cycles
                if len(distance_cols) != 5 or len(load_cols) != 5:
                    print(f"Skipping {file_name}: Expected 5 cycles, found {len(distance_cols)} distance and {len(load_cols)} load cycles.")
                    continue

                # Compute standard deviation for each pressure setting
                distance_std = df[distance_cols].std(axis=1)
                load_std = df[load_cols].std(axis=1)

                # Extract Pressure column
                pressure = df["Pressure (mbar)"]

                # Assign a unique color to this file
                color = colors[file_name]

                # Plot Standard Deviation of Distance
                ax1.plot(pressure, distance_std, marker="o", linestyle="-", label=f"{file_name} Distance StdDev", color=color)

                # Plot Standard Deviation of Load
                ax2.plot(pressure, load_std, marker="x", linestyle="--", label=f"{file_name} Load StdDev", color=color)

            except Exception as e:
                print(f"Error processing {file}: {e}")

        # Configure axes labels and title
        ax1.set_xlabel("Pressure (mbar)")
        ax1.set_ylabel("Distance Standard Deviation (mm)", color="blue")
        ax2.set_ylabel("Load Standard Deviation (kg)", color="red")
        ax1.set_title("Standard Deviation of Distance & Load across 5 Cycles")

        # Combine legends from both axes
        ax1_handles, ax1_labels = ax1.get_legend_handles_labels()
        ax2_handles, ax2_labels = ax2.get_legend_handles_labels()
        ax1.legend(ax1_handles + ax2_handles, ax1_labels + ax2_labels, loc="upper left")

        ax1.grid(True)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVPlotter()
    window.show()
    sys.exit(app.exec_())