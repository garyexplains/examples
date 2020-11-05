# Introduction
Here are a few notes to help you get qemu running on a Raspberry Pi to emulate a RISC-V 64-bit processor in a virtual machine.

# Prerequisites
You will need a Raspberry Pi 4 with at least 4GB of RAM. This may also work on a Raspberry Pi 4 with 2GB of RAM, but you will need to allocate the virtual machine less RAM.
Theoretically, it might work on a Raspberry Pi 3, but RAM will be an issue.

Also, you will need to run a 64-bit version of Linux like Ubuntu 18.04 LTS for the Pi 4. It *may* work using the 64-bit version of Raspberry Pi OS.

# Prepare the Pi

```
sudo apt update
sudo apt install build-essential nano git htop ninja-build wget
```

# Build QEMU
```
git clone https://github.com/qemu/qemu
cd qemu
mkdir build
cd build
../configure --target-list=riscv64-softmmu
make  -j3
sudo make install
cd ..
```

# Download the RISC-V version of Fedora
You can download Fedora RISC-V from https://dl.fedoraproject.org/pub/alt/risc-v/repo/virt-builder-images/images/
```
wget https://dl.fedoraproject.org/pub/alt/risc-v/repo/virt-builder-images/images/Fedora-Minimal-Rawhide-20200108.n.0-fw_payload-uboot-qemu-virt-smode.elf
wget https://dl.fedoraproject.org/pub/alt/risc-v/repo/virt-builder-images/images/Fedora-Minimal-Rawhide-20200108.n.0-sda.raw.xz
unxz Fedora-Minimal-Rawhide-20200108.n.0-sda.raw.xz
```

# Run QEMU
```
qemu-system-riscv64 \
   -nographic \
   -machine virt \
   -smp 2 \
   -m 2047M \
   -kernel Fedora-Minimal-Rawhide-*-fw_payload-uboot-qemu-virt-smode.elf \
   -bios none \
   -object rng-random,filename=/dev/urandom,id=rng0 \
   -device virtio-rng-device,rng=rng0 \
   -device virtio-blk-device,drive=hd0 \
   -drive file=Fedora-Minimal-Rawhide-20200108.n.0-sda.raw,format=raw,id=hd0 \
   -device virtio-net-device,netdev=usernet \
   -netdev user,id=usernet,hostfwd=tcp::10000-:22
```

# Fedora
Login with `riscv` and `fedora_rocks!`

```
sudo dnf install gcc htop nano git file
mkdir src
cd src
curl https://raw.githubusercontent.com/garyexplains/examples/master/doublelinkedlist.c --output doublelinkedlist.c
gcc -O3 -o doublelinkedlist doublelinkedlist.c
file doublelinkedlist 
./doublelinkedlist 
```

# Useful links
https://wiki.qemu.org/Documentation/Platforms/RISCV

https://fedoraproject.org/wiki/Architectures/RISC-V/Installing

https://risc-v-getting-started-guide.readthedocs.io/en/latest/linux-qemu.html
