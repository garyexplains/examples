#!/usr/bin/python
#Copyright (C) 2018, 2019, Gary Sims
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#
#1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

#
# Usage:
# vASM.py assemblyfile.asm
#
# It will produce a file called rom.bin. This is hard coded at the moment.
#

#
# Notes:
# This is very easy to break. There should be much more error checking etc
#
# The code can be refactored etc, but I have deliberately left it reptitive and verbose.
#
# Did I mention that this is very easy to break. There should be much more error checking!
#

import sys
import re

labels = {}

def parselabels(fn):
	linenum = 0
	with open(sys.argv[1]) as f:
		for line in f:
			line = line.replace('\n', '').replace('\r', '')
			if line[0]=='#':
				# Note that linenum won't be increased, so the address
				# remains correct
				continue

			if line[0]=='.':
				labels[line[1:]] = linenum*4
				print "Label: " + line[1:] + " @ " + format(linenum*4, '#04x')
			else:
				linenum = linenum + 1

def zerobin(fn):
	with open("rom.bin", "wb") as binary_file:
		binary_file.close()

def writebin(fn, b):
	with open("rom.bin", "ab") as binary_file:
        	binary_file.write(bytearray(b))

if len(sys.argv) != 2:
	print "Usage: vASM file.asm"
	sys.exit()

zerobin("rom.bin")

parselabels(sys.argv[1])

