# SOCKS Proxy Manager Bot

A Telegram-based management tool for controlling access to a SOCKS proxy server running on your VPS using IP whitelisting. This solution is perfect for scenarios where client applications don't support proxy authentication or when you need fine-grained access control to your proxy.

## 🔍 Project Overview

This project provides a complete solution for running a secure SOCKS proxy on your VPS with IP-based access control. Instead of using username/password authentication (which some clients don't support), it uses iptables to restrict access to specific IP addresses. The management is handled through a convenient Telegram bot interface.

### Key Benefits:

- **Client Compatibility**: Works with applications that don't support proxy authentication
- **Fine-grained Access Control**: Easily grant or revoke access for specific IP addresses
- **Remote Management**: Control your proxy from anywhere using Telegram
- **Security**: Only authorized users can manage the proxy; only whitelisted IPs can connect
- **Convenience**: User-friendly interface with buttons instead of commands
- **Reliability**: Runs as a system service with automatic restarts

## 📋 Features

- 🔒 Secure IP-based access control via iptables
- 🤖 Telegram bot with intuitive button interface
- 🔘 Easy IP address management (add/remove)
- 📊 Status monitoring and service control
- 📜 Log viewing
- 🔄 Automatic service recovery with supervisor

## 🖥️ VPS Requirements

This solution is designed to run on a VPS (Virtual Private Server) with:

- Ubuntu/Debian-based system
- Root or sudo access
- Python 3.7+
- Dante SOCKS proxy server installed
- iptables for firewall rules

The bot can be easily deployed on low-cost VPS solutions from providers like DigitalOcean, Linode, Vultr, or AWS.

## 📦 Installation

1. Clone this repository to your VPS:
   ```bash
   git clone https://github.com/yourusername/socks-proxy-manager.git
   cd socks-proxy-manager
   ```

2. Install required packages:
   ```bash
   pip install python-telegram-bot --upgrade
   ```

3. Configure your bot token and authorized user ID in `socks_bot.py`

4. Run the setup script:
   ```bash
   sudo ./setup.sh
   ```

5. Set up initial iptables rules:
   ```bash
   sudo ./iptables_setup.sh
   ```

## 🚀 Usage Scenarios

### For Developers
- Access development environments through a secure proxy
- Test geolocation-specific features from your VPS's location
- Connect to services that require a fixed IP

### For Teams
- Provide secure proxy access to team members
- Easily add/remove access when team composition changes
- Avoid sharing proxy credentials between team members

### For Privacy-conscious Users
- Route traffic through your own controlled proxy
- Avoid exposure of credentials through insecure proxy authentication
- Create separate access for different devices with unique IPs

## 🤖 Bot Commands

The bot uses an intuitive button interface with the following functions:

- **📊 Status**: Check if your proxy is running
- **📋 IP Rules**: View the current whitelist
- **➕ Add IP**: Grant access to a new IP address
- **➖ Remove IP**: Revoke access for an IP address
- **🔄 Restart Proxy**: Restart the proxy service
- **📜 Logs**: View recent logs

## 🔧 Technical Implementation

- **Dante SOCKS Proxy**: Provides the actual SOCKS4/5 proxy functionality
- **iptables**: Handles IP filtering at the firewall level
- **python-telegram-bot**: Powers the Telegram bot interface
- **Supervisor**: Ensures the bot stays running

## 📝 Notes on Security

- The proxy itself accepts all connections at the application level
- IP filtering is handled at the firewall level using iptables
- Only whitelisted IPs can reach the proxy port
- The Telegram bot only accepts commands from authorized user IDs

## 🛠️ Troubleshooting

If clients can't connect:
1. Verify the client IP is correctly added to the whitelist
2. Check if the proxy service is running
3. Make sure the client is configured to use SOCKS4 or SOCKS5
4. Confirm there are no other firewall rules blocking the connection

## 📄 License

MIT