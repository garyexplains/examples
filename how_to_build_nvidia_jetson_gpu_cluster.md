# Introduction

Here are some brief instructions on how to build an NVIDIA GPU Accelerated Supercomputer using Jetson boards like the Jetson Nano and the Jetson Xavier.
These instructions accompany the video TBD.

# Hardware
You will need at least two Jetson boards. The cheapest is the Jetson Nano 2GB at $59. You will need Ethernet (preferable Gigabit), and a hub/switch.
For the initial setup, you will also need a monitor, keyboard, and mouse. But these aren't needed once the cluster is configured and running.

https://developer.nvidia.com/embedded/jetson-nano-2gb-developer-kit

# Software
You need to be running the same version of the NVIDIA JetPack SDK on each board.
JetPack includes the OS (Linux, based on Ubuntu) along with CUDA-X accelerated libraries, samples, documentation, and developer tools.

https://developer.nvidia.com/embedded/jetpack


# Configuration
## User configuration
Make sure you use the same user account name across all the boards.

## Network
Each board should be in the same physical network, within the same subnet. The easiest option is to use fixed IP addresses like:

```
192.168.1.51
192.168.1.52
192.168.1.53
192.168.1.54
```
## Prerequiste software
Install the prerequiste software on **every** node
```
sudo apt-get update; sudo apt-get -y install openssh-server git htop python3-pip python-pip nano 
```

## Generate your ssh keys
Generate your ssh keys on the controller node. Run the command and follow the prompts.

```
ssh-keygen
```
Then, for every node in your cluster (Replace <IP-ADDRESS> with IP of each node):
```
ssh-copy-id <IP-ADDRESS>
```
e.g. `ssh-copy-id 192.168.1.51`

## Cluster file
Create a cluster file on the controller node. One line per cluster.
```
192.168.1.51
192.168.1.52
etc
```
You can do this in an editor like vim or nano, or use a command like this:
```
cat > clusterfile << _EOF_
192.168.1.51
192.168.1.52
192.168.1.53
192.168.1.54
_EOF_
```
## /etc/hosts
On each node make sure all other nodes are listed in /etc/hosts with their right hostnames, e.g.
```
192.168.1.51   node1
192.168.1.52   node2
192.168.1.53   node3
192.168.1.54   node4
```

# The MPI & CUDA program
A copy of the script must be present on each node with the same path and filename

## To run it on on cluster
`mpiexec -hostfile ~/clusterfile python ./primality_cluster_test1.py`