with open(sys.argv[1]) as f:
	for line in f:

		# Ignore labels
		if line[0]=='.':
			continue

		# Ignore comments
		if line[0]=='#':
			continue

		line = line.replace('\n', '').replace('\r', '')
		tok = re.split(r'[, ]',line)

		if '' in tok:
			tok.remove('')

		print str(tok)
		
		if tok[0].upper() == "LD":
			r = int(tok[1].upper()[1])
			if r >= 0 and r <= 7:
				a1 = tok[2]
				if a1[0] == '$':
					# Address
					addr = int(a1[1:], 0)
					b = [0x02, r, addr >> 8, addr & 0xFF]
					writebin("rom.bin", b)
				elif a1[0] == 'R':
					# Register
					r2 = int(a1[1:], 0)
					b = [0x01, r, 0, r2]
					writebin("rom.bin", b)
				else:
					# Value
					v = int(a1, 0)
					b = [0x00, r, v >> 8,  v & 0xFF]
					writebin("rom.bin", b)
			else:
				print "Invalid register name"
				print tok[1].upper()
				sys.exit()
		elif tok[0].upper() == "ST":
			r = int(tok[1].upper()[1])
			if r >= 0 and r <= 7:
				a1 = tok[2]
				if a1[0] == '$':
					# Address
					addr = int(a1[1:], 0)
					b = [0x10, r, addr >> 8, addr & 0xFF]
					writebin("rom.bin", b)
				elif a1[0] == 'R':
					# Address in register
					r2 = int(a1[1:], 0)
					b = [0x13, r, 0, r2]
					writebin("rom.bin", b)
				else:
					print "Invalid mode"
					print line
					sys.exit()
			else:
				print "Invalid register name"
				print tok[1].upper()
				sys.exit()
		elif tok[0].upper() == "STL":
			r = int(tok[1].upper()[1])
			if r >= 0 and r <= 7:
				a1 = tok[2]
				if a1[0] == '$':
					# Address
					addr = int(a1[1:], 0)
					b = [0x11, r, addr >> 8, addr & 0xFF]
					writebin("rom.bin", b)
				elif a1[0] == 'R':
					# Address in register
					r2 = int(a1[1:], 0)
					b = [0x14, r, 0, r2]
					writebin("rom.bin", b)
				else:
					print "Invalid mode"
					print line
					sys.exit()
			else:
				print "Invalid register name"
				print tok[1].upper()
				sys.exit()
		elif tok[0].upper() == "STH":
			r = int(tok[1].upper()[1])
			if r >= 0 and r <= 7:
				a1 = tok[2]
				if a1[0] == '$':
					# Address
					addr = int(a1[1:], 0)
					b = [0x12, r, addr >> 8, addr & 0xFF]
					writebin("rom.bin", b)
				elif a1[0] == 'R':
					# Address in register
					r2 = int(a1[1:], 0)
					b = [0x14, r, 0, r2]
					writebin("rom.bin", b)
				else:
					print "Invalid mode"
					print line
					sys.exit()
			else:
				print "Invalid register name"
				print tok[1].upper()
				sys.exit()
		elif tok[0].upper() == "CMP":
			r = int(tok[1].upper()[1])
			if r >= 0 and r <= 7:
				a1 = tok[2]
				if a1[0] == 'R':
					# Register
					r2 = int(a1[1:], 0)
					b = [0x20, r, 0, r2]
					writebin("rom.bin", b)
				else:
					# Value
					v = int(a1, 0)
					b = [0x21, r, v >> 8,  v & 0xFF]
					writebin("rom.bin", b)
			else:
				print "Invalid register name"
				print tok[1].upper()
				sys.exit()
		elif tok[0].upper() == "BEQ":
			if tok[1] in labels:
				addr = labels[tok[1]]
				v = addr
				b = [0x30, 0, v >> 8,  v & 0xFF]
				writebin("rom.bin", b)
			else:
				print "Unknown label"
				print tok[1]
				sys.exit()
		elif tok[0].upper() == "BGT":
			if tok[1] in labels:
				addr = labels[tok[1]]
				v = addr
				b = [0x31, 0, v >> 8,  v & 0xFF]
				writebin("rom.bin", b)
			else:
				print "Unknown label"
				print tok[1]
				sys.exit()
		elif tok[0].upper() == "BLT":
			if tok[1] in labels:
				addr = labels[tok[1]]
				v = addr
				b = [0x32, 0, v >> 8,  v & 0xFF]
				writebin("rom.bin", b)
			else:
				print "Unknown label"
				print tok[1]
				sys.exit()
		elif tok[0].upper() == "BRA":
			if tok[1] in labels:
				addr = labels[tok[1]]
				v = addr
				b = [0x33, 0, v >> 8,  v & 0xFF]
				writebin("rom.bin", b)
			else:
				print "Unknown label"
				print tok[1]
				sys.exit()
		elif tok[0].upper() == "ADD":
			r = int(tok[1].upper()[1])
			if r >= 0 and r <= 7:
				a1 = tok[2]
				if a1[0] == 'R':
					# Register
					r2 = int(a1[1:], 0)
					b = [0x42, r, 0, r2]
					writebin("rom.bin", b)
				else:
					# Value
					v = int(a1, 0)
					b = [0x40, r, v >> 8,  v & 0xFF]
					writebin("rom.bin", b)
			else:
				print "Invalid register name"
				print tok[1].upper()
				sys.exit()
		elif tok[0].upper() == "SUB":
			r = int(tok[1].upper()[1])
			if r >= 0 and r <= 7:
				a1 = tok[2]
				if a1[0] == 'R':
					# Register
					r2 = int(a1[1:], 0)
					b = [0x43, r, 0, r2]
					writebin("rom.bin", b)
				else:
					# Value
					v = int(a1, 0)
					b = [0x41, r, v >> 8,  v & 0xFF]
					writebin("rom.bin", b)
			else:
				print "Invalid register name"
				print tok[1].upper()
				sys.exit()
		elif tok[0].upper() == "HALT":
				b = [0xFE, 0xFE, 0xFF, 0xFF]
				writebin("rom.bin", b)
		elif tok[0].upper() == "NOOP":
				b = [0xFF, 0xFF, 0xFF, 0xFF]
				writebin("rom.bin", b)
		else:
			print "Unknown operand"
			print tok[0]
			sys.exit()
