import psutil
import time
from RPiKeyboardConfig import RPiKeyboardConfig
from datetime import datetime


def displayseconds(k):
	now = datetime.now()
	s = now.second
	led = 60 + (s % 15)
	if led!=displayseconds.oldled:
		k.set_led_by_idx(idx=displayseconds.oldled, colour=(0, 0, 0))
		k.set_led_by_idx(idx=led, colour=(170, 200, 255))
		k.send_leds()
		displayseconds.oldled = led


# Initialise the keyboard
keyboard = RPiKeyboardConfig()
displayseconds.oldled = 58

while True:
	now = datetime.now()
	h = 12 if now.hour % 12 == 0 else now.hour % 12  # 1..12
	m = now.minute                                   # 0..59
	s = now.second

	ampm = "A" if now.hour < 12 else "P"
	md1 = int(m/10)
	md2 = m - (md1 * 10)
	if md1 == 0:
		md1 = 10
	if md2 == 0:
		md2 = 10

	if ampm == "A":
		keyboard.set_led_by_matrix(matrix=[0, 13], colour=(170, 100, 255)) # AM - Light
	else:
		keyboard.set_led_by_matrix(matrix=[0, 13], colour=(42, 255, 255)) # PM - Dark


	keyboard.set_led_by_matrix(matrix=[0, h], colour=(85, 255, 255))
	keyboard.set_led_by_matrix(matrix=[1, md1], colour=(85, 255, 255))
	keyboard.send_leds()

	for i in range(5):
		displayseconds(keyboard)
		time.sleep(0.1)

	keyboard.set_led_by_matrix(matrix=[1, md1], colour=(0, 0, 0))
	keyboard.set_led_by_matrix(matrix=[0, h], colour=(85, 255, 255))
	keyboard.set_led_by_matrix(matrix=[1, md2], colour=(170, 100, 255))
	keyboard.send_leds()

	for i in range(5):
		displayseconds(keyboard)
		time.sleep(0.1)

	keyboard.set_led_by_matrix(matrix=[1, md2], colour=(0, 0, 0))
	keyboard.send_leds()

	for i in range(20):
		displayseconds(keyboard)
		time.sleep(0.1)

	keyboard.set_led_by_matrix(matrix=[0, h], colour=(0, 0, 0))
	keyboard.set_led_by_matrix(matrix=[0, 13], colour=(0, 0, 0)) #AM/PM
	keyboard.set_led_by_idx(idx=24+s, colour=(0, 0, 0)) # Seconds
