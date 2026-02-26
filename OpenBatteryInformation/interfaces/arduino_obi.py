# OBI-1 Diagnostic Tool
# Copyright (C) 2026 Ray Ellison
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Portions Derived from "Open Battery Information" 
# Copyright (c) 2024 Martin Jansson (MIT License)import serial

import serial.tools.list_ports
import time

class SerialInterface:
    def __init__(self, baudrate=9600, debug_callback=None):
        self.serial = serial.Serial()
        self.serial.baudrate = baudrate
        self.serial.timeout = 0.5
        self.debug_callback = debug_callback

    def log(self, message):
        if self.debug_callback:
            self.debug_callback(message)
        else:
            print(f"[DEBUG] {message}")

    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port):
        try:
            self.serial.port = port
            self.serial.open()
            # Crucial: Wait for Arduino to finish rebooting after serial DTR toggle
            time.sleep(2)
            self.serial.reset_input_buffer()
            self.log(f"Connected to {port} at {self.serial.baudrate} baud.")
            return True
        except Exception as e:
            self.log(f"Connection failed: {e}")
            return False

    def disconnect(self):
        if self.serial.is_open:
            self.serial.close()
            self.log("Disconnected.")

    def send_command(self, cmd_list):
        """Sends a binary packet list."""
        if not self.serial.is_open:
            return False
        try:
            packet = bytes(cmd_list)
            self.serial.write(packet)
            self.log(f">> Sent Packet: {packet.hex(' ').upper()}")
            return True
        except Exception as e:
            self.log(f"Write error: {e}")
            return False

    def request(self, cmd_list, expected_len=1, wait_time=0.6):
        """Sends binary packet and waits for raw byte response."""
        if not self.serial.is_open:
            return None
        
        try:
            self.serial.reset_input_buffer()
            packet = bytes(cmd_list)
            self.serial.write(packet)
            self.log(f">> Request: {packet.hex(' ').upper()}")
            
            # The Arduino needs time to talk to the battery (OneWire is slow)
            time.sleep(wait_time)
            
            if self.serial.in_waiting > 0:
                response = self.serial.read(self.serial.in_waiting)
                self.log(f"<< Received {len(response)} bytes: {response.hex(' ').upper()}")
                return response
            
            self.log("!! Device timed out (No response from battery/Arduino)")
            return None
        except Exception as e:
            self.log(f"Serial Error: {e}")
            return None
