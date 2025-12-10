from RPiKeyboardConfig import RPiKeyboardConfig

# Initialise the keyboard
keyboard = RPiKeyboardConfig()

# Set LED direct control mode
keyboard.set_led_direct_effect()

# Set individual LED by index (HSV format: hue, saturation, value)
keyboard.set_led_by_idx(idx=5, colour=(0, 255, 255))      # Red
keyboard.set_led_by_idx(idx=6, colour=(85, 255, 255))     # Green
keyboard.set_led_by_idx(idx=7, colour=(170, 255, 255))    # Cyan

# Set LED by matrix position
keyboard.set_led_by_matrix(matrix=[2, 3], colour=(42, 255, 255))  # Orange

# Send LED updates to keyboard (required after setting colours)
keyboard.send_leds()

