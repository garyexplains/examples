# Copyright (C) 2018-2022 Gary Sims
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# vCPU emulator

from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from vDISASM import disassemble # Include the disassembler for debugging

# Pin 25 on Pico is the built-in LED
led = Pin(25, Pin.OUT)

# Runtime flags
DEBUG = False
INTERACTIVE = False
DUMPDISPLAY = True

# Registers
# R0 to R7
# R8 to R15 are reserved

registers = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
pc = 0
mainmem = bytearray(0x10000) # 64K, last 1K (starting at 0xFBFF) for char display
flag_z = 0
flag_gt = 0
flag_lt = 0
DISPLAY_START_ADDRESS = 0xFBFF

# Init OLED display for PICO
# This demo uses a 128x32 OLED I2C display
# Driven by the SSD1306.
oled_width = 128 # Pixels
oled_height = 32 # Pixels
i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(oled_width, oled_height, i2c)

# OLED DISPLAY STUFF ON PICO
# Text display. Three lines, 16 characters each.
# 48 Bytes in total.
# Lots of potential for bigger displays.
# Graphic modes and text modes possible, etc.
# This demo uses a 128x32 OLED I2C display
# Driven by the SSD1306.
def dumpdisplaytooled():
    oled.fill(0)
    x = 0
    y = 0
    i = DISPLAY_START_ADDRESS
    j = DISPLAY_START_ADDRESS + 48
    while i < j:
        line = ""
        while x < 16:
            c = mainmem[i] & 0xFF
            if c < 32: # non-printable characters
                line = line + " "
            else:
                line = line + str(chr(c))
            x = x + 1
            i = i + 1
        oled.text(line, 0, y)
        x = 0
        y = y + 12
    oled.show()

# Print a numnber in 4 digit hex
def hexstr(n):
    return "{:04x}".format(n)

# Debug display to standard output
# Assume 16x3 char display, memory mapped at 0xFBFF
# Just like the OLED display.
def dumpdisplay():
    print("----------------")
    x = 0
    i = DISPLAY_START_ADDRESS
    j = DISPLAY_START_ADDRESS + 48
    while i < j:
        line = ""
        while x < 16:
            c = mainmem[i] & 0xFF
            if c < 32: # non-printable characters
                line = line + " "
            else:
                line = line + str(chr(c))
            x = x + 1
            i = i + 1
        print(line)
        x = 0
    print("----------------")

# Output the program counter, the machine code at the program counter,
# and the registers and flags.
def dumpregisters(o, d):
    print("PC: " + str(pc-4) + " Op:0x" + "{:04x}".format(o) + " Data:0x" + "{:04x}".format(d))
    print("CODE: " + disassemble(o, d))
    print("R0:" + hexstr(registers[0]) + "  R1:" + hexstr(registers[1]) + "  R2:" + hexstr(registers[2]) + "  R3:" + hexstr(registers[3]) + "  R4:" + hexstr(registers[4]) + "  R5:" + hexstr(registers[5]) + "  R6:" + hexstr(registers[6]) + "  R7:" + hexstr(registers[7]))
    print("Z:" + str(flag_z) + "  GT:" + str(flag_gt) + "  LT:" + str(flag_lt))

