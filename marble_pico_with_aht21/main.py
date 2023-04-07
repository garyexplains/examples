from machine import Pin, Timer

led = Pin(25, Pin.OUT)
timer = Timer()

def blink(timer):
    led.toggle()

timer.init(freq=2.5, mode=Timer.PERIODIC, callback=blink)

import time, machine
import aht

# Example SCL pin and SDA pin for WEMOS D1 mini Lite
i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4),id=0)
sensor = aht.AHT2x(i2c, crc=True)

while True:
    print("Humidity: {:.2f}".format(sensor.humidity))
    print("Temperature: {:.2f}".format(sensor.temperature))
    time.sleep(1)
