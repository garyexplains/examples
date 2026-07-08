#!/usr/bin/env python3
"""
Linux Machine Fingerprint Collector (No Root Required)
For Internet Privacy class demonstration.
"""

import os
import socket
import uuid
import subprocess
import re
import json
from datetime import datetime


def run_command(cmd, timeout=5):
    """Run shell command safely."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else ""
    except:
        return ""


def get_hostname():
    return socket.gethostname()


def get_machine_id():
    """One of the strongest persistent identifiers on Linux."""
    paths = ['/etc/machine-id', '/var/lib/dbus/machine-id']
    for path in paths:
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except:
            continue
    return ""


def get_mac_addresses():
    """MAC addresses from network interfaces (no root needed)."""
    macs = {}
    
    # Preferred method: /sys filesystem (fully user-readable)
    try:
        for iface in os.listdir('/sys/class/net/'):
            if iface in ('lo', 'docker', 'veth', 'br-'):
                continue
            addr_path = f'/sys/class/net/{iface}/address'
            if os.path.exists(addr_path):
                with open(addr_path, 'r') as f:
                    mac = f.read().strip()
                    if mac and mac != "00:00:00:00:00:00":
                        macs[iface] = mac
    except:
        pass

    # Fallback using ip command
    if not macs:
        output = run_command("ip -o link show | awk '{print $2, $NF}'")
        for line in output.splitlines():
            if 'link/ether' in line or ':' in line:
                parts = line.split()
                if len(parts) >= 2:
                    iface = parts[0].rstrip(':')
                    mac = parts[-1]
                    if iface != 'lo':
                        macs[iface] = mac
    
    return macs


def get_system_uuids():
    """Various stable UUIDs."""
    uuids = {}
    
    # Boot ID (changes on reboot)
    try:
        with open('/proc/sys/kernel/random/boot_id', 'r') as f:
            uuids['boot_id'] = f.read().strip()
    except:
        pass

    # Product UUID (sometimes readable without root)
    try:
        with open('/sys/class/dmi/id/product_uuid', 'r') as f:
            uuids['product_uuid'] = f.read().strip()
    except:
        pass

    # Board serial (often restricted, but try anyway)
    try:
        with open('/sys/class/dmi/id/board_serial', 'r') as f:
            val = f.read().strip()
            if val and val != "0" and not val.startswith("To be filled"):
                uuids['board_serial'] = val
    except:
        pass

    return uuids


def get_disk_info():
    """Disk identifiers (many visible without root)."""
    disks = {}
    
    # lsblk is usually allowed for regular users
    output = run_command("lsblk -o NAME,SERIAL,UUID,MODEL,TRAN -d 2>/dev/null")
    if output:
        disks['lsblk'] = output.splitlines()[:10]  # limit output
    
    # Try udevadm for main drive (no sudo needed in most cases)
    for dev in ['sda', 'nvme0n1', 'vda']:
        output = run_command(f"udevadm info --query=property --name=/dev/{dev} 2>/dev/null | grep -E 'ID_SERIAL|ID_MODEL'")
        if output:
            disks[dev] = output
            break
    
    return disks


def get_cpu_info():
    """Basic CPU information."""
    info = {}
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if ':' in line:
                    key, val = [x.strip() for x in line.split(':', 1)]
                    if key in ['model name', 'vendor_id', 'cpu cores', 'siblings', 'cache size']:
                        info[key] = val
                        if len(info) >= 6:  # limit
                            break
    except:
        pass
    return info


def get_user_info():
    return {
        'username': os.getenv('USER') or os.getenv('LOGNAME'),
        'uid': os.getuid(),
        'home': os.getenv('HOME'),
        'shell': os.getenv('SHELL'),
        'display': os.getenv('DISPLAY') or os.getenv('WAYLAND_DISPLAY'),
    }


def main():
    fingerprint = {
        "timestamp": datetime.now().isoformat(),
        "hostname": get_hostname(),
        "machine_id": get_machine_id(),
        "mac_addresses": get_mac_addresses(),
        "system_uuids": get_system_uuids(),
        "disk_info": get_disk_info(),
        "cpu_info": get_cpu_info(),
        "user_info": get_user_info(),
        "python_uuid": str(uuid.uuid1()),   # Often includes MAC address
    }

    print("=== Linux Machine Fingerprint (No Root) ===\n")
    print(json.dumps(fingerprint, indent=2))

    print("\n" + "="*70)
    print("Key Privacy Points:")
    print("• /etc/machine-id is extremely stable and widely used")
    print("• MAC addresses are easily accessible")
    print("• product_uuid and boot_id provide additional entropy")
    print("• Even without root, a program can build a strong fingerprint")
    print("• Many applications and trackers combine this with browser data")


if __name__ == "__main__":
    main()
