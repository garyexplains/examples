#!/bin/bash

# Copyright (c) 2022 Gary Sims. All rights reserved.

# THIS SOFTWARE IS PROVIDED ``AS IS″ AND WITHOUT ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE.   

# This was tested on a Raspberry Pi 4 running Raspberry Pi OS Lite for ARM64,
# based on Debian version 11 (bullseye).

set -e

sudo apt update
sudo apt install -y nfs-kernel-server dnsmasq unzip nmap kpartx rsync

# Get network info
GATEWAY="192.168.1.1"
NAMESERVER=$GATEWAY
IP="192.168.1.45"
IP_AND_NET="192.168.1.45/24"
BRD="192.168.1.255"
NETMASK="255.255.255.0"

echo "Setting static IP using above information"

cat << EOF | sudo tee /etc/network/interfaces
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
        address $IP
        netmask $NETMASK
        gateway $GATEWAY

source /etc/network/interfaces.d/*
EOF

sudo mkdir -p /tftpboot/base
sudo chmod 777 /tftpboot
sudo cp -r /boot/* /tftpboot/base
sudo cp /boot/bootcode.bin /tftpboot/

echo "Writing dnsmasq.conf"
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

#echo "Create a 10-eth0.netdev and a 11-eth0.network"
#
#cat << EOF | sudo tee /etc/systemd/network/10-eth0.netdev
#[Match]
#Name=eth0
#
#[Network]
#DHCP=no
#EOF
#
#cat << EOF | sudo tee /etc/systemd/network/11-eth0.network
#[Match]
#Name=eth0
#
#[Network]
#Address=$IP_AND_NET
#DNS=$NAMESERVER
#
#[Route]
#Gateway=$GATEWAY
#EOF


#sudo systemctl enable systemd-networkd
#echo "Please reboot!"

sudo mkdir -p /nfs/bases/basefs
cd /nfs/bases

#echo "Getting latest Raspberry Pi OS lite image to use as NFS root"
#sudo wget -O raspios_latest.zip https://downloads.raspberrypi.org/raspios_lite_arm64_latest
#sudo unzip -o raspios_latest.zip
#sudo rm raspios_latest.zip

echo "Extracting image"
mkdir -p /tmp/img
IMGFN=`sudo find /nfs/bases/ -name "*arm64-lite.img" -printf "%f"`
sudo kpartx -a -v $IMGFN
sleep 1
sudo mount /dev/mapper/loop0p2 /tmp/img
sudo rsync -xa /tmp/img/ /nfs/bases/basefs/
sudo umount /tmp/img

sudo mount /dev/mapper/loop0p1 /tmp/img
sudo rsync -xa --exclude bootcode.bin --exclude start.elf --exclude cmdline.txt /tmp/img/ /tftpboot/base
sudo cp /tmp/img/bootcode.bin /tftpboot
sudo umount /tmp/img
sleep 1
sudo kpartx -d -v $IMGFN

#echo "Copy over base OS"
#sudo mkdir -p /nfs/bases/basefs
#sudo rsync -xa --progress --exclude /nfs --exclude /etc/systemd/network/10-eth0.netdev --exclude /etc/systemd/network/11-eth0.network --exclude /etc/dnsmasq.conf --exclude /etc/network/interfaces / /nfs/bases/basefs
#cat << EOF | sudo tee /nfs/bases/basefs/etc/network/interfaces
#source /etc/network/interfaces.d/*
#EOF

echo "Delete SSH keys in /nfs/bases/basefs. Additionally enable the ssh server."
# Delete SSH keys in /nfs/bases/basefs. 
# Additionally enable the ssh server
cd /nfs/bases/basefs
sudo mount --bind /dev dev
sudo mount --bind /sys sys
sudo mount --bind /proc proc
sudo chroot . rm -f /etc/ssh/ssh_host_*
sudo chroot . dpkg-reconfigure openssh-server
sudo chroot . systemctl enable ssh
sleep 1
sudo umount dev sys proc
sudo touch boot/ssh

# cmdline.txt in /tftpboot/base
echo "Config cmdline.txt in /tftpboot/base"
echo "console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=$IP:/nfs/__SERIAL__,vers=4.1,proto=tcp rw ip=dhcp rootwait" | sudo tee /tftpboot/base/cmdline.txt
sudo chmod 777 /tftpboot/base/cmdline.txt

# /etc/exports
echo "Config /etc/exports"
cat /etc/exports | grep -v tftpboot > /tmp/exports
sudo cp -f /tmp/exports /etc/exports
echo "/tftpboot *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# Start services
sudo systemctl enable dnsmasq
sudo systemctl restart dnsmasq
sudo systemctl enable rpcbind
sudo systemctl restart rpcbind
sudo systemctl enable nfs-kernel-server
sudo systemctl restart nfs-kernel-server

