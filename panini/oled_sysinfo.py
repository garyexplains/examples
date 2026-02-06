import time
import subprocess
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import psutil
import socket

# --- settings ---
# I2C Bus，Orin Nano 的 Pin 3,5
I2C_BUS = 7
OLED_ADDR = 0x3c

# CPU temperature path
CPU_TEMP_PATH = "/sys/class/thermal/thermal_zone1/temp"

# --- initialize I2C 和 OLED ---
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=OLED_ADDR)
    print("OLED display initialized successfully.")
except Exception as e:
    print(f"Error initializing I2C or OLED: {e}")
    exit()

# --- display clear ---
display.fill(0)
display.show()

# --- setup canvas ---
width = display.width
height = display.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

# --- load font ---
try:
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12
    )
except IOError:
    font = ImageFont.load_default()

try:
    small_font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10
    )
except IOError:
    small_font = ImageFont.load_default()

# ---------------------------------------------------------------------
# IP display：prioritize Wi-Fi → Ethernet → others
# ---------------------------------------------------------------------
def get_ip_address():
    wifi_ifaces = []
    eth_ifaces = []
    other_ifaces = []

    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip = addr.address

                # 排除 loopback
                if ip.startswith("127."):
                    continue

                if iface.startswith(("wlan", "wlp")):
                    wifi_ifaces.append((iface, ip))
                elif iface.startswith(("eth", "en")):
                    eth_ifaces.append((iface, ip))
                else:
                    other_ifaces.append((iface, ip))

    if wifi_ifaces:
        iface, ip = wifi_ifaces[0]
        return f"WiFi IP: {ip}"
    elif eth_ifaces:
        iface, ip = eth_ifaces[0]
        return f"ETH  IP: {ip}"
    elif other_ifaces:
        iface, ip = other_ifaces[0]
        return f"IP: {ip}"
    else:
        return "IP: Not found"

# --- system info ---
def get_cpu_usage():
    cpu = psutil.cpu_percent(interval=None)
    return f"CPU Use: {cpu:05.2f}%"

def get_mem_usage():
    mem = psutil.virtual_memory()
    return f"RAM Use: {mem.percent:05.2f}%"

def get_cpu_temperature():
    try:
        with open(CPU_TEMP_PATH, 'r') as f:
            cpu_temp = int(f.read()) / 1000.0
        return f"CPU Temp: {cpu_temp:.1f}°C"
    except FileNotFoundError:
        return "CPU Temp: N/A"
    except Exception:
        return "CPU Temp: Err"

def get_hostname():
    return f"Host: {socket.gethostname()}"

def get_uptime():
    uptime_seconds = int(time.time() - psutil.boot_time())
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days > 0:
        uptime_str = f"{days}d {hours:02d}h {minutes:02d}m"
    else:
        uptime_str = f"{hours:02d}h {minutes:02d}m"
    return f"Up: {uptime_str}"

def get_ram_available_gb():
    mem = psutil.virtual_memory()
    return f"RAM Avl: {mem.available / (1024**3):.2f} GB"

def get_ram_total_gb():
    mem = psutil.virtual_memory()
    return f"RAM Tot: {mem.total / (1024**3):.2f} GB"

def get_top_processes(sort_key):
    sort_map = {
        "cpu": "%cpu",
        "mem": "%mem",
    }
    sort_field = sort_map.get(sort_key, "%cpu")

    try:
        cmd = [
            "ps",
            "-eo",
            "comm,%cpu,%mem",
            f"--sort=-{sort_field}",
        ]
        output = subprocess.check_output(cmd, text=True)
    except Exception:
        return ["(process read error)"]

    lines = output.strip().splitlines()
    if len(lines) <= 1:
        return ["(no process data)"]

    top_lines = []
    for line in lines[1:5]:
        cols = line.split()
        if len(cols) < 3:
            continue
        comm, cpu_pct, mem_pct = cols[0], cols[1], cols[2]
        if sort_key == "cpu":
            entry = f"{comm[:12]} C{cpu_pct}"
        else:
            entry = f"{comm[:12]} M{mem_pct}"
        top_lines.append(entry)

    if not top_lines:
        return ["(no process data)"]
    return top_lines

# --- main loop ---
print("Starting system monitor loop. Press Ctrl+C to exit.")
rotation_start = time.monotonic()
while True:
    try:
        # canvas clear
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        elapsed = int(time.monotonic() - rotation_start)
        screen = (elapsed // 5) % 4

        # Screen 1: original system summary
        if screen == 0:
            ip_text = get_ip_address()
            cpu_temp_text = get_cpu_temperature()
            cpu_usage_text = get_cpu_usage()
            mem_usage_text = get_mem_usage()

            draw.text((0, 0), ip_text, font=font, fill=255)
            draw.text((0, 16), cpu_temp_text, font=font, fill=255)
            draw.text((0, 32), cpu_usage_text, font=font, fill=255)
            draw.text((0, 48), mem_usage_text, font=font, fill=255)

        # Screen 2: host, uptime, available and total RAM (GB)
        elif screen == 1:
            draw.text((0, 0), get_hostname(), font=font, fill=255)
            draw.text((0, 16), get_uptime(), font=font, fill=255)
            draw.text((0, 32), get_ram_available_gb(), font=font, fill=255)
            draw.text((0, 48), get_ram_total_gb(), font=font, fill=255)

        # Screen 3: top 4 by CPU
        elif screen == 2:
            draw.text((0, 0), "Top CPU", font=small_font, fill=255)
            for idx, line in enumerate(get_top_processes("cpu")):
                draw.text((0, 12 + idx * 13), line, font=small_font, fill=255)

        # Screen 4: top 4 by MEM
        else:
            draw.text((0, 0), "Top MEM", font=small_font, fill=255)
            for idx, line in enumerate(get_top_processes("mem")):
                draw.text((0, 12 + idx * 13), line, font=small_font, fill=255)

        # display
        display.image(image)
        display.show()

        time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting. Clearing display.")
        display.fill(0)
        display.show()
        break
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(5)
