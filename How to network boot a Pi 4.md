# How to network boot a Pi 4

## Prepare the client board

```
sudo apt update
```
### To find the Ethernet MAC address:

```
ethtool -P eth0
```
e.g. dc:a6:32:03:22:20

### To find the serial number:

```
grep Serial /proc/cpuinfo | cut -d ' ' -f 2 | cut -c 8-16
```
e.g. 047b45dcb

```
sudo raspi-config
```

### Set the boot order
Within raspi-config, choose Advanced Options, then Boot Order, then Network Boot. You must then reboot the device for the change to the boot order to be programmed into the bootloader EEPROM. 

**YOU NEED TO REBOOT BACK INTO RASPBERRY PI OS! DON'T JUST SHUTDOWN**

Once the Pi has rebooted, check that the boot order is now 0xf21:

```
vcgencmd bootloader_config
```

i.e. try SD first, followed by NETWORK then repeat

### Optionally check the PXE boot messages.

On a different Pi, on the same network:
```
sudo tcpdump -i eth0 port bootpc | grep dc:a6
```

## Prepare the server board
You server needs to have a fixed IP address.

*Note: The offical way to do this is using systemd and to create two files 10-eth0.netdev and a 11-eth0.network.
Using this method didn't work as expecgted for me and the PXE boot messages where not getting to Dnsmasq.
Some more debugging is needed. So instead I use the old method of /etc/network/interfaces*

```
cat << EOF | sudo tee /etc/network/interfaces
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
        address 192.168.1.45
        netmask 255.255.255.0
        gateway 192.168.1.1

source /etc/network/interfaces.d/*
EOF
```

Change `192.168.1.45` etc to fit your network setup.

## Other resources

My shell scripts to automate some of this process:

Other articles that could be useful

