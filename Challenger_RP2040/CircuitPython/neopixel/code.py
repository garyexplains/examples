# SPDX-FileCopyrightText: 2022 Gary Sims
# Heavily based on:
# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
NeoPixel example for Challenger RP2040 WiFi/BLE

REQUIRED HARDWARE:
* RGB NeoPixel LEDs connected to pin GP11.
"""
import board
import neopixel
import time
import digitalio

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)
 
 
def rainbow_cycle(p, wait):
    for j in range(255):
        p.fill(wheel(j))
        p.show()
        time.sleep(wait)
        
# Update this to match the number of NeoPixel LEDs connected to your board.
num_pixels = 1

pixels = neopixel.NeoPixel(board.GP11, num_pixels)
pixels.brightness = 120

led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT

while True:
    pixels.fill((255, 255, 0))
    led.value = True
    rainbow_cycle(pixels,0)
    led.value = False
    rainbow_cycle(pixels,0)