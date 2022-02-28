# How to connect a Raspberry Pi to remote stroage on a NAS over iSCSI

## Introduction
iSCSI provides block-level access to storage devices by carrying SCSI commands over a TCP/IP network. A NAS, like one from Synology, can act as an iSCSI remote storage device.

### SCSI
The Small Computer System Interface is a set of standards for physically connecting and transferring data between computers and peripheral devices.
The SCSI standards define commands, protocols, electrical, optical and logical interfaces. SCSI-1 was published in 1986!

### iSCSI
There are two parties in an iSCSI setup… the client and the server.
- The client is called the Initiator
- The server, the remote storage, is the Target


## Create iSCSI Target on NAS
Many NAS devices support iSCSI. This is how you do it on a Synology NAS running DSM 7.

## Discover and connect Pi to Target

## Format the remote disk

## Mount it permanently
The remote iSCSI drive can only be mounted after boot up has completed. This means the networking is up and open-iscsi is running.


