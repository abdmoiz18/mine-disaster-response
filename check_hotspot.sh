#!/bin/bash
# save as: check_hotspot.sh

echo "=== MineNav Hotspot Status Check ==="
echo ""

# 1. Check interface
echo "1. Network Interfaces:"
iwconfig | grep -A1 "wlan"
echo ""

# 2. Check hostapd status
echo "2. Hotspot Service:"
sudo systemctl status hostapd --no-pager -l | head -20
echo ""

# 3. Check connected clients
echo "3. Connected Devices:"
sudo arp -a | grep wlan1 || echo "No clients yet"
echo ""

# 4. Check DHCP leases
echo "4. DHCP Leases:"
if [ -f /var/lib/misc/dnsmasq. leases ]; then
    cat /var/lib/misc/dnsmasq. leases
else
    echo "No leases yet"
fi
echo ""

# 5. Signal strength
echo "5. Signal Info:"
sudo iw dev wlan1 info
echo ""
