# How to use a Nokia 5110 LCD Display with a Raspberry Pi

Installation instructions
-------------------------

Note: This snippet has been borrowed from: https://github.com/rm-hull/luma.examples

Assuming you are using a Raspberry Pi (running Debian Jessie or newer), follow the pre-requisites &
instructions in the above repositories to wire up your display, then from a command-line::
```
  $ sudo usermod -a -G i2c,spi,gpio pi
  $ sudo apt install python3-dev python3-pip libfreetype6-dev libjpeg-dev build-essential
  $ sudo apt install libsdl-dev libportmidi-dev libsdl-ttf2.0-dev libsdl-mixer1.2-dev libsdl-image1.2-dev
```
Log out and in again and clone this repository::
```
  $ git clone https://github.com/rm-hull/luma.examples.git
  $ cd luma.examples
```
Finally, install the luma libraries using::
```
  $ sudo -H pip install -e .
```

Luma.LCD
-------------------------

- Source:https://github.com/rm-hull/luma.lcd
- Documentation: https://luma-core.readthedocs.io/en/latest/intro.html

Wriring
-------------------------
![Wiring diagram](https://github.com/garyexplains/examples/raw/master/Connect%20Nokia%205110%20display%20PCD8544%20to%20Raspberry%20Pi.png)
