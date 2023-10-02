# How to enable ZRAM on the Raspberry Pi

This document includes some written notes that accompany my video ?????


## Install zram-tools

```
sudo apt install zram-tools
```

THAT'S IT!!!

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
You can edit `/etc/default/zram-swap` to change the compression algorithm or swap allocation: `sudo vi /etc/default/zram-swap`

Here is an example:




and then restart zram-swap with systemctl restart zram-swap.service. The configuration file is heavily commented and self-documenting.

A very simple configuration that's expected to use roughly 2GB RAM might look something like:

# override fractional calculations and specify a fixed swap size
_zram_fixedsize="6G"

# compression algorithm to employ (lzo, lz4, zstd, lzo-rle)
_zram_algorithm="lzo-rle"
Remember that the ZRAM device size references uncompressed data, real memory utilization should be ~2-3x smaller than the zram device size due to compression.

You can see which compression algorithms are supported using `cat /sys/block/zram0/comp_algorithm`

```
lzo lzo-rle [lz4] zstd
```
