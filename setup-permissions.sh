#!/bin/bash

echo "🔧 OBI-1 Linux Environment Setup (2026 Edition)"
echo "-----------------------------------------------"

# 1. Check and Install GNOME 45 Runtime
if ! flatpak list --runtime | grep -q "org.gnome.Platform/x86_64/45"; then
    echo "⚠️  Missing required runtime: GNOME 45"
    read -p "Would you like to install it now from Flathub? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        flatpak install flathub org.gnome.Platform//45 -y
    fi
else
    echo "✅ GNOME 45 Runtime is already installed."
fi

# 2. Hardware Permissions (Serial/USB)
echo "📦 Configuring hardware access..."

# Add user to common serial groups
sudo usermod -a -G dialout $USER
sudo usermod -a -G uucp $USER 2>/dev/null || true # For Arch-based users

# 3. Create Udev Rule
# This grants access to common Arduino/Serial chips (CH340, CP2102, FTDI)
RULE_PATH="/etc/udev/rules.d/99-obi-serial.rules"
echo "📝 Creating udev rules at $RULE_PATH"

echo 'KERNEL=="ttyUSB*", MODE="0666", GROUP="dialout"' | sudo tee $RULE_PATH
echo 'KERNEL=="ttyACM*", MODE="0666", GROUP="dialout"' | sudo tee -a $RULE_PATH

# 4. Refresh System
echo "🔄 Refreshing system rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "-----------------------------------------------"
echo "🎉 Setup Complete!"
echo "⚠️  IMPORTANT: You MUST log out and log back in (or reboot) for group changes to take effect."