# DECODE
# Opcodes can be found here:
# https://github.com/garyexplains/examples/blob/master/My%20CPU%20ISA%20design%20opcodes%20-%20Sheet1.pdf
#
# All instructions are 4 bytes, eg:
# LD R1, 0xabcd - 00 R1 AB CD
# The opcode is the first byte, the register (if used) is the second byte.
# The last two bytes are the data or address (depending on the opcode)
#
def decode(pc, opcode, data):
    global flag_z, flag_gt, flag_lt
    global mainmem
    global registers

    op = opcode >> 8
    mode = opcode & 0xFF
    if op == 0x00: #LD value
        # Need to sanity check RR
        # to avoid out-of-bounds access
        registers[mode] = data
    elif op == 0x01: #LD from register
        # Checks?
        registers[mode] = registers[data & 0xFF]
    elif op == 0x02: #LD from memory
        # Checks?
        registers[mode] = mainmem[data]
    elif op == 0x10: #ST to memory from reg
        # Checks?
        mainmem[data] = registers[mode]
    elif op == 0x11: #STL to memory from reg
        # Checks?
        mainmem[data] = registers[mode] & 0xFF
    elif op == 0x12: #STH to memory from reg
        # Checks?
        mainmem[data] = registers[mode] >> 8
    elif op == 0x13: #ST 16 bit write to addr in second reg
        # Checks?
        mainmem[registers[data]] = registers[mode]
    elif op == 0x14: #STL write to addr in second reg
        # Checks?
        mainmem[registers[data]] = registers[mode] & 0xFF
    elif op == 0x15: #STH write to addr in second reg
        # Checks?
        mainmem[registers[data]] = registers[mode] >> 8
    elif op == 0x20: # CMP R1, R2
        # Checks?
        if registers[mode] == registers[data & 0xFF]:
            flag_z = 1
            flag_gt = 0
            flag_lt = 0
        elif registers[mode] > registers[data & 0xFF]:
                        flag_z = 0
                        flag_gt = 1
                        flag_lt = 0
        elif registers[mode] < registers[data & 0xFF]:
                        flag_z = 0
                        flag_gt = 0
                        flag_lt = 1
    elif op == 0x21: # CMP R1, 0xABCD
        # Checks?
        if registers[mode] == data:
            flag_z = 1
            flag_gt = 0
            flag_lt = 0
        elif registers[mode] > data:
                        flag_z = 0
                        flag_gt = 1
                        flag_lt = 0
        elif registers[mode] < data:
                        flag_z = 0
                        flag_gt = 0
                        flag_lt = 1
    elif op == 0x30: # BEQ label - 30 00 AB CD # If Z flag is set
        if flag_z == 1:
            pc = data
    elif op == 0x31: # BGT label - 31 00 AB CD # If GT flag is set
        if flag_gt == 1:
            pc = data
    elif op == 0x32: # BLT label - 32 00 AB CD # If LT flag is set
        if flag_lt == 1:
            pc = data
    elif op == 0x33: # BRA label
            pc = data
    elif op == 0x40: # ADD R1, 0xABCD - 40 RR AB CD
        # Checks?
        registers[mode] = (registers[mode] + data) & 0xFFFF
    elif op == 0x41: # SUB R1, 0xABCD - 41 RR AB CD
        # Checks?
        registers[mode] = (registers[mode] - data) & 0xFFFF
    elif op == 0x42: # ADD R1, R2 - 40 RR 00 RR
        # Checks?
        registers[mode] = (registers[mode] + registers[data & 0xFF]) & 0xFFFF
    elif op == 0x43: # SUB R1, R2 - 41 RR AB CD
        # Checks?
        registers[mode] = (registers[mode] - registers[data & 0xFF]) & 0xFFFF
    elif op == 0xFE: # HALT - Jump to end of memory
            pc = 0xFFFF
    elif op != 0xFF: # NOOP
        # ERROR
        print("ILLEGAL OP CODE")
        exit(0)

    return pc

#
# MAIN
#

# Hard coded to read from rom.bin
with open("rom.bin", mode='rb') as file: # b is important -> binary
    code = bytearray(file.read())

endofprog = len(code)

# Copy code into main memory
i = 0
while i < endofprog:
    mainmem[i] = code[i]
    i = i + 1

cmd = 's' # when in interactive mode
refreshdisplay=0

while pc < endofprog:
    # Read next 4 bytes
    inst1 =  mainmem[pc] << 8 | mainmem[pc+1]
    pc = pc + 2
    inst2 =  mainmem[pc] << 8 | mainmem[pc+1]
    pc = pc + 2

    if DEBUG == True or INTERACTIVE == True:
        dumpregisters(inst1, inst2)
        dumpdisplay()
    elif DUMPDISPLAY == True:
        dumpdisplay()
        
    # Update OLED display, regardless of DEBUG etc flags
    # But not every cycle, otherwise too much time is taken
    # just to update the display
    refreshdisplay = (refreshdisplay + 1) % 3
    if refreshdisplay == 0:
        led.toggle()
        dumpdisplaytooled()
    
    # If in interactive mode then allow for single stepping etc
    # More interactive commands could be added here
    if INTERACTIVE == True:
        if cmd == 's':
            cmd = input("[S]tep")
            if cmd == '':
                cmd = 's'

    # Decode the instructions retrieved previously
    # The program counter is returned always
    # to handle branches etc.
    pc = decode(pc, inst1, inst2)