import time
from RPiKeyboardConfig import RPiKeyboardConfig
import random

MAXCOL = 15
MAXROW = 5

def ledexists(k, x, y):
	try:
		k.set_led_by_matrix(matrix=[y, x], colour=(42, 255, 255))
	except:
		return 0
	return 1

# Initialise the keyboard
keyboard = RPiKeyboardConfig()

# Set LED direct control mode
keyboard.set_led_direct_effect()

for r in range(MAXROW+1):
	hue = random.randint(0, 255)   # inclusive: 0..255
	for c in range(MAXCOL+1):
		if ledexists(keyboard, c, r):
			keyboard.set_led_by_matrix(matrix=[r, c], colour=(hue, 255, 255))
keyboard.send_leds()
