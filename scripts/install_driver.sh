#!/bin/bash
# install_driver.sh

echo "Starting NVIDIA driver installation..."

# Update package lists
sudo apt update

# Install the recommended NVIDIA driver for the V100
sudo ubuntu-drivers autoinstall

# Check for installation success (optional but recommended)
if [ $? -eq 0 ]; then
    echo "NVIDIA driver installed successfully. REBOOT IS REQUIRED."
    echo "The system will now reboot in 10 seconds. After rebooting, run 'setup_docker.sh'."
    sleep 10
    sudo reboot
else
    echo "Driver installation failed. Please check the logs."
fi