OBI-1 Diagnostic (Flatpak Edition)

OBI-1 is an advanced, Linux-optimized diagnostic tool for lithium-ion battery packs, primarily targeting Makita LXT systems. This version is an evolution of the original project, rebuilt for 2026 Linux environments with enhanced safety monitoring.

<img src="OpenBatteryInformation/docs/images/OBI-Screenshot.png" width="50%" alt="OBI-1 Diagnostic Interface">
⚖️ License & Acknowledgments

    Current License: This software is licensed under the GNU GPLv3.

    Origin: This project is a specialized fork of Open Battery Information by Martin Jansson.

    Compliance: We retain the original MIT license notice for the foundation code while applying GPLv3 protections to all new modifications and the combined work.

🛠 Enhancements in this Fork

Unlike the original Python script approach, this version introduces:

    Revised UI: A complete rewrite using GTK4 and Libadwaita for a native GNOME/Linux look, featuring a centered HeaderBar with integrated window controls.

    Automated Permissions: A custom setup-permissions.sh script to handle serial port access without manual user group management.

    Flatpak Distribution: Fully sandboxed packaging for security and cross-distribution compatibility.

    Visual Safety Alerts: Real-time color coding for low-voltage cells (<2.5V) and high-temperature warnings (≥60°C).

🚀 Installation (Linux)
1. Install Prerequisites

To run on Ubuntu or non-GNOME systems, you must ensure the GNOME 45 Runtime is installed:
Bash

flatpak install flathub org.gnome.Platform//45

2. Configure Hardware Access

By default, Linux restricts access to the serial ports used by your Arduino interface. Run the included setup script to apply the necessary udev rules:
Bash

chmod +x setup-permissions.sh
./setup-permissions.sh

Note: You must log out and log back in for group changes to take effect. You may also need to unplug and replug your USB adapter.
3. Install the App

Download the org.obi.diagnostic.flatpak file from the Releases section and run:
Bash

flatpak install --user org.obi.diagnostic.flatpak

4. Launch

Find OBI-1 Diagnostic in your application menu or launch via terminal:
Bash

flatpak run org.obi.diagnostic

💻 Development & Building

To modify the source or build the package manually, ensure you have flatpak-builder installed.

    Build and Install Locally:

Bash

flatpak-builder --user --install --force-clean build-dir org.obi.diagnostic.json

    Create a Redistributable Bundle:

Bash

flatpak-builder --repo=repo --force-clean build-dir org.obi.diagnostic.json
flatpak build-bundle ./repo org.obi.diagnostic.flatpak org.obi.diagnostic

🤝 Support & Contributions

This project aims to aid in battery repair and reduce waste by identifying false BMS triggers.

    For questions regarding the original logic, visit the original repository.

    To support the original author, consider Buying them a coffee.
