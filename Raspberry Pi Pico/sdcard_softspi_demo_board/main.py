import machine
import sdcard
import uos

# Assign chip select (CS) pin (and start it high)
cs = machine.Pin(22, machine.Pin.OUT)

# Intialize SPI peripheral (start with 1 MHz)
spi = machine.SoftSPI(baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(5),
                  mosi=machine.Pin(18),
                  miso=machine.Pin(19))

# Initialize SD card
sd = sdcard.SDCard(spi, cs)

# Mount filesystem
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")

# Create a file and write something to it
with open("/sd/test01.txt", "w") as file:
    file.write("Hello, SD World!\r\n")
    file.write("This is a test\r\n")

# Open the file we just created and read from it
with open("/sd/test01.txt", "r") as file:
    data = file.read()
    print(data)