import os

class DefaultModule:
    """
    The Base Module for all battery types. 
    Specific modules (like Makita) will inherit from this.
    """
    def __init__(self):
        self.name = "Default Module"
        self.description = "Select a module to begin diagnostics."
        # This dictionary will store the live data
        self.data_points = {
            "Status": "Idle",
            "Voltage": "0.00 V",
            "Capacity": "0 %"
        }

    def get_info_text(self):
        return "This is the base module. Please select a specific battery type."

    def get_parameters(self):
        """Returns the list of parameters this module supports."""
        return self.data_points.keys()

    def update_data(self, serial_connection):
        """
        Logic for reading data from the Arduino. 
        Specific battery modules will override this method.
        """
        # Placeholder for simulation
        pass
