# How to overclock a Raspberry Pi Zero 2 W
_This is a work in progress!_

## Measure the temperature

`vcgencmd measure_temp`

## Overclock settings
This will only work with active cooling (i.e. a fan).

Edit the file `/boot/config.txt` and add the following after the line which says `#uncomment to overclock the arm. 700 MHz is the default.`

```
arm_freq=1300
over_voltage=6
```

Save the file and reboot.

## Recovery
If your Pi doesn't boot due to some overzealous overclocking setting then press and hold the SHIFT key during the initial boot. This will override the settings on the `config.txt`
