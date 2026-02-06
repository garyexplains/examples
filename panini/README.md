# Intro
Python script to show four pages of system information on the OLED display of the Panini case for the Jetson Orin Nano.

# System information
It rotates through 4 OLED screens every 5 seconds in a loop:
1. Shows the IP address (first one from Wi-Fi → Ethernet → others), CPU temp, CPU usage %, RAM usage %.
2. hostname, uptime, available RAM (GB), total RAM (GB)
3. Top 4 processes sorted by CPU usage
4. Top 4 processes sorted by MEM usage.

And just for fun, there are also two surprise screens (a rotating cube and bouncing balls) which appear randomly, but not often. 

# Photos
![Panini OLED IP address etc](panini-oled-photos/panini_oled_sysinfo_1.jpg?raw=true)
![Panini OLED hostname etc](panini-oled-photos/panini_oled_sysinfo_2.jpg?raw=true)
![Panini OLED CPU usage etc](panini-oled-photos/panini_oled_sysinfo_3.jpg?raw=true)
![Panini OLED MEM usage etc](panini-oled-photos/panini_oled_sysinfo_4.jpg?raw=true)
![Panini OLED 3D cube etc](panini-oled-photos/panini_oled_sysinfo_cube.jpg?raw=true)
![Panini OLED balls etc](panini-oled-photos/panini_oled_sysinfo_ball.jpg?raw=true)

# References
https://roboco.tw/blog/panini-oled

https://blog.cavedu.com/2025/12/22/orinnano_panini/

https://roboco.tw/paniniwh

# systemd
Create a systemd service (to allow the OLED program to start automatically on every boot).

If the OLED displays correctly after testing `python3 oled_sysinfo.py`, you can create a service that starts automatically at boot

Create the service file: `sudo nano /etc/systemd/system/oled.service` and paste the following content:

```
[Unit]

Description=Panini OLED system info

After=network.target

[Service]

Type=simple

ExecStart=/usr/bin/python3 /home/jetson/oled_sysinfo.py

WorkingDirectory=/home/jetson

StandardOutput=journal

StandardError=journal

Restart=always

User=jetson

[Install]

WantedBy=multi-user.target
```

If your username is not __jetson__, please change `User=jetson` to your actual username and modify `ExecStart` and `WorkingDirectory` accordingly. 

### Enable the service
Reload systemd:
```
sudo systemctl daemon-reexec
```

### Enable the service (automatic startup on boot)
```
sudo systemctl enable oled.service
```

### Start the service immediately
```
sudo systemctl start oled.service
```

### Check the status
Use the following command to check if the service status is normal
```
systemctl status oled.service
```
