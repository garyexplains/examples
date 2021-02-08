# Display Image & text on I2C driven ssd1306 OLED display
# Needs https://github.com/raspberrypi/micropython/blob/pico/drivers/display/ssd1306.py on Pico
from machine import Pin, I2C, Timer
from ssd1306 import SSD1306_I2C
import framebuf

WIDTH = 128 # oled display width
HEIGHT = 32 # oled display height

i2c = I2C(0) # Init I2C using I2C0 defaults, SCL=Pin(GP9), SDA=Pin(GP8), freq=400000

oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)                  # Init oled display

# Clear the oled display in case it has junk on it.
oled.fill(0)

# Add some text
oled.text("Rasp Pi Pico",5,5)
oled.text("Prime Finder:",5,15)

# Update the oled display
oled.show()

led25 = Pin(25, Pin.OUT)
tim25 = Timer()

def tick25(timer):
    global led25
    led25.toggle()   

tim25.init(freq=2, mode=Timer.PERIODIC, callback=tick25)

def is_prime(n: int) -> bool:
    """Primality test using 6k+-1 optimization."""
    if n <= 3:
        return n > 1
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i ** 2 <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

p = 1
while p < 1000000:
    if is_prime(p):
        oled.fill_rect(5,25,80,8,0)
        oled.text(str(p),5,25)
        oled.show()
    p = p + 1
