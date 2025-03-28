#!/bin/bash
# Initial iptables setup for SOCKS proxy

# Exit on error
set -e

echo "Setting up initial iptables rules..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Clear existing rules for INPUT chain
echo "Clearing existing INPUT chain rules..."
iptables -F INPUT

# Allow established connections
echo "Adding basic rules..."
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow local loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow SSH (port 22) to prevent lockout
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Block all other incoming connections to the proxy port
echo "Adding proxy-specific rules..."
iptables -A INPUT -p tcp --dport 1080 -j DROP
iptables -A INPUT -p udp --dport 1080 -j DROP

# Save the rules
echo "Saving rules..."
netfilter-persistent save

echo "iptables setup complete!"
echo "Now you can use the Telegram bot to add specific IPs to the whitelist."