import time
from RPiKeyboardConfig import RPiKeyboardConfig

# Initialise the keyboard
keyboard = RPiKeyboardConfig()

# Set LED direct control mode
keyboard.set_led_direct_effect()

MAXIDX = 84
PARTS = 4
import random
hue = random.randint(0, 255)   # inclusive: 0..255
for i in range(MAXIDX+1):
	section = (i * PARTS) // MAXIDX
	h =  (hue + (section * 50)) % 255
	keyboard.set_led_by_idx(idx=i, colour=(h, 255, 255))
keyboard.send_leds()
