# How to create Network Attached Storage (NAS) using a Raspberry Pi

Just about any Single Board Computer (SBC) like a Raspberry Pi, Orange Pi, ODROID or NVIDIA Jetson can be used to create Network Attached Storage (NAS). Really the only prerequisites are that the board can run Linux, has a USB port, and has networking. After that, it just comes down to performance.

To build a Raspberry Pi-powered NAS is quite simple. Here is a step-by-step guide.

## Assumptions
This guide concentrates on the NAS parts of the overall system build, therefore I assume that you have already:

1. Installed a Debian/Ubuntu-based OS on your board. In the base of the Raspberry Pi than means Raspberry Pi OS, for something like the NVIDIA Jetson then you should install Jetpack.
2. Configured a static IP address (this is optional, but recommended)
3. Enabled SSH access to the board
4. Set the board to boot to the command line and not the desktop (to save memory on smaller boards).

If you need help with _vi_ or with the Linux commandline then please check these videos:

+ [Understanding Vi and Vim (Vi IMproved) in 10 Minutes](https://youtu.be/nbph7RYWhwM)
+ [Linux Directories Explained - including /etc /home /var /proc /usr](https://youtu.be/PEaixsvzRUk)
+ [10 Linux Terminal Commands for Beginners](https://youtu.be/CpTfQ-q6MPU)

### Power matters
You need to be sure about how you connect a hard drive to the Raspberry Pi. Some hard drives draw the power directly from the USB port and depending on the drive and the model of Pi board then the power drawn maybe too much. Using an external hard drive with its own power supply is the best option or at least use a powered USB hub.

More information here:

+ [Raspberry Pi Power FAQ](https://www.raspberrypi.org/documentation/faqs/#pi-power)
+ [External storage configuration](https://www.raspberrypi.org/documentation/configuration/external-storage.md)

## Set the host name.
You need to change the hostname of your board from the default so that you can uniquely identify it on your network.
```
sudo raspi-config
```

Goto "2 Network Options" and then "N1 Hostname". Set the host name (e.g. 'mypi0nas', exit from _raspi-config_ using "< FINISH >" and then reboot as prompted.

## Install SAMBA
Use SAMBA to share your files over the network. SAMBA is an open-source re-implementation of the SMB networking protocol (AKA Windows networking). To install SAMBA use:
```
sudo apt install samba
```

## Prep the hard drive
Now we can prepare, partition, format, and mount the hard drive.

+ **WARNING: ALL THE DATA WILL BE LOST ON THIS HARD DRIVE**
+ **WARNING: PROCEED WITH CAUTION**
+ **WARNING: IF YOU HAVE DATA ON THIS DRIVE THAT YOU NEED THEN STOP NOW**

Connect the drive to your board. Find the name of the drive using `lsblk`. It will likely be _/dev/sda_, but double-check and verify you have the correct drive name.

+ **From here on I will assume the drive is /dev/sda, please use the correct drive path according to your setup**

You may find that the drive has been auto mounted, you need to unmount it. Do a `df -h` to see if it is mounted then, if needed, `sudo umount /dev/sda`

+ **JUMP TO "Create the directories" IF YOU DON"T WANT TO PARTITION AND FORMAT THE DRIVE**

Next, you need to partition the drive. I will use _fdisk_, there are alternatives. I have a whole video about how to do this: [How to Partition and Format a Disk in Linux](https://www.youtube.com/watch?v=JCFlsslBvX8)

+ **WARNING: ALL THE DATA ON THIS DRIVE WILL BE LOST**

```
sudo fdisk /dev/sda
o
n
p
1
w
```

Now create the filesystem:

```
sudo mkfs -t ext4 /dev/sda1
```

## Create the directories
Create a top-level directory to mount the drive

```
sudo mkdir /myhd
```

Create a top-level directory that you can share on the network:

```
cd /myhd
sudo mkdir gary
```

Create a new user, for example, _gary_
```
sudo adduser gary
```

Follow the prompts and enter a new password, etc.

Change the ownership of the gary directory:

```
sudo chown gary:gary gary
```

## Edit /etc/fstab
```
ls -la /dev/disk/by-uuid
```

Note down the long number like `0603c209-795d-48d4-87e9-7f91390b1e6d` that points to /dev/sda1

Now edit the /etc/fstab file using `sudo vi /etc/fstab` and add a line like this:

```
UUID=0603c209-795d-48d4-87e9-7f91390b1e6d /myhd ext4 nofail,auto 0 0
```

Now force a mount of all the drives listed and /etc/fstab and check the results:

```
sudo mount -a
df -h
```

## Configure SAMBA
Edit /etc/samba/smb.conf (with `sudo vi /etc/samba/smb.conf`) and add this to the end of the file:

```
[gary]
        comment = Gary
        browseable = yes
        path = /myhd/gary
        guest ok = no
        read only = no
        writable = yes
        valid users = gary
```

Also, make sure you comment out (using #) the _[home]_ section. This will stop a conflict between the network share _gary_ defined above and the _gary_ home folder.
Add an smb user 

```
sudo smbpasswd -a gary
```

Set the password as promotped.

## All done!
Restart the samba service (or reboot) using `sudo service smbd restart` and you should have access to _\\\\mypi0nas_ via Windows Explorer. If that doesn't work try the static IP address you set, e.g. _\\\\192.168.1.42_


## Spin down when IDLE
You should also make sure that the hard drives spin down when idle. There are two methods.

### Method 1 hd-parm
```
sudo apt install hdparm
sudo hdparm -S 60 /dev/sda
```

(Values between 1 to 240 work in 5-second steps, so 60 is 5 minutes)
### Method 2 hd-idle

```
cd
wget https://downloads.sourceforge.net/project/hd-idle/hd-idle-1.04.tgz
tar -zxvf hd-idle-1.04.tgz
cd hd-idle
sudo apt install debhelper
dpkg-buildpackage -rfakeroot
sudo dpkg -i ../hd-idle_*.deb
sudo vi /etc/default/hd-idle
```

Set `START_HD_IDLE=true` and uncomment this line: `HD_IDLE_OPTS="-i 180 -l /var/log/hd-idle.log"`
