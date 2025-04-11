import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLabel, QHBoxLayout
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Distance Plotting Utility")  # Set window title
        self.setGeometry(100, 100, 900, 700)  # Set window size and position

        self.layout = QVBoxLayout()  # Main vertical layout for the window
        self.setLayout(self.layout)

        button_layout = QHBoxLayout()  # Layout for buttons

        # Button for selecting CSV file
        self.load_button = QPushButton("Select CSV File")
        self.load_button.clicked.connect(self.load_csv)  # Connect button to load_csv method
        button_layout.addWidget(self.load_button)

        # Button for switching between distance and error plots
        self.toggle_button = QPushButton("Switch to Error Plot")
        self.toggle_button.clicked.connect(self.toggle_plot_mode)  # Connect button to toggle_plot_mode method
        self.toggle_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.toggle_button)

        # Button for exporting the plot as an image
        self.export_button = QPushButton("Export Plot as Image")
        self.export_button.clicked.connect(self.export_plot)  # Connect button to export_plot method
        self.export_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.export_button)

        self.layout.addLayout(button_layout)  # Add button layout to main layout

        # Set up the plot canvas
        self.canvas = FigureCanvas(Figure())  # Create an empty figure canvas
        self.ax = self.canvas.figure.add_subplot(111)  # Add subplot to figure
        self.layout.addWidget(self.canvas)  # Add the canvas to the layout

        # Labels for displaying the max error and standard deviation
        self.error_label = QLabel("Max Error: N/A")
        self.std_label = QLabel("Standard Deviation of Error: N/A")
        self.layout.addWidget(self.error_label)
        self.layout.addWidget(self.std_label)

        # Initialize data attributes
        self.df = None  # Dataframe to hold CSV data
        self.max_error = None  # Max error value
        self.std_dev = None  # Standard deviation of error
        self.plot_mode = 'distance'  # Default plot mode is 'distance'

    def load_csv(self):
        """Load the selected CSV file and prepare data for plotting"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")  # Open file dialog
        if not filepath:
            return  # If no file is selected, return

        df = pd.read_csv(filepath)  # Read CSV into dataframe
        df.columns = [col.strip() for col in df.columns]  # Clean column names (remove any extra spaces)

        # Add a new column for the actual measured distance
        df['actual_distance'] = df['contraction_distance mm'] + df['error mm cycle 1']

        # Store the dataframe and calculate error statistics
        self.df = df
        self.max_error = df['error mm cycle 1'].abs().max()  # Calculate max error
        self.std_dev = df['error mm cycle 1'].std()  # Calculate standard deviation of error

        # Update the labels with error statistics
        self.error_label.setText(f"Max Error: {self.max_error:.3f} mm")
        self.std_label.setText(f"Standard Deviation of Error: {self.std_dev:.3f} mm")

        # Enable buttons after CSV is loaded
        self.export_button.setEnabled(True)
        self.toggle_button.setEnabled(True)
        self.plot_mode = 'distance'  # Default to distance plot
        self.toggle_button.setText("Switch to Error Plot")  # Update button text

        self.plot_distance()  # Plot the distance graph initially

    def toggle_plot_mode(self):
        """Switch between distance plot and error plot"""
        if self.plot_mode == 'distance':
            self.plot_mode = 'error'  # Switch to error plot mode
            self.toggle_button.setText("Switch to Distance Plot")  # Update button text
            self.plot_error()  # Plot the error graph
        else:
            self.plot_mode = 'distance'  # Switch back to distance plot mode
            self.toggle_button.setText("Switch to Error Plot")  # Update button text
            self.plot_distance()  # Plot the distance graph

    def plot_distance(self):
        """Plot the contraction distance vs actual distance graph"""
        if self.df is None:
            return  # If no data is available, return

        df = self.df
        max_idx = df['contraction_distance mm'].idxmax()  # Find index of max contraction distance

        self.ax.clear()  # Clear the current plot
        self.canvas.figure.suptitle("Contraction vs Actual Distance", fontsize=18, fontweight='bold')  # Set plot title

        # Plot expected contraction distance (dashed line)
        self.ax.plot(df['contraction_distance mm'],
                     df['contraction_distance mm'],
                     linestyle='--', color='black', label='Expected Distance')

        # Plot measured distance (increasing)
        self.ax.plot(df['contraction_distance mm'][:max_idx + 1],
                     df['actual_distance'][:max_idx + 1],
                     color='blue', label='Measured Distance (Increasing)')

        # Plot measured distance (decreasing)
        self.ax.plot(df['contraction_distance mm'][max_idx + 1:],
                     df['actual_distance'][max_idx + 1:],
                     color='red', label='Measured Distance (Decreasing)')

        # Set labels and legend
        self.ax.set_title("Contraction Distance vs Actual Distance", fontsize=12)
        self.ax.set_xlabel("Contraction Distance (mm)")
        self.ax.set_ylabel("Distance (mm)")
        self.ax.legend()
        self.ax.grid(True)  # Add grid for better readability
        self.canvas.draw()  # Redraw the canvas

    def plot_error(self):
        """Plot the error vs expected contraction distance graph"""
        if self.df is None:
            return  # If no data is available, return

        df = self.df
        max_idx = df['contraction_distance mm'].idxmax()  # Find index of max contraction distance

        self.ax.clear()  # Clear the current plot
        self.canvas.figure.suptitle("Error vs Expected Contraction Distance", fontsize=18, fontweight='bold')  # Set plot title

        self.ax.grid(True)  # Add grid for better readability
        self.ax.set_ylim(-5, 20)  # Set ylim to 20
        self.canvas.draw()  # Redraw the canvas

        # Plot error for increasing distance
        self.ax.plot(df['contraction_distance mm'][:max_idx + 1],
                     df['error mm cycle 1'][:max_idx + 1],
                     color='blue', label='Error (Increasing)')

        # Plot error for decreasing distance
        self.ax.plot(df['contraction_distance mm'][max_idx + 1:],
                     df['error mm cycle 1'][max_idx + 1:],
                     color='red', label='Error (Decreasing)')

        self.ax.axhline(0, linestyle='--', color='gray')  # Add horizontal line at y=0 for reference
        self.ax.set_title("Error vs Contraction Distance", fontsize=12)
        self.ax.set_xlabel("Contraction Distance (mm)")
        self.ax.set_ylabel("Error (mm)")
        self.ax.legend()
        self.ax.grid(True)  # Add grid for better readability
        self.canvas.draw()  # Redraw the canvas

    def export_plot(self):
        """Export the current plot as an image"""
        if self.df is None:
            return  # If no data is available, return

        filepath, _ = QFileDialog.getSaveFileName(self, "Save Plot As Image", "", "PNG Files (*.png)")  # Open save dialog
        if not filepath:
            return  # If no file path is selected, return

        fig = Figure(figsize=(8, 6))  # Create a new figure
        fig.subplots_adjust(top=0.85)  # Make space for big title
        ax = fig.add_subplot(111)  # Add subplot to the figure
        ax.set_ylim(-5, 20)
        df = self.df
        max_idx = df['contraction_distance mm'].idxmax()  # Find index of max contraction distance

        # Plot either the distance or error graph based on current mode
        if self.plot_mode == 'distance':
            fig.suptitle("Contraction vs Actual Distance", fontsize=18, fontweight='bold')

            ax.plot(df['contraction_distance mm'],
                    df['contraction_distance mm'],
                    linestyle='--', color='black', label='Expected Distance')

            ax.plot(df['contraction_distance mm'][:max_idx + 1],
                    df['actual_distance'][:max_idx + 1],
                    color='blue', label='Measured Distance (Increasing)')

            ax.plot(df['contraction_distance mm'][max_idx + 1:],
                    df['actual_distance'][max_idx + 1:],
                    color='red', label='Measured Distance (Decreasing)')

            ax.set_title("Contraction Distance vs Actual Distance", fontsize=12)
            ax.set_xlabel("Contraction Distance (mm)")
            ax.set_ylabel("Distance (mm)")
        else:
            fig.suptitle("Error vs Expected Contraction Distance", fontsize=18, fontweight='bold')

            ax.plot(df['contraction_distance mm'][:max_idx + 1],
                    df['error mm cycle 1'][:max_idx + 1],
                    color='blue', label='Error (Increasing)')

            ax.plot(df['contraction_distance mm'][max_idx + 1:],
                    df['error mm cycle 1'][max_idx + 1:],
                    color='red', label='Error (Decreasing)')

            ax.axhline(0, linestyle='--', color='gray')
            ax.set_title("Error vs Contraction Distance", fontsize=12)
            ax.set_xlabel("Contraction Distance (mm)")
            ax.set_ylabel("Error (mm)")

        ax.legend()  # Add legend
        ax.grid(True)  # Add grid

        # Add error statistics to the plot
        stat_text = f"Max Error: {self.max_error:.3f} mm\nStd Dev: {self.std_dev:.3f} mm"
        ax.text(0.95, 0.05, stat_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray'))

        fig.savefig(filepath, dpi=300, bbox_inches='tight')  # Save plot to the selected file path
        print(f"Plot exported to: {filepath}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()  # Show the plot window
    sys.exit(app.exec_())  # Execute the application
