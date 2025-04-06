#!/bin/bash
# Script to enable or disable SOCKS proxy access through iptables
# Exit on error
set -e
# Port for SOCKS proxy
SOCKS_PORT=1

# Function to enable SOCKS proxy (open port)
enable_socks() {
    echo "Opening SOCKS proxy port ${SOCKS_PORT} to all..."
    # First remove any existing DROP or REJECT rules for this port
    sudo iptables -D INPUT -p tcp --dport ${SOCKS_PORT} -j DROP 2>/dev/null || true
    sudo iptables -D INPUT -p tcp --dport ${SOCKS_PORT} -j REJECT 2>/dev/null || true
    # Add ACCEPT rule
    sudo iptables -I INPUT -p tcp --dport ${SOCKS_PORT} -j ACCEPT
    sudo netfilter-persistent save
    echo "SOCKS proxy is now accessible!"
}

# Function to disable SOCKS proxy (close port)
disable_socks() {
    echo "Closing SOCKS proxy port ${SOCKS_PORT}..."

    # Get the line number of the rule that matches our port
    LINE=$(sudo iptables -L INPUT -n --line-numbers | grep "dpt:${SOCKS_PORT}" | awk '{print $1}')

    # If we found a matching rule, delete it by line number
    if [ -n "$LINE" ]; then
        sudo iptables -D INPUT $LINE
        echo "Rule deleted successfully!"
    else
        echo "No matching rule found for port ${SOCKS_PORT}"
    fi

    # Add a DROP rule to block the port completely
    sudo iptables -I INPUT -p tcp --dport ${SOCKS_PORT} -j DROP

    sudo netfilter-persistent save
    echo "SOCKS proxy is now blocked!"
}

# Check command line argument
case "$1" in
    enable)
        enable_socks
        ;;
    disable)
        disable_socks
        ;;
    status)
        if sudo iptables -C INPUT -p tcp --dport ${SOCKS_PORT} -j ACCEPT 2>/dev/null; then
            echo "SOCKS proxy is currently ENABLED"
        else
            if sudo iptables -C INPUT -p tcp --dport ${SOCKS_PORT} -j DROP 2>/dev/null ||
               sudo iptables -C INPUT -p tcp --dport ${SOCKS_PORT} -j REJECT 2>/dev/null; then
                echo "SOCKS proxy is currently DISABLED (explicitly blocked)"
            else
                echo "SOCKS proxy is currently DISABLED"
            fi
        fi
        ;;
    *)
        echo "Usage: $0 {enable|disable|status}"
        exit 1
        ;;
esac
exit 0