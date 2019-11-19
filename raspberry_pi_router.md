## Assumption
You have Raspian installed on your Pi and that you can connect to it over Ethernet from your primary LAN (_eth0_).

## Install dnsmasq
From the command line, run `sudo apt install dnsmasq` to install dnsmasq

Stop it, for now with `sudo systemctl stop dnsmasq`

## Static IP for eth1
Now set a static IP address for the second ethernet connection (eth1). Edit /etc/dhcpcd.conf with `sudo nano /etc/dhcpcd.conf`. Go to the end of the file and edit it so that it looks like the following:
```
interface eth1
    static ip_address=192.168.7.1/24
```

## Configure dnsmasq
Discard the old conf file and create a new configuration:
```
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```
Add these lines:
```
interface=eth1
dhcp-range=192.168.7.100,192.168.7.120,255.255.255.0,24h
```
This will define a new DHCP range 192.168.7.x which will be adminsitered by the Pi via _eth1_.

Now start dnsmasq with `sudo systemctl start dnsmasq`

### Note
To see clients connected to eth1 use `cat /var/lib/misc/dnsmasq.leases`

The output will be something like
```
574256399 00:10:a7:0c:a2:c1 192.168.7.109 rpi3a 01:00:10:a7:0c:a2:c1
```

## IP forwarding
Edit /etc/sysctl.conf and add line (for persistence)

`sudo nano /etc/sysctl.conf`
```
net.ipv4.ip_forward=1
```
Activate forwarding now with `sudo sysctl -w net.ipv4.ip_forward=1`

Add a masquerade for outbound traffic on eth0

```
sudo iptables -t nat -A  POSTROUTING -o eth0 -j MASQUERADE
```

Save the iptables rule.

```
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
```
Edit /etc/rc.local with `sudo nano /etc/rc.local` and add this just above "exit 0" to install these rules on boot.

```
iptables-restore < /etc/iptables.ipv4.nat
```

---
Now the router is working. Connect a wired device to the _eth1_ network. From that device you will have access to the network attached to _eth0_ and _eth1_ and if _eth0_'s network has Internet, you will get Internet access as well.

Now add a third network over Wi-Fi!

----------------
## Static IP for wlan0
Now set a static IP address for the Wi-Fi (wlan0). Edit /etc/dhcpcd.conf with `sudo nano /etc/dhcpcd.conf`. Go to the end of the file and add these lines:
```
interface wlan0
    static ip_address=192.168.17.1/24
    nohook wpa_supplicant
```

This will give it a static address of _192.168.17.1_

# hostapd

```
sudo apt install hostapd
sudo systemctl stop hostapd
```
Edit the configuration file `sudo nano /etc/dhcpcd.conf`. Go to the end of the file and edit it so that it looks like the following:

```
interface wlan0
    static ip_address=192.168.17.1/24
    nohook wpa_supplicant
```
The Wi-Fi network will be 192.168.17.x

Now restart the DHCP server with `sudo service dhcpcd restart`

Edit the dnsmasq.conf file with `sudo nano /etc/dnsmasq.conf` and add

```
interface=wlan0
dhcp-range=192.168.17.100,192.168.17.120,255.255.255.0,24h
```

Reload the configuration file with `sudo systemctl reload dnsmasq`

## hostapd
To use the 5 GHz band, you can change the operations mode from hw_mode=g to hw_mode=a. Possible values for hw_mode are:

a = IEEE 802.11a (5 GHz)
b = IEEE 802.11b (2.4 GHz)
g = IEEE 802.11g (2.4 GHz)

Edit `sudo nano /etc/hostapd/hostapd.conf` and add these line:
```
interface=wlan0
driver=nl80211
ssid=PiNet
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=raspberry
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

_PiNet_ will be the network SSID and the password will be _raspberry_. Change accordingly.

We now need to tell the system where to find this configuration file.

Edit this file `sudo nano /etc/default/hostapd` and find the line with #DAEMON_CONF, and replace it with this:

```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```
Now enable and start hostapd:
```
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
```

You will now have a PiNet Wi-Fi network which has access to the network on _eth0_
