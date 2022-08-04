"""
Copyright (c) 2022 Gary Sims

MIT License
SPDX-License-Identifier: MIT
"""

import max7219
from time import sleep
from machine import RTC
import network
import time
from machine import Pin, RTC, SPI
import urequests

clock_style = 1 # 1 = 3 col, 2 = 6 col BDC, 3 = length style

def binary_at(disp, b, x):
    y = 7
    while y > 1:
        bit = b & 0x01
        if bit == 1:
            disp.pixel(x, y, 1)
        y = y - 1
        b = b >> 1

def bcd_at(disp, b, x):
    d1 = b // 10
    d2 = b % 10
    print(b, d1, d2)
    binary_at(display, d1, x)
    binary_at(display, d2, x+1)

def len_at(disp, b, x):
    d1 = b // 10
    d2 = b % 10

    disp.vline(x, 8-d1, d1, 1)
    if d2==9:
        disp.pixel(x,0,1)
    disp.vline(x+1, 8-d2, d2, 1)

def sync_time_with_worldtimeapi_org(rtc, blocking=True):
    TIME_API = "http://worldtimeapi.org/api/ip"

    response = None
    while True:
        try:
            response = urequests.get(TIME_API)
            break
        except:
            if blocking:
                response.close()
                continue
            else:
                response.close()
                return

    json = response.json()
    current_time = json["datetime"]
    the_date, the_time = current_time.split("T")
    year, month, mday = [int(x) for x in the_date.split("-")]
    the_time = the_time.split(".")[0]
    hours, minutes, seconds = [int(x) for x in the_time.split(":")]

    # We can also fill in these extra nice things
    year_day = json["day_of_year"]
    week_day = json["day_of_week"]
    is_dst = json["dst"]
    response.close()
    rtc.datetime((year, month, mday, week_day, hours, minutes, seconds, 0)) # (year, month, day, weekday, hours, minutes, seconds, subseconds)
    
led = Pin("LED", Pin.OUT)
led.off()

#Matrix init
spi = SPI(0,sck=Pin(2),mosi=Pin(3))
cs = Pin(5, Pin.OUT)
display = max7219.Matrix8x8(spi, cs, 1)
display.brightness(10)
display.fill(0)
display.show()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('SSID', 'password1234')

while not wlan.isconnected() and wlan.status() >= 0:
    print("Waiting to connect:")
    time.sleep(1)

led.on()

rtc = RTC()
sync_time_with_worldtimeapi_org(rtc)

force_sync_counter = 0
while True:
    led.toggle()
    Y, M, D, W, H, M, S, SS = rtc.datetime()
    #print(H, M, S)
    
    display.fill(0)
    
    if clock_style == 1:
        binary_at(display, H, 0)
        binary_at(display, M, 2)
        binary_at(display, S, 4)
    elif clock_style == 2:
        bcd_at(display, H, 0)
        bcd_at(display, M, 3)
        bcd_at(display, S, 6)
    else:
        len_at(display, H, 0)
        len_at(display, M, 3)
        len_at(display, S, 6)
    
    display.show()
    if force_sync_counter > 85000: # A little less than a day
        force_sync_counter = 0
        sync_time_with_worldtimeapi_org(rtc, blocking=False)
    force_sync_counter = force_sync_counter + 1
    sleep(1)
    