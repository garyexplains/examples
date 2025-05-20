# I2C Scanner MicroPython
from machine import Pin, SoftI2C
from machine import Pin, SoftI2C
import ssd1306
import time
import digits
import random

dice = [6,8,10,12,20,4]
currentdiceidx = 0
currentdice = 6

def shake():
    global currentdice
    i = 0
    while i < 10:
        r = random.randint(1, 9)
        digits.printnum(r, oled, 0, 0)
        if currentdice > 9:
            digits.printnum(r, oled, 32, 0)
        oled.fill(0)
        i = i + 1

def shakedice():
    global currentdice
    i = 0
    while i < 10:
        r = random.randint(1, 6)
        digits.putdice(r, oled, 0, 0)
        if currentdice == 12:
            digits.putdice(r, oled, 36, 0)
        oled.fill(0)
        i = i + 1

#You can choose any other combination of I2C pins
i2c = SoftI2C(scl=Pin(15), sda=Pin(14))

oled_width = 128
oled_height = 32
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

spinbutton = Pin(17, Pin.IN, Pin.PULL_UP)
selectbutton = Pin(11, Pin.IN, Pin.PULL_UP)
while True:
    if selectbutton.value() == 0:  # Detect button press
        time.sleep(0.02)    # Anti-bounce
        if selectbutton.value() == 0:
            currentdiceidx = currentdiceidx + 1
            if currentdiceidx >= len(dice):
                currentdiceidx = 0
            currentdice = dice[currentdiceidx]
            print(currentdice, currentdiceidx)
            oled.fill(0)
            digits.printnum(currentdice, oled, 0, 0)

            while selectbutton.value() == 0:  # Wait for it to be released
                pass
            
    if spinbutton.value() == 0:  # Detect button press
        time.sleep(0.02)    # Anti-bounce
        if spinbutton.value() == 0:
            if currentdice == 6 or currentdice == 12:
                shakedice()
            else:
                shake()
            oled.fill(0)
            if currentdice == 12:
                r = random.randint(1, 6)
                r1 = random.randint(1, 6)
            else:
                r = random.randint(1, currentdice)
            print(r)
            if currentdice == 6:
                digits.putdice(r, oled, 0, 0)
            elif currentdice == 12:
                digits.putdice(r, oled, 0, 0)
                digits.putdice(r1, oled, 36, 0)
            elif currentdice > 9:
                digits.printnum(r, oled, 0, 0, 1)
            else:
                digits.printnum(r, oled, 0, 0)
            while spinbutton.value() == 0:  # Wait for it to be released
                pass

