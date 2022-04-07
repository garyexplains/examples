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

# History
# March 2022 - Updated for python3

#
# Usage:
# vDISASM.py

# It will disassemble rom.bin. This is hard coded at the moment.

# Opcodes can also be found here:
# https://github.com/garyexplains/examples/blob/master/My%20CPU%20ISA%20design%20opcodes%20-%20Sheet1.pdf
# 
# LD R1, 0xabcd - 00 RR AB CD
# LD R1, R2 - 01 RR 00 RR
# LD R1, $0x100 - 02 RR 01 00 # 16 bit read into reg
#
# ST R1, $0x100 - 10 RR 01 00 # 16 bit write
# STL R1, $0x100 - 11 RR 01 00 # lower 8 bits of reg
# STH R1, $0x100 - 12 RR 01 00 # upper 8 bits of reg
# ST R1, R2 - 13 RR 00 R2 # 16 bit write to addr in R2
# STL R1, R2 - 14 RR 00 R2 # lower 8 bits of R1 to addr in R2
# STH R1, R2 - 15 RR 00 R2 # upper 8 bits of R1 to addr in R2
#
# CMP R1, R2 - 20 RR 00 RR # Compare R1 and R2
# CMP R1, 0xabcd - 21 RR ABCD # Compare R1 to 0xabcd
#
# BEQ label - 30 00 AB CD # If Z flag is set
# BGT label - 31 00 AB CD # If GT flag is set
# BLT label - 32 00 AB CD # If LT flag is set
# BRA label - 33 00 ABCD # Unconditional branch
#
# ADD R1, 0xabcd - 40 RR ABCD
# SUB R1, 0xabcd - 41 RR ABCD
# ADD R1, R2 - 42 RR 00 RR
# SUB R1, R2 - 43 RR 00 RR
#
# HALT - FE FE FF FF
# NOOP - FF FF FF FF

# INIT
import os
import struct

def hexstr(n):
    return "{:4x}".format(n)

def makeregisterstring(r):
    return "R" + str(r)

def disassemble(opcode, data):
    disasm = ""
    op = opcode >> 8
    mode = opcode & 0xFF
    if op == 0x00: #LD value
        disasm = disasm + "LD " + makeregisterstring(mode) + ", " + hexstr(data)
    elif op == 0x01: #LD from register
        disasm = disasm + "LD " + makeregisterstring(mode) + ", " + makeregisterstring(data & 0xFF)
    elif op == 0x02: #LD from memory
        # Checks?
        disasm = disasm + "LD " + makeregisterstring(mode) + ", $" + hexstr(data)
    elif op == 0x10: #ST to memory from reg
        disasm = disasm + "ST " + makeregisterstring(mode) + ", $" + hexstr(data)
    elif op == 0x11: #STL to memory from reg
        disasm = disasm + "STL " + makeregisterstring(mode) + ", $" + hexstr(data)
    elif op == 0x12: #STH to memory from reg
        disasm = disasm + "STH " + makeregisterstring(mode) + ", $" + hexstr(data)
    elif op == 0x13: #ST 16 bit write to addr in second reg
        disasm = disasm + "ST " + makeregisterstring(mode) + ", " + makeregisterstring(data & 0xFF)
    elif op == 0x14: #STL write to addr in second reg
        disasm = disasm + "STL " + makeregisterstring(mode) + ", " + makeregisterstring(data & 0xFF)
    elif op == 0x15: #STH write to addr in second reg
        disasm = disasm + "STH " + makeregisterstring(mode) + ", " + makeregisterstring(data & 0xFF)
    elif op == 0x20: # CMP R1, R2
        disasm = disasm + "CMP " + makeregisterstring(mode) + ", " + makeregisterstring(data & 0xFF)
    elif op == 0x21: # CMP R1, 0xABCD
        disasm = disasm + "CMP " + makeregisterstring(mode) + ", " + hexstr(data)
    elif op == 0x30: # BEQ label - 30 00 AB CD # If Z flag is set
        disasm = disasm + "BEQ $" + hexstr(data)
    elif op == 0x31: # BGT label - 31 00 AB CD # If GT flag is set
        disasm = disasm + "BGT $" + hexstr(data)
    elif op == 0x32: # BLT label - 32 00 AB CD # If LT flag is set
        disasm = disasm + "BLT $" + hexstr(data)
    elif op == 0x33: # BRA label
        disasm = disasm + "BRA $" + hexstr(data)
    elif op == 0x40: # ADD R1, 0xABCD - 40 RR AB CD
        disasm = disasm + "ADD " + makeregisterstring(mode) + ", " + hexstr(data)
    elif op == 0x41: # SUB R1, 0xABCD - 41 RR AB CD
        disasm = disasm + "SUB " + makeregisterstring(mode) + ", " + hexstr(data)
    elif op == 0x42: # ADD R1, R2 - 40 RR 00 RR
        disasm = disasm + "ADD " + makeregisterstring(mode) + ", " + makeregisterstring(data & 0xFF)
    elif op == 0x43: # SUB R1, R2 - 41 RR AB CD
        disasm = disasm + "SUB " + makeregisterstring(mode) + ", " + makeregisterstring(data & 0xFF)
    elif op == 0xFE: # HALT - Jump to end of memory
        disasm = disasm + "HALT"
    elif op == 0xFF: # NOOP
        disasm = disasm + "NOOP"
    else:
        disasm = disasm + "???"

    return disasm


#
# MAIN
#
if __name__ == '__main__':
    with open("rom.bin", mode='rb') as file: # b is important -> binary
        code = bytearray(file.read())

    endofprog = len(code)

    pc = 0
    while pc+2 < endofprog:
        inst1 =  code[pc] << 8 | code[pc+1]
        pc = pc + 2
        inst2 =  code[pc] << 8 | code[pc+1]
        pc = pc + 2

        nm =  disassemble(inst1, inst2)
        print(hexstr(pc - 4), nm)
