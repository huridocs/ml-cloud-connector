#!/bin/bash
# setup_docker.sh

echo "Starting Docker and NVIDIA Container Toolkit installation..."

# 1. Install Docker
echo "Installing Docker..."

# Add Docker's official GPG key
sudo apt update
sudo apt install ca-certificates curl gnupg -y
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources
echo \
  "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  \"$(. /etc/os-release && echo \"$VERSION_CODENAME\")\" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker packages
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# Add current user to the 'docker' group
sudo usermod -aG docker "$USER"
echo "Docker installed. You will need to log out and back in for the 'docker' group changes to take effect."

# 2. Install NVIDIA Container Toolkit
echo "Installing NVIDIA Container Toolkit..."

# Configure the repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Update package lists and install the toolkit
sudo apt update
sudo apt install -y nvidia-container-toolkit

# Configure the Docker daemon to use the NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker service to apply changes
sudo systemctl restart docker

echo "======================================================================="
echo "Setup complete! Please log out and log back in (or start a new shell)."
echo "Then, verify your GPU setup with: docker run --rm --gpus all nvidia/cuda:latest nvidia-smi"
echo "======================================================================="