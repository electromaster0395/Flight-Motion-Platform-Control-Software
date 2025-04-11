import numpy as np
import pandas as pd

class DistanceToPressure:
    def __init__(self, csv_path):
        # Load the CSV file using pandas
        self.data = pd.read_csv(csv_path)

        rows = self.data.values.tolist()  # Convert the data into a list of rows
        
        # Ensure I am getting the row data (print all values in the second column for verification)
        for i in rows:
            print(i[1])

        # Store the rows corresponding to weight-direction pairs in self.weight_direction_rows
        self.weight_direction_rows = rows
        # Define a list of known weights
        self.weights = [13, 24, 33, 43]
        self.is_going_up = True  # Initial direction of movement (default: True, going up)
        self.last_distance = 0  # Track the last distance

    def set_load(self, load):
        """Set the load and find the closest weights to interpolate between."""
        # If the load is not in the predefined weights, calculate the closest lower and upper weights
        if load not in self.weights:
            lower_weight = max([w for w in self.weights if w < load], default=None)
            upper_weight = min([w for w in self.weights if w > load], default=None)

            # If no valid lower or upper weight, raise an error
            if lower_weight is None and upper_weight is None:
                raise ValueError(f"No weights available for load {load}.")
            # If only the lower weight is available, use it and set interpolation factor to 0
            elif lower_weight is None:
                self.load = (upper_weight, upper_weight)
                self.interpolation_factor = 0
            # If only the upper weight is available, use it and set interpolation factor to 0
            elif upper_weight is None:
                self.load = (lower_weight, lower_weight)
                self.interpolation_factor = 0
            # Otherwise, use both lower and upper weights for interpolation
            else:
                self.load = (lower_weight, upper_weight)
                self.interpolation_factor = (load - lower_weight) / (upper_weight - lower_weight)
        else:
            # If the load matches one of the predefined weights, no interpolation is needed
            self.load = (load, load)
            self.interpolation_factor = 0

    def get_pressure(self, distance):
        """
        Calculate the pressure based on the given distance. 
        The pressure is calculated by interpolating between pressure values corresponding 
        to the lower and upper weights at the specified distance.
        """
        # NOTE FOR FUTURE ME: Change curves to be set only once when setting load for better efficiency!
        
        lower_weight, upper_weight = self.load
        
        # Find the index of the lower and upper weights in the list of weights
        lower_row_index = self.weights.index(lower_weight)
        upper_row_index = self.weights.index(upper_weight)

        lower_weight_rows = []
        upper_weight_rows = []

        # Find the rows corresponding to the lower and upper weights (for both directions)
        lower_weight_rows.append(self.weight_direction_rows[lower_row_index])
        lower_weight_rows.append(self.weight_direction_rows[lower_row_index + 4])

        upper_weight_rows.append(self.weight_direction_rows[upper_row_index])
        upper_weight_rows.append(self.weight_direction_rows[upper_row_index + 4])

        # Print values from the "up" and "down" curves to check if correct rows are selected
        print(upper_weight_rows[0][4], upper_weight_rows[1][4])

        # Determine the direction of movement based on whether the distance has increased or decreased
        self.is_going_up = distance - self.last_distance > 0

        # Initialize the pressure variable
        lerp_pressure = -1

        # Interpolate the pressure based on the direction (up or down)
        if self.is_going_up:
            # Interpolate for the "up" direction using the rows for the lower and upper weights
            lerp_pressure = lower_weight_rows[0][distance] + (self.interpolation_factor * (upper_weight_rows[0][distance] 
                                                                                           - lower_weight_rows[0][distance]))
        else:
            # Interpolate for the "down" direction using the rows for the lower and upper weights
            lerp_pressure = lower_weight_rows[1][distance] + (self.interpolation_factor * (upper_weight_rows[1][distance] 
                                                                                           - lower_weight_rows[1][distance]))

        # Update the last distance for future calculations
        self.last_distance = distance

        # Return the pressure, rounded to the nearest integer
        return round(lerp_pressure)

# Example usage:
# Create an instance of the DistanceToPressure class by providing the path to your CSV file
#muscle = DistanceToPressure("output\\wheelchair_DtoP.csv")

# Set the load (for example, 40kg)
#muscle.set_load(24)

# Retrieve the pressure for a given distance (e.g., distance = 10, up direction)
#try:
#    for i in range(0, 10):
#        pressure = muscle.get_pressure(i)
#        print(f"Pressure at {i}mm distance (up direction): {pressure} mbar")
#
#    for i in range(10, 0, -1):
#        pressure = muscle.get_pressure(i)
#        print(f"Pressure at {i}mm distance (down direction): {pressure} mbar")
#
#except IndexError as e:
#    print(f"Error: {e}")
