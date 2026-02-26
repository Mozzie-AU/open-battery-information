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
# Copyright (c) 2024 Martin Jansson (MIT License)

import time
import re

# --- OBI FIRMWARE BINARY COMMANDS ---
MODEL_CMD           = [0x01, 0x02, 0x10, 0xCC, 0xDC, 0x0C]
READ_DATA_REQUEST   = [0x01, 0x04, 0x1D, 0xCC, 0xD7, 0x00, 0x00, 0xFF]
TESTMODE_CMD        = [0x01, 0x03, 0x09, 0x33, 0xD9, 0x96, 0xA5]
RESET_ERROR_CMD     = [0x01, 0x02, 0x09, 0x33, 0xDA, 0x04]
LEDS_ON_CMD         = [0x01, 0x02, 0x09, 0x33, 0xDA, 0x31]
LEDS_OFF_CMD        = [0x01, 0x02, 0x09, 0x33, 0xDA, 0x34]

class MakitaModule:
    def __init__(self, interface):
        self.interface = interface

    def _sanitize(self, text):
        return re.sub(r'[^\x20-\x7E]', '', text)

    def read_static_info(self):
        raw_data = self.interface.request(MODEL_CMD, expected_len=16)
        if not raw_data: return {"Model": "No Data", "ROM ID": "---"}
        
        rom_id_hex = raw_data.hex(' ').upper()[:23]
        decoded = raw_data.decode('ascii', errors='ignore')
        
        # Regex for Makita model numbers
        model_match = re.search(r'(BL\d{4}[A-Z]?)', decoded)
        model_name = model_match.group(1) if model_match else "BL1860B (Auto-ID)"

        return {
            "Model": model_name,
            "ROM ID": rom_id_hex
        }

    def read_live_data(self):
        raw_data = self.interface.request(READ_DATA_REQUEST, expected_len=31)
        return self._parse_live(raw_data)

    def set_leds(self, turn_on=True):
        if self.interface.send_command(TESTMODE_CMD):
            time.sleep(0.3)
            return self.interface.send_command(LEDS_ON_CMD if turn_on else LEDS_OFF_CMD)
        return False

    def clear_battery_errors(self):
        self.interface.log(">> Handshake: Sending TESTMODE...")
        if self.interface.send_command(TESTMODE_CMD):
            time.sleep(0.4)
            self.interface.log(">> Handshake: Sending RESET_ERROR...")
            result = self.interface.send_command(RESET_ERROR_CMD)
            time.sleep(1.2) # BMS Reboot cooldown
            return result
        return False

    def _parse_live(self, data):
        res = {}
        if not data: return {"State": "No Response"}
        
        if len(data) < 28:
            return {"State": "Initializing Bus..."}
        
        try:
            # Heartbeat jitter masking
            state_byte = data[2]
            if 0xD0 <= state_byte <= 0xDF:
                res["State"] = "UNLOCKED / OK"
            elif state_byte == 0x00:
                res["State"] = "STANDBY"
            else:
                res["State"] = f"STATUS: {hex(state_byte)}"

            # Little Endian Voltages
            v1 = (data[4] | (data[5] << 8)) / 1000
            v2 = (data[6] | (data[7] << 8)) / 1000
            v3 = (data[8] | (data[9] << 8)) / 1000
            v4 = (data[10] | (data[11] << 8)) / 1000
            v5 = (data[12] | (data[13] << 8)) / 1000

            res["Cell 1"] = f"{v1:.3f}V"
            res["Cell 2"] = f"{v2:.3f}V"
            res["Cell 3"] = f"{v3:.3f}V"
            res["Cell 4"] = f"{v4:.3f}V"
            res["Cell 5"] = f"{v5:.3f}V"
            res["Pack Voltage"] = f"{(v1+v2+v3+v4+v5):.2f}V"

            res["Temp Cell"] = f"{data[26]}°C"
            res["Charge count"] = str(data[24])

        except Exception:
            res["State"] = "Mapping Error"
            
        return res
