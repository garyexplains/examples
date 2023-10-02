# How to enable ZRAM on the Raspberry Pi

This document includes some written notes that accompany my video .....

Test on Raspberry Pi OS based on Debian 11 (bullseye).

- 64-bit version on a Raspberry Pi 4 with 4GB RAM 
- 32-bit version on a Raspberry Pi Zero 2 with 512MB of RAM

Before you start it is best to make sure your system is up to date:

```
sudo apt update && sudo apt upgrade
```

## Install zram-tools

```
sudo apt install zram-tools
```

THAT'S IT!!! 😁

You can see the stats of ZRAM storage using `sudo cat /proc/swaps`

```
Filename                                Type            Size            Used            Priority
/var/swap                               file            102396          29520           -2
/dev/zram0                              partition       262140          0               100
```
You can also use `zramctl` to get status information about the zram setup:

```
NAME       ALGORITHM DISKSIZE DATA COMPR TOTAL STREAMS MOUNTPOINT
/dev/zram0 lz4           256M   4K   63B    4K       4 [SWAP]
```

## Configuration
You can edit `/etc/default/zramswap` to change the compression algorithm or swap allocation. Before you do that it is essential to note that
the ZRAM device size refers to the __uncompressed data__ size, actual memory utilization will be ~2-3x smaller than the zram device size due to compression.

`sudo vi /etc/default/zramswap`

Here is an example:

```
# Compression algorithm selection
# speed: lz4 > zstd > lzo
# compression: zstd > lzo > lz4
# This is not inclusive of all that is available in latest kernels
# See /sys/block/zram0/comp_algorithm (when zram module is loaded) to see
# what is currently set and available for your kernel[1]
# [1]  https://github.com/torvalds/linux/blob/master/Documentation/blockdev/zram.txt#L86
#ALGO=lz4

# Specifies the amount of RAM that should be used for zram
# based on a percentage the total amount of available memory
# This takes precedence and overrides SIZE below
#PERCENT=50

# Specifies a static amount of RAM that should be used for
# the ZRAM devices, this is in MiB
# Use 256 for a Raspberry Pi Zero 2 with 512MB of RAM
#SIZE=256
# Use 1024 for a Raspberry Pi 4 or Raspberry Pi 5 with 4GB of RAM
#SIZE=1024

# Specifies the priority for the swap devices, see swapon(2)
# for more details. Higher number = higher priority
# This should be higher than hdd/ssd swaps.
PRIORITY=100
```

Then restart zramswap with `systemctl restart zramswap`. 

You can see which compression algorithms are supported using `cat /sys/block/zram0/comp_algorithm`

```
lzo lzo-rle [lz4] zstd
```

Once the ZRAM is being used you can see the difference between the __compressed__ size and the __uncompressed_size__ using `zramctl`

```
NAME       ALGORITHM DISKSIZE   DATA  COMPR  TOTAL STREAMS MOUNTPOINT
/dev/zram0 lz4             2G 432.4M 165.1M 173.1M       4 [SWAP]
```

Above you can see that 432MB of main memory have been swapped to ZRAM, but the actual amount of RAM used by the ZRAM is 165MB. At this point `top` or `htop` will report
~450MB of swap space is being used:

```
MiB Swap:   2148.0 total,   1686.8 free,    461.1 used.   1051.5 avail Mem
```

## Kernel Parameters to make better use of ZRAM

The Linux kernel can be tuned and tweaked to make better use of ZRAM.

Edit  `/etc/sysctl.conf` with `sudo vi /etc/sysctl.conf` and add these lines and the end:

```
vm.vfs_cache_pressure=500
vm.swappiness=100
vm.dirty_background_ratio=1
vm.dirty_ratio=50
vm.watermark_boost_factor = 0
vm.watermark_scale_factor = 125
vm.page-cluster = 0
```

Then reboot your system, or enable the new parameters with:

```
sudo sysctl --system
```

### Those Kernel parameters

- A higher _vm.vfs_cache_pressure_ value makes the system more aggressive in reclaiming memory used for dentries and inodes. Conversely, a lower value means it would prioritize keeping them in memory at the expense of other cached data.
- _vm.swappiness_ is a kernel parameter in Linux that controls the relative weight given to swapping out runtime memory, as opposed to dropping pages from the system page cache. A higher value means the kernel will aggressively swap processes out of physical memory and move them to swap space.
- _vm.dirty_background_ratio_ is a tunable parameter that determines the percentage of system memory that can be filled with "dirty" pages before the kernel begins writing them to disk in the background. "Dirty" pages are those memory pages that have been modified (or "dirtied") but have not yet been written back to their respective files on disk. _vm.dirty_background_ratio_ is expressed as a percentage.
- _vm.dirty_ratio_ is a tunable parameter that represents a percentage. It specifies the maximum amount of total system memory (RAM) that can be filled with "dirty" pages before processes are forced to start writing these pages to disk.
- The _vm.page-cluster_ kernel parameter in Linux controls the number of pages that are read from or written to the disk in a single operation during a swap-in or file-page reclaim from swap space. Various tests done by Pop! OS and some testing done by users on r/Fedora have shown that _vm.page-cluster = 0_ is ideal.
