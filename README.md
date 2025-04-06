# SOCKS Proxy Manager with Timer Bot

A Telegram-based management solution for controlling access to a SOCKS proxy server running on your VPS. The project now includes two specialized bots:
1. **IP Whitelist Bot**: Control access using IP-based whitelisting
2. **Timer Bot**: Enable/disable the proxy for specific time periods

This solution is perfect for scenarios where client applications don't support proxy authentication or when you need fine-grained access control to your proxy.

## 🔍 Project Overview

This project provides a complete solution for running a secure SOCKS proxy on your VPS with both IP-based access control and time-based activation/deactivation. Instead of using username/password authentication (which some clients don't support), it uses iptables to control access. Management is handled through convenient Telegram bot interfaces.

### Key Benefits:

- **Client Compatibility**: Works with applications that don't support proxy authentication
- **Dual Control Methods**: Control by IP whitelist or by timed access periods
- **Fine-grained Access Control**: Easily grant or revoke access for specific IP addresses
- **Time-Based Control**: Set automatic timers to enable and disable proxy access
- **Remote Management**: Control your proxy from anywhere using Telegram
- **Security**: Only authorized users can manage the proxy
- **Convenience**: User-friendly interfaces with buttons instead of commands
- **Reliability**: Runs as system services with automatic restarts

## 📋 Features

### IP Whitelist Bot
- 🔒 Secure IP-based access control via iptables
- 🤖 Telegram bot with intuitive button interface
- 🔘 Easy IP address management (add/remove)
- 📊 Status monitoring and service control
- 📜 Log viewing

### Timer Bot
- ⏱️ Enable the proxy for preset time periods (1h, 3h, 6h)
- 🕒 Automatic shutdown when timer expires
- 🔄 Status updates with remaining time
- 🔓 Quick enable/disable functionality

### Shared Features
- 🛡️ Robust firewall management with iptables
- 🔄 Automatic service recovery with supervisor
- 📝 Comprehensive logging

## 🖥️ VPS Requirements

This solution is designed to run on a VPS (Virtual Private Server) with:

- Ubuntu/Debian-based system
- Root or sudo access
- Python 3.7+
- Dante SOCKS proxy server installed
- iptables for firewall rules

The bots can be easily deployed on low-cost VPS solutions from providers like DigitalOcean, Linode, Vultr, or AWS.

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

3. Configure your bot tokens and authorized user IDs:
   - Edit `socks_bot.py` for the IP whitelist bot
   - Edit `socks_timer_bot.py` for the timer-based access bot

4. Run the setup script:
   ```bash
   sudo ./setup.sh
   ```

5. Set up initial iptables rules:
   ```bash
   sudo ./iptables_setup.sh
   ```

6. Configure supervisor to keep both bots running:
   ```bash
   sudo cp socks_bot.conf socks_timer_bot.conf /etc/supervisor/conf.d/
   sudo supervisorctl update
   ```

## 🚀 Usage Scenarios

### For Developers
- Access development environments through a secure proxy
- Test geolocation-specific features from your VPS's location
- Connect to services that require a fixed IP
- Enable the proxy only when needed with auto-shutdown timers

### For Teams
- Provide secure proxy access to team members
- Easily add/remove access when team composition changes
- Avoid sharing proxy credentials between team members
- Set up temporary access for contractors with automatic expiration

### For Privacy-conscious Users
- Route traffic through your own controlled proxy
- Avoid exposure of credentials through insecure proxy authentication
- Create separate access for different devices with unique IPs
- Enable the proxy only when needed to reduce exposure

## 🤖 Bot Commands and Functions

### IP Whitelist Bot
- **📊 Status**: Check if your proxy is running
- **📋 IP Rules**: View the current whitelist
- **➕ Add IP**: Grant access to a new IP address
- **➖ Remove IP**: Revoke access for an IP address
- **🔄 Restart Proxy**: Restart the proxy service
- **📜 Logs**: View recent logs

### Timer Bot
- **🔓 Enable Proxy**: Turn on proxy access indefinitely
- **⏱️ Enable for 1h/3h/6h**: Enable the proxy with automatic shutdown
- **🔒 Disable Proxy**: Turn off proxy access immediately
- **⏱️ Set Timer**: Set a shutdown timer while keeping proxy enabled
- **🔄 Refresh Status**: Check current status and remaining time

## 🔧 Technical Implementation

- **Dante SOCKS Proxy**: Provides the actual SOCKS4/5 proxy functionality
- **iptables**: Handles IP filtering at the firewall level
- **python-telegram-bot**: Powers the Telegram bot interfaces
- **Supervisor**: Ensures the bots stay running
- **Threading**: Manages timers for automatic proxy shutdown

## 📝 Notes on Security

- The proxy itself accepts all connections at the application level
- IP filtering is handled at the firewall level using iptables
- Only whitelisted IPs can reach the proxy port when using IP whitelisting
- The Telegram bots only accept commands from authorized user IDs
- The timer bot provides an additional layer of security by limiting exposure time

## 🛠️ Troubleshooting

If clients can't connect:
1. Verify the client IP is correctly added to the whitelist (if using IP whitelist)
2. Check if the proxy service is running
3. Verify that the firewall is properly configured (run `sudo bash firewall.sh status`)
4. Make sure the client is configured to use SOCKS4 or SOCKS5
5. Confirm there are no other firewall rules blocking the connection

## 📄 License

MIT