# How to connect a Raspberry Pi to remote storage on a NAS over iSCSI

## Introduction
iSCSI provides block-level access to storage devices by carrying SCSI commands over a TCP/IP network. A NAS, like one from Synology, can act as an iSCSI remote storage device.

### SCSI
The Small Computer System Interface is a set of standards for physically connecting and transferring data between computers and peripheral devices.
The SCSI standards define commands, protocols, electrical, optical, and logical interfaces. SCSI-1 was published in 1986!

### iSCSI
There are two parties in an iSCSI setup… the client and the server.
- The client is called the Initiator
- The server, the remote storage, is the Target


## Create iSCSI Target on NAS
Many NAS devices support iSCSI. This is how you do it on a Synology NAS running DSM 7.

## Discover and connect Pi to Target
It is important to always use `sudo` when running these iSCSI commands. Some of the commands will work without sudo but the records, status, and database of current connections
is stored on a per-user basis, so when you switch between root and pi the results are different.

Install open-iscsi.
```
sudo apt update
sudo apt -y install open-iscsi
```

To set the Target edit `/etc/iscsi/initiatorname.iscsi`
```
sudo nano /etc/iscsi/initiatorname.iscsi
```
Set InitiatorName to the same IQN you set on the iSCSI target server

```
sudo nano /etc/iscsi/iscsid.conf
```
- ??? node.startup = automatic
- ??? CHAPS

Restart iSCSI services.
```
sudo systemctl restart iscsid open-iscsi
```
```
sudo iscsiadm -m discovery -t sendtargets -p 192.168.1.104
```
Where 192.168.1.104 is the IP address of your NAS.

Confirm results of discovery
```
sudo iscsiadm -m node -o show
```

Login to the Target
```
sudo iscsiadm -m node --login
```
This shoudl be done even if you aren't using authentication

Confirm the established session with the Target
```
sudo iscsiadm -m session -o show
```

The remote iSCSI device should now appear as a block device on the Pi. You should see `sda` now as a device. Use the following commands to check the status of `sda`

```
dmesg | grep scsi
dmesg | grep "\[sd"
cat /proc/partitions
```

`/proc/partitions` should like something like this:

```
major minor  #blocks  name

   1        0       4096 ram0
   1        1       4096 ram1
   1        2       4096 ram2
   1        3       4096 ram3
   1        4       4096 ram4
   1        5       4096 ram5
   1        6       4096 ram6
   1        7       4096 ram7
   1        8       4096 ram8
   1        9       4096 ram9
   1       10       4096 ram10
   1       11       4096 ram11
   1       12       4096 ram12
   1       13       4096 ram13
   1       14       4096 ram14
   1       15       4096 ram15
 179        0   62367744 mmcblk0
 179        1    1580296 mmcblk0p1
 179        2          1 mmcblk0p2
 179        5      32767 mmcblk0p5
 179        6     262143 mmcblk0p6
 179        7   60475392 mmcblk0p7
   8        0  134217728 sda
```

## Format the remote disk
Now that there is a block device (i.e. `sda`) on your Pi, it can be partitioned and formatted like any other HDD/SSD.

You might find this video useful: [How to Partition and Format a Disk in Linux](https://www.youtube.com/watch?v=JCFlsslBvX8)

### Partition the disk

```
sudo fdisk /dev/sda
```

Use `g` to create a new empty GPT partition table

```
Command (m for help): g
Created a new GPT disklabel (GUID: 5C8EB2FC-E8AC-4B45-878A-F3D7431D1463).
The old dos signature will be removed by a write command.
```

Use `n` to create a new partition:

```
Command (m for help): n
Partition number (1-128, default 1):
First sector (2048-268435422, default 2048):
Last sector, +/-sectors or +/-size{K,M,G,T,P} (2048-268435422, default 268435422):

Created a new partition 1 of type 'Linux filesystem' and of size 128 GiB.
```

Use `w` to write the new partition table to the disk and exit.

### Format the disk as ext4
```
sudo mkfs.ext4 /dev/sda1
```

## Mount it permanently
The remote iSCSI drive can only be mounted after boot-up has been completed. This means the networking is up and open-iscsi is running.

