#!/bin/bash

# Define the rule file path
RULE_FILE="/etc/udev/rules.d/99-obi-serial.rules"

echo "--- OBI-1 Diagnostic Permission Setup ---"

# Create the rule for both common types of USB serial chips
# 0666 gives Read/Write access to Owner, Group, and Others
cat <<EOF | sudo tee $RULE_FILE
# Rule for OBI-1 Diagnostic: Allow user access to ttyUSB and ttyACM devices
KERNEL=="ttyUSB*", MODE="0666"
KERNEL=="ttyACM*", MODE="0666"
EOF

echo "Applying new rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Success! Please unplug and replug your battery interface."
