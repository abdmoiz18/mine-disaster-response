#!/bin/bash
# save as: setup_hotspot.sh
# chmod +x setup_hotspot.sh
# sudo ./setup_hotspot.sh

# Variables
INTERFACE="wlan1"  # Your Archer interface
SSID="MineNav_Demo"
PASSWORD="SecureDemo123"
CHANNEL="36"  # 5GHz channel
IP_RANGE="192.168.10"

echo "=== Setting up MineNav Super Hotspot ==="

# 1. Stop conflicting services
sudo systemctl stop hostapd dnsmasq
sudo systemctl disable hostapd dnsmasq

# 2. Configure static IP
sudo tee -a /etc/dhcpcd.conf <<EOF

# MineNav Hotspot Configuration
interface $INTERFACE
    static ip_address=${IP_RANGE}. 1/24
    nohook wpa_supplicant
EOF

# 3. Create hostapd config with ESP32 optimization
sudo tee /etc/hostapd/hostapd.conf <<EOF
interface=$INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=a
channel=$CHANNEL
ieee80211n=1
ieee80211ac=1
wmm_enabled=1
auth_algs=1
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
require_ht=0
require_vht=0
country_code=US
EOF

# 4. Configure dnsmasq for ESP32-friendly DHCP
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null
sudo tee /etc/dnsmasq.conf <<EOF
interface=$INTERFACE
dhcp-range=${IP_RANGE}. 10,${IP_RANGE}.200,255.255.255.0,24h
dhcp-option=3,${IP_RANGE}. 1
dhcp-option=6,${IP_RANGE}.1
dhcp-option-force=51,86400
log-dhcp
EOF

# 5. Enable packet forwarding
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# 6. Configure services
sudo sed -i 's|^#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "=== Configuration Complete ==="
echo "Hotspot SSID: $SSID"
echo "Password: $PASSWORD"
echo "IP Range: ${IP_RANGE}. 1/24"
echo ""
echo "Rebooting in 5 seconds...  (Ctrl+C to cancel)"
sleep 5
sudo reboot
