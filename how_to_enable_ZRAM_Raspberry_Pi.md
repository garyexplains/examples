# How to enable ZRAM on the Raspberry Pi

This document includes some written notes that accompany my video ?????

This applies to Raspberry Pi OS based on Debian 11 (bullseye).

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
SIZE=500

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
