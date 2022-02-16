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
e.g. 037b65dae

You can also find the serial number on the boot screen. Boot the Pi without a micro SD card to see the boot screen and the information.
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

### Install the packages needed
```
sudo apt update
sudo apt install -y nfs-kernel-server dnsmasq unzip nmap kpartx rsync
```
### Your server needs to have a fixed IP address.

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

### Create the root file system that will be served over NFS

The client Raspberry Pi will need a root file system to boot from: we will use a copy of the server’s root filesystem and place it in /nfs/<SERIAL> where <SERIAL> is the board's serial number without the leading zeros, e.g. 37b65dae

```
SERIALNUM="37b65dae"
sudo mkdir -p /nfs/$SERIALNUM
sudo rsync -xa --progress --exclude /nfs / /nfs/$SERIALNUM
```

Delete SSH keys and enable the ssh server
 
```
SERIALNUM="37b65dae"
cd /nfs/$SERIALNUM
sudo mount --bind /dev dev
sudo mount --bind /sys sys
sudo mount --bind /proc proc
sudo chroot . rm -f /etc/ssh/ssh_host_*
sudo chroot . dpkg-reconfigure openssh-server
sudo chroot . systemctl enable ssh
sleep 1
sudo umount dev sys proc
sudo touch boot/ssh
```
Configure /etc/fstab for the client
```
SERIALNUM="37b65dae"
echo | sudo tee /nfs/$SERIALNUM/etc/fstab
echo "proc /proc proc defaults 0 0" | sudo tee -a /nfs/$SERIALNUM/etc/fstab
echo "192.168.1.45:/tftpboot /boot nfs defaults,vers=4.1,proto=tcp 0 0" | sudo tee -a /nfs/$SERIALNUM/etc/fstab
```
**You MUST change the serial number to that of your board, and use the correct IP address of the server (e.g. 192.168.1.45)**
        
Export the root file system created earlier, and the TFTP boot folder.

```
SERIALNUM="37b65dae"      
echo "/nfs/$SERIALNUM *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
echo "/tftpboot *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
```
**You MUST change the serial number to that of your board**
        
## TFTP
```
SERIALNUM="37b65dae"
sudo mkdir -p /tftpboot/$SERIALNUM
sudo chmod 777 /tftpboot
sudo cp -r /boot/* /tftpboot/$SERIALNUM
sudo cp /boot/bootcode.bin /tftpboot/
```
Write dnsmasq.conf
```
cat << EOF | sudo tee /etc/dnsmasq.conf
port=0
dhcp-range=$BRD,proxy
bind-interfaces
log-dhcp
enable-tftp
log-facility=/var/log/dnsmasq
tftp-root=/tftpboot
pxe-service=0,"Raspberry Pi Boot"
EOF
```        

Configure cmdline.txt
```
SERIALNUM="37b65dae"
echo "console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.1.45:/nfs/$SERIALNUM,vers=4.1,proto=tcp rw ip=dhcp rootwait" | sudo tee /tftpboot/$SERIALNUM/cmdline.txt
sudo chmod 777 /tftpboot/base/cmdline.txt
```
**You MUST change the serial number to that of your board, and use the correct IP address of the server (e.g. 192.168.1.45)**
        
### Restart all the services
```
sudo systemctl enable dnsmasq
sudo systemctl restart dnsmasq
sudo systemctl enable rpcbind
sudo systemctl restart rpcbind
sudo systemctl enable nfs-kernel-server
sudo systemctl restart nfs-kernel-server
```
        
## Other resources

My shell scripts to automate some of this process:

Other articles that could be useful
- https://www.raspberrypi.com/documentation/computers/remote-access.html#network-boot-your-raspberry-pi
- https://linuxhit.com/raspberry-pi-pxe-boot-netbooting-a-pi-4-without-an-sd-card/
- https://williamlam.com/2020/07/two-methods-to-network-boot-raspberry-pi-4.html
- https://hackaday.com/2019/11/11/network-booting-the-pi-4/
- https://codestrian.com/index.php/2020/02/14/setting-up-a-pi-cluster-with-netboot/
- https://linuxhit.com/raspberry-pi-pxe-boot-netbooting-a-pi-4-without-an-sd-card/
