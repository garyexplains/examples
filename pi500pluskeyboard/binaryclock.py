import psutil
import time
from RPiKeyboardConfig import RPiKeyboardConfig
from datetime import datetime

def binary_at(k, b, r):
	# There is no LED at [2,1] so shift every along a bit
	if r == 2:
		y = 9
		limit = 1
	else:
		y = 8
		limit = 0
	while y > limit:
		bit = b & 0x01
		if bit == 1:
			k.set_led_by_matrix(matrix=[r, y], colour=(85, 255, 255))
		else:
			k.set_led_by_matrix(matrix=[r, y], colour=(0, 0, 0))
		y = y - 1
		b = b >> 1
	k.send_leds()

# Initialise the keyboard
keyboard = RPiKeyboardConfig()

while True:
	now = datetime.now()
	h = 12 if now.hour % 12 == 0 else now.hour % 12  # 1..12
	m = now.minute                                   # 0..59
	s = now.second

	ampm = "A" if now.hour < 12 else "P"
	if ampm == "A":
		keyboard.set_led_by_matrix(matrix=[0, 13], colour=(170, 100, 255)) # AM - Light
	else:
		keyboard.set_led_by_matrix(matrix=[0, 13], colour=(42, 255, 255)) # PM - Dark

	binary_at(keyboard, h, 0)
	binary_at(keyboard, m, 1)
	binary_at(keyboard, s, 2)
	time.sleep(0.5)
