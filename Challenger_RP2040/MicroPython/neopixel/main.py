from machine import Pin, Timer
import time

led = Pin(10, Pin.OUT)
timer = Timer()

from neopixel import Neopixel

# num_leds, state_machine, pin, mode
pixels = Neopixel(1, 0, 11, "RGB")

def blink(timer):
    led.toggle()

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
        p.set_pixel(0, wheel(j))
        p.show()
        time.sleep(wait)
 
timer.init(freq=2.5, mode=Timer.PERIODIC, callback=blink)

pixels.clear()
pixels.brightness(25)
pixels.set_pixel(0, (255, 0, 255))
pixels.show()

while True:
    rainbow_cycle(pixels,0.01)