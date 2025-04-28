#!/bin/bash

# Proxmox Host Agent Installation Script

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Create installation directory
INSTALL_DIR="/opt/proxmox-agent"
mkdir -p $INSTALL_DIR

# Copy files
echo "Copying files to $INSTALL_DIR..."
cp -r * $INSTALL_DIR/

# Create .env file if it doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
  echo "Creating .env file..."
  cp .env.example $INSTALL_DIR/.env
  echo "Please edit $INSTALL_DIR/.env with your configuration"
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r $INSTALL_DIR/requirements.txt

# Install systemd service
echo "Installing systemd service..."
cp $INSTALL_DIR/proxmox-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable proxmox-agent

# Start service
echo "Starting service..."
systemctl start proxmox-agent

# Check status
echo "Checking service status..."
systemctl status proxmox-agent

echo "Installation complete!"
echo "The agent is now running and will synchronize VMs with AccountDB."
echo "You can check the logs with: journalctl -u proxmox-agent"
