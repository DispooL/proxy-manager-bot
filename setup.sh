#!/bin/bash
# Setup script for SOCKS Proxy Manager Bot

# Exit on error
set -e

echo "Setting up SOCKS Proxy Manager Bot..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Install required packages if not present
echo "Installing dependencies..."
apt update
apt install -y supervisor python3-pip iptables-persistent

# Create log files
echo "Creating log files..."
touch /var/log/socks_bot.log
touch /var/log/socks_bot_stdout.log
chmod 666 /var/log/socks_bot.log
chmod 666 /var/log/socks_bot_stdout.log

# Copy the script to final location
echo "Installing bot script..."
chmod +x socks_bot.py

# Setup supervisor
echo "Setting up supervisor..."
cp socks_proxy_bot.conf /etc/supervisor/conf.d/

# Reload supervisor
echo "Starting bot service..."
supervisorctl reread
supervisorctl update
supervisorctl start socks_proxy_bot

echo "Setup complete! The bot should now be running."
echo "You can check the status with: supervisorctl status socks_proxy_bot"
echo "View logs with: tail -f /var/log/socks_bot.log"