import time
from RPiKeyboardConfig import RPiKeyboardConfig

MAXCOL = 15
ROW = 1
STARTCOL = 0

def ledexists(k, x, y):
	try:
		k.set_led_by_matrix(matrix=[y, x], colour=(42, 255, 255))
	except:
		return 0
	return 1

def inctonextvalidled(k, x, y):
	while True:
		x = x + 1
		if x > MAXCOL:
			x = STARTCOL
		if ledexists(k, x, y):
			return x


# Initialise the keyboard
keyboard = RPiKeyboardConfig()

# Set LED direct control mode
keyboard.set_led_direct_effect()

i1 = STARTCOL
i2 = MAXCOL
i3 = MAXCOL - 1

while True:
	keyboard.set_led_by_matrix(matrix=[ROW, i1], colour=(0, 255, 255))
	keyboard.set_led_by_matrix(matrix=[ROW, i2], colour=(0, 255, 232))
	keyboard.set_led_by_matrix(matrix=[ROW, i3], colour=(0, 255, 128))
	keyboard.send_leds()

	time.sleep(0.05)

	keyboard.set_led_by_matrix(matrix=[ROW, i3], colour=(0, 0, 0))
	keyboard.send_leds()

	i1 = inctonextvalidled(keyboard, i1, ROW)
	i2 = inctonextvalidled(keyboard, i2, ROW)
	i3 = inctonextvalidled(keyboard, i3, ROW)
