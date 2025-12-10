import time
from RPiKeyboardConfig import RPiKeyboardConfig

# Initialise the keyboard
keyboard = RPiKeyboardConfig()

# Set LED direct control mode
keyboard.set_led_direct_effect()

MAXIDX = 84

while True:
	for hue in range(256):
		for i in range(MAXIDX+1):
			keyboard.set_led_by_idx(idx=i, colour=(hue, 255, 255))
		keyboard.send_leds()
