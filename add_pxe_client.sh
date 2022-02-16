#!/bin/bash

# Copyright (c) 2022 Gary Sims. All rights reserved.

# THIS SOFTWARE IS PROVIDED ``AS IS″ AND WITHOUT ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE.   

# This was tested on a Raspberry Pi 4 running Raspberry Pi OS Lite for ARM64,
# based on Debian version 11 (bullseye).

set -e

if [ "$#" -ne 1 ]
then
  echo "Usage: ..."
  exit 1
fi

# Remove leading zeros from serial number
SERIALNUM=$(echo $1 | sed 's/^0*//')
IP="192.168.1.45"

echo "Adding $SERIALNUM to PXE server $IP"

sudo mkdir -p /tftpboot/$SERIALNUM

sudo rsync -ax /tftpboot/base/ /tftpboot/$SERIALNUM
sudo sed -i 's/__SERIAL__/'$SERIALNUM'/g' /tftpboot/$SERIALNUM/cmdline.txt

#
# TODO
# copy basefs to $SERIALNUM subtree
sudo mkdir -p /nfs/$SERIALNUM
sudo rsync -ax /nfs/bases/basefs/ /nfs/$SERIALNUM

# edit /etc/exports
cat /etc/exports | grep -v $SERIALNUM > /tmp/exports
sudo cp -f /tmp/exports /etc/exports
echo "/nfs/$SERIALNUM *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# edit /etc/fstab
echo | sudo tee /nfs/$SERIALNUM/etc/fstab
echo "proc /proc proc defaults 0 0" | sudo tee -a /nfs/$SERIALNUM/etc/fstab
echo "$IP:/tftpboot /boot nfs defaults,vers=4.1,proto=tcp 0 0" | sudo tee -a /nfs/$SERIALNUM/etc/fstab

# whatelse?
sudo systemctl restart dnsmasq
sudo systemctl restart rpcbind
sudo systemctl restart nfs-kernel-server