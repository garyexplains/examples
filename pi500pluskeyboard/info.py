from RPiKeyboardConfig import RPiKeyboardConfig

# Initialise the keyboard
keyboard = RPiKeyboardConfig()

### Keyboard Information
# Get keyboard model and info
print(f"Model: {keyboard.model}")           # "PI500" or "PI500PLUS"
print(f"Variant: {keyboard.variant}")       # "ISO", "ANSI", or "JIS"

# Get firmware version
version = keyboard.get_firmware_version()
print(f"Firmware: {version[0]}.{version[1]}.{version[2]}")

# Get ASCII art of current keyboard layout
ascii_map = keyboard.get_ascii_keycode_map(layer=0)
print(ascii_map)
