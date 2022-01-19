# Turn your Raspberry Pi into a Wi-Fi network extender/booster/repeater

## Use desktop to configure wlan0

### Connect to your existing Wi-Fi network:

- Left click on Wi-Fi icon in taskbar
- wlan0
- Click on your Wi-Fi network
- Enter the password

### Optionally set a static address (not mandatory):
- Right click on Wi-Fi icon in taskbar
- Wireless & Wired Network Settings
- Select wlan0 from drop-down
- Enter IPv4 address: 192.168.1.111
Note: You can pick whatever address is valid in your network. Beware of using an address in the existing DHCP pool range

Reboot and test that you have connectivity over the Wi-Fi. Make sure you don't have an Ethernet cable plugged in!!!

## Use command line to setup the rest

### Install all the software you need

```
sudo apt update
```
Install the host access point server that lets the Pi act as an access point:
```
sudo apt install hostapd
```

Automatically start the hostapd service when your Raspberry Pi boots:
```
sudo systemctl unmask hostapd
```
```
sudo systemctl enable hostapd
```
Install the dnsmasq software to provide network management services (DNS, DHCP)  to wireless clients
```
sudo apt install dnsmasq
```
Install netfilter-persistent and iptables-persistent so you can save the firewall rules and restoring them when the Raspberry Pi boots:
```
sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent
```

### Setup DHCP for wlan1

```
sudo nano /etc/dhcpcd.conf
```
Go to the end of the file and add the following:
```
interface wlan1
static ip_address=192.168.4.1/24
nohook wpa_supplicant
```

If you set a static IP address for wlan0 then change this line (if you see it):
```
inform 192.168.1.111
```
to
```
static ip_address=192.168.1.111/24
```
Save and exit from nano (CTRL-X).

### Enable Routing and IP Masquerading

Create a new file:
```
sudo nano /etc/sysctl.d/routed-ap.conf
```
File contents:
```
# Enable IPv4 routing
net.ipv4.ip_forward=1
```
Now run these two commands to add a firewall rule and save it.
```
sudo iptables -t nat -A POSTROUTING -o wlan1 -j MASQUERADE
sudo netfilter-persistent save
```

### Time to configure the DHCP and DNS for wlan1
Rename the default configuration file and edit a new one:
```
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```
Add the following lines to the new `dnsmasq.conf` file:
```
interface=wlan1
dhcp-range=192.168.4.100,192.168.4.200,255.255.255.0,24h
domain=wlan
address=/gw.wlan/192.168.4.1
```
Note: Your Raspberry Pi will issue IP addresses between 192.168.4.100 and 192.168.4.200, with a lease time of 24 hours.
You should be able to reach the Raspberry Pi under the name `gw.wlan`

Note 2: To see clients connected to _wlan1_ use `cat /var/lib/misc/dnsmasq.leases`

The output will be something like
```
574256399 00:10:a7:0c:a2:c1 192.168.4.100 OnePlus-6 01:00:10:b7:1c:a2:c1
```

### Configure the Access Point server
```
sudo nano /etc/hostapd/hostapd.conf
```
Add the following:
```
country_code=GB
interface=wlan1
ssid=NameOfNetwork_EXT
hw_mode=g
channel=7
wpa_passphrase=YourSecretPassword
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```
Note: Change `country_code=GB` to the two-letter ISO code of your country.

Note: If your Wi-Fi dongle supports 5GHz, you can change the operations mode from `hw_mode=g` to `hw_mode=a`.

Now reboot!
