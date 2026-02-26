#!/bin/bash

echo "🔧 Setting up permissions for OBI-1 Diagnostic Tool..."

# 1. Add user to dialout group
sudo usermod -a -G dialout $USER

# 2. Create a udev rule for common USB-Serial adapters (CH340/CP2102)
# This ensures the device is readable without needing a reboot sometimes
echo 'KERNEL=="ttyUSB*", MODE="0666", GROUP="dialout"' | sudo tee /etc/udev/rules.d/99-obi-serial.rules

# 3. Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "✅ Done! PLEASE LOG OUT AND LOG BACK IN for group changes to take effect."
