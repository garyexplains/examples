# How to create Network Attached Storage (NAS) using a Raspberry Pi

Just about any Single Board Computer (SBC) like a Raspberry Pi, Orange Pi, ODROID or NVIDIA Jetson can be used to create Network Attached Storage (NAS). Really the only prerequisites are that the board can run Linux, has a USB port, and has networking. After that, it just comes down to performance.

To build a Raspberry Pi-powered NAS is quite simple. Here is a step-by-step guide.

## Assumptions
This guide concentrates on the NAS parts of the overall system build, therefore I assume that you have already:

1. Installed a Debian/Ubuntu-based OS on your board. In the base of the Raspberry Pi than means Raspberry Pi OS, for something like the NVIDIA Jetson then you should install Jetpack.
2. Configured a static IP address (this is optional, but recommended)
3. Enabled SSH access to the board
4. Set the board to boot to the command line and not the desktop (to save memory on smaller boards).

## Set the host name.
You need to change the hostname of your board from the default so that you can uniquely identify it on your network.
````
sudo raspi-config
````

Goto 

## Install SAMBA
Use SAMBA to share your files over the network. SAMBA is an open-source re-implementation of the SMB networking protocol (AKA Windows networking). To install SAMBA use:
````
sudo apt install samba
````

## Prep the hard drive
Now we can prepare, partition, format, and mount the hard drive.

+ **WARNING: ALL THE DATA WILL BE LOST ON THIS HARD DRIVE**
+ **WARNING: PROCEED WITH CAUTION**
+ **WARNING: IF YOU HAVE DATA ON THIS DRIVE THAT YOU NEED THEN STOP NOW**

Connect the drive to your board. Find the name of the drive using 'lsblk'. It will likely be /dev/sda, but double-check and verify you have the correct drive name.

You may find that the drive has been auto mounted, you need to unmount it. Do a 'df -h' to see if it is mounted then, if needed, 'sudo umount /dev/sda'

Prep the hard drive
Find it (lsblk)
Check if already mounted
df -h
/dev/sda1 mounted on /media/pi/…..
If it is already formatted then skip the following
Partition it
Format it
## Create the directories
Create a top-level directory
Create a new user (adduser)
Chown to user (e.g. p)
Edit /etc/fstab
## Configure SAMBA
Edit /etc/samba/smb.conf
Add smb user (smbpasswd -a gary)
## Spin down when IDLE
Method 1
sudo apt install hdparm
sudo hdparm -S 60 /dev/sda
(Values between 1 to 240 work in 5 second steps, so 60 is 5 minutes)
Method 2
wget https://downloads.sourceforge.net/project/hd-idle/hd-idle-1.04.tgz
tar -zxvf hd-idle-1.04.tgz
cd hd-idle
sudo apt install debhelper
dpkg-buildpackage -rfakeroot
sudo dpkg -i ../hd-idle_*.deb
sudo vi /etc/default/hd-idle
START_HD_IDLE=true
HD_IDLE_OPTS="-i 180 -l /var/log/hd-idle.log"
