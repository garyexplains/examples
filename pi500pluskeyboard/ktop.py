import psutil
import time
from RPiKeyboardConfig import RPiKeyboardConfig

# Initialise the keyboard
keyboard = RPiKeyboardConfig()

barcol = [85,85,85,85,85,42,42,42,42,42,0,0,0,0,0,0]
MAXCOL = 15

def ledexists(k, x, y):
	try:
		k.set_led_by_matrix(matrix=[y, x], colour=(42, 255, 255))
	except:
		return 0
	return 1

def plotperc(k, r, p):
	gaps = 0
	numleds = int((p * 14)/100)
	for i in range(numleds + 1):
		while True:
			if i+gaps > MAXCOL:
				break;
			if ledexists(k, i+gaps, r):
				keyboard.set_led_by_matrix(matrix=[r, i+gaps], colour=(barcol[i], 255, 255))
				break
			else:
				gaps = gaps + 1
	for i in range(numleds, 15):
		while True:
			if i+gaps > MAXCOL:
				break;
			if ledexists(k, i+gaps, r):
				keyboard.set_led_by_matrix(matrix=[r, i+gaps], colour=(0, 0, 0))
				break
			else:
				gaps = gaps + 1
	keyboard.send_leds()

# Intro
u = 0
while u < 100:
	for c in range(4):
		plotperc(keyboard, c, u)
	u = u + 15

u = 100
while u > 0:
	for c in range(4):
		plotperc(keyboard, c, u)
	u = u - 15

# Real thing
while True:
	usage = psutil.cpu_percent(interval=None, percpu=True)
	for c in range(4):
		u = usage[c]
		plotperc(keyboard, c, u)
	mem = psutil.virtual_memory()
	plotperc(keyboard, 4, mem.percent)
	smem = psutil.swap_memory()
	plotperc(keyboard, 5, smem.percent)
	time.sleep(0.3)
