//
// Bit fiddling example in C
//
// Copyright (C) <2022>, Gary Sims
// All rights reserved.
//
// License: BSD 2-Clause "Simplified" License / SPDX: BSD-2-Clause

// Reference tables for AND, OR, XOR
// AND
// a	b	a AND b
// 0	0	    0
// 0	1	    0
// 1	0	    0
// 1	1	    1
//
// OR
// a	b	a OR b
// 0	0	    0
// 0	1	    1
// 1	0	    1
// 1	1	    1
//
// XOR
// a	b	a XOR b
// 0	0	    0
// 0	1	    1
// 1	0	    1
// 1	1	    0

// Bit numbering
// 7 6 5 4 3 2 1 0

#include <stdio.h>

// Print a binary number
// i will start as 1000000, then 01000000, 00100000, until 00000000 when the loop with end
// Remember that in "expression ? statement1 : statement2". Any non 0 value will be considered as true, and so execute statement1
void print_8bin(unsigned char n) {
  unsigned char i;
  for (i = 1 << 7; i > 0; i = i >> 1) {
    (n & i) ? printf("1") : printf("0");
  }
}

// Set bit n of the byte by using the bitwise OR operator (|)
void set_bit(unsigned char *byte, unsigned char n) {
    *byte |= 1 << n;
}

// Get the value of bit n of the byte
unsigned char get_bit(unsigned char byte, unsigned char n) {
  return (byte >> n) & 1;
}

// Toggle bit n of the byte by using the bitwise XOR operator (^)
void toggle_bit(unsigned char *byte, int n) {
    *byte ^= 1 << n;
}

// Swap two numbers using XOR
// Remember that x ^ x = 0 or x ^ y ^ y = x
void swap_using_xor(unsigned char *x, unsigned char *y) {
  *x = *x ^ *y;     // x = x ^ y
  *y = *x ^ *y;     // y = (x ^ y) ^ y which means now y = original x
  *x = *x ^ *y;     // x = (x ^ y) ^ y but since y is now original x then
                    // it is really x = (x ^ y) ^ x, so x = original y
}

int main() {
  unsigned char byte = 0;

  set_bit(&byte, 7);
  print_8bin(byte);
  printf("\n");

  unsigned char b = get_bit(byte, 7);
  printf("%d\n", b);

  toggle_bit(&byte, 7);
  print_8bin(byte);
  printf("\n");

  unsigned char m = 17;
  unsigned char n = 99;
  printf("m is %d, n is %d\n", m, n);
  swap_using_xor(&m, &n);
  printf("m is %d, n is %d\n", m, n);
  return 0;
}