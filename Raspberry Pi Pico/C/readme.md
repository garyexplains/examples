# How to program a Raspberry Pico using WSL in Windows 10

Note: When you see a path like /mnt/c/Users/Gary please replace it with the path to your own user folder on Windows. It is important that you use a folder accessible from Windows (not just WSL) so that you can drag and drop the .uf2 file onto the Pico.

## In WSL
### Get the SDK and the examples
```
cd /mnt/c/Users/Gary/
mkdir pico
cd pico

git clone -b master https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
cd ..
git clone -b master https://github.com/raspberrypi/pico-examples.git
```
### Get the compilers etc
```
sudo apt update
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi build-essential

git clone https://github.com/raspberrypi/pico-project-generator.git
```

### Generate your project

Note: Make sure you are running the Xserver (see "Open GUI apps on Windows Subsystem for Linux (and on Raspberry Pi)" - https://www.youtube.com/watch?v=ymV7j003ETA)

```
cd pico-project-generator
export PICO_SDK_PATH="/mnt/c/Users/Gary/pico/pico-sdk"
export DISPLAY=127.0.0.1:0
./pico_project.py --gui
```

### Build the project
First go into the project directory
```
cd ..
cd PROJECT (i.e cd gary/hello_world_usb)
```
Edit the code, replace the puts() with:
```
        while (true) {
            printf("Hello from Pico!\n");
            sleep_ms(1000);
         }
```
And build
```
cd build
cmake ..
make
```

## In Windows (not WSL)
### Copy .uf2 file to Pico

Press and hold the BOOTSEL button while powering on (or resetting) the Pico. A drive will appear called RPI-RP2. Copy the .uf2 directly to that drive. The Pico will reboot and start running the code.
