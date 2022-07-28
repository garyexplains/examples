# SPDX-FileCopyrightText: 2022 Gary Sims
# Heavily based on work by:
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from digitalio import DigitalInOut
from digitalio import Direction
import rtc
import adafruit_ssd1306

from adafruit_espatcontrol import (
    adafruit_espatcontrol,
    adafruit_espatcontrol_wifimanager,
)

def sync_time_with_worldtimeapi_org(wifi, rtc, blocking=True):
    TIME_API = "http://worldtimeapi.org/api/ip"

    response = None
    while True:
        try:
            response = wifi.get(TIME_API)
            break
        except (ValueError, RuntimeError, adafruit_espatcontrol.OKError) as e:
            if blocking:
                continue
            else:
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

    now = time.struct_time((year, month, mday, hours, minutes, seconds, week_day, year_day, is_dst))

    rtc.datetime = now

# OLED display 128x32
i2c = busio.I2C(board.GP17, board.GP16)
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)
oled.text("Init...", 0, 0, 1)
oled.show()

#RTC
the_rtc = rtc.RTC()

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Debug Level
# Change the Debug Flag if you have issues with AT commands
debugflag = False

if board.board_id == "challenger_rp2040_wifi":
    RX = board.ESP_RX
    TX = board.ESP_TX
    resetpin = DigitalInOut(board.WIFI_RESET)
    rtspin = False
    uart = busio.UART(TX, RX, baudrate=11520, receiver_buffer_size=2048)
    esp_boot = DigitalInOut(board.WIFI_MODE)
    esp_boot.direction = Direction.OUTPUT
    esp_boot.value = True
    status_light = None

else:
    RX = board.ESP_TX
    TX = board.ESP_RX
    resetpin = DigitalInOut(board.ESP_WIFI_EN)
    rtspin = DigitalInOut(board.ESP_CTS)
    uart = busio.UART(TX, RX, timeout=0.1)
    esp_boot = DigitalInOut(board.ESP_BOOT_MODE)
    esp_boot.direction = Direction.OUTPUT
    esp_boot.value = True
    status_light = None

oled.fill(0)
oled.text("Connect...", 0, 0, 1)
oled.show()

esp = adafruit_espatcontrol.ESP_ATcontrol(
    uart, 115200, reset_pin=resetpin, rts_pin=rtspin, debug=debugflag
)
wifi = adafruit_espatcontrol_wifimanager.ESPAT_WiFiManager(esp, secrets, status_light)
# Error check?

oled.fill(0)
oled.text("Sync...", 0, 0, 1)
oled.show()
sync_time_with_worldtimeapi_org(wifi, the_rtc)

force_sync_counter = 0
while True:
    tnow = time.localtime()
    #print(tnow)
    tstr = "{:02d}".format(tnow.tm_hour) + ":" + "{:02d}".format(tnow.tm_min) + ":" + "{:02d}".format(tnow.tm_sec)
    oled.fill(0)
    oled.text(tstr, 0, 0, 1)
    oled.show()
    force_sync_counter = force_sync_counter + 1
    if force_sync_counter > 85000: # A little less than a day
        force_sync_counter = 0
        sync_time_with_worldtimeapi_org(wifi, the_rtc, blocking=False)
    time.sleep(1)