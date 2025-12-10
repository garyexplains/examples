import time
from RPiKeyboardConfig import RPiKeyboardConfig

# Initialise the keyboard
keyboard = RPiKeyboardConfig()

# Set LED direct control mode
keyboard.set_led_direct_effect()

MAXIDX = 84

for i in range(MAXIDX+1):
	keyboard.set_led_by_idx(idx=i, colour=(0, 0, 255))
keyboard.send_leds()
