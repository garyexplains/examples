// Copyright (C) <2024>, Gary Sims
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//   list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright notice,
//   this list of conditions and the following disclaimer in the documentation
//   and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
// ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//

#include <stdio.h>
#include <stdint.h>
#include <string.h>

// ------------------------------

#define FIXED_FACTOR 100000000000000000
#define FIXED_PLACES 17

void print_fixed_point_r(uint64_t n, int i) {
    uint64_t num = n;
    int c;

    c = num % 10;
    num = num / 10;
    if((i<FIXED_PLACES) || (num>0))
        print_fixed_point_r(num, i + 1);
    if (i == FIXED_PLACES) {
        if(num==0)
            printf("0");
        printf(".");
    }
    printf("%c", c + '0');
}

void print_fixed_point(uint64_t n) {
    print_fixed_point_r(n, 1);
}

uint64_t set_fixed_point_int(uint64_t n) {
    return n * FIXED_FACTOR;
}

// decimal expansion for positive fixed point rational numbers
uint64_t fixed_point_dec_expansion(uint64_t dividend, uint64_t divisor) {
    uint64_t result = 0;
    if (divisor == 0)
        return 0;

    uint64_t quotient = dividend / divisor;
    result = result + quotient;
    result = result * 10;

    // Start calculating the fractional part
    uint64_t remainder = dividend % divisor;
    
    for (int i = 0; i < FIXED_PLACES-1; i++) {
        // Multiply the remainder by 10 for the next digit
        remainder = remainder * 10;
        int digit = remainder / divisor;
        result = result + digit;
        result = result * 10;
        remainder = remainder % divisor;
    }
    return result;
}
// ---------------------------------

void print_bin32_fraction_expansion(uint32_t frac) {
    uint32_t p = frac;
    uint64_t f = 2;

    printf("1 ");
    for(int i=0;i<23;i++) {
            if( (p & 0x400000) != 0) {
                printf(" + ");
                print_fixed_point(fixed_point_dec_expansion(1, f));
            }
            p = (p << 1);
            f = f << 1;
    }
    printf("\n");
}


uint64_t calc_bin32_fraction_fixed(uint32_t frac) {
    uint32_t p = frac;
    uint64_t f = 2;
    uint64_t fraction = set_fixed_point_int(1);

    for(int i=0;i<23;i++) {
            if( (p & 0x400000) != 0) {
                fraction = fraction + fixed_point_dec_expansion(1, f);
            }
            p = p << 1;
            f = f << 1;
    }
    return fraction;
}

uint64_t calc_bin32_expo_fixed(uint32_t e) {
    int32_t shift = e - 127;
    uint64_t expo = set_fixed_point_int(1);

    if(shift > 0) {
        for(int i=0;i<shift;i++) {
            expo = expo << 1;
        }
    } else {
        int f = 1;
        for(int i=0;i<shift*-1;i++) {
            f = f << 1;
        }
        expo = fixed_point_dec_expansion(1, f);
    }
    return expo;
}

uint64_t calc_expo_fixed(uint64_t f, int e) {

    if(e > 0) {
        for(int i=0;i<e;i++) {
            f = f << 1;
        }
    } else {
        for(int i=0;i<e*-1;i++) {
            f = f >> 1;
        }
    }
    return f;
}

void decode_binary32(float f) {
    uint32_t p;
    uint32_t sign;
    uint32_t expo=0;
    uint32_t fraction=0;

    printf("\n%f decodes to:\nBinary Representation: ", f);
    memcpy(&p, &f, 4);
    sign = (p & 0x80000000);
    printf("%c", (sign == 0) ? '0' : '1');
    p = (p << 1);

    for(int i=0;i<8;i++) {
        if( (p & 0x80000000) == 0) {
            printf("0");
        } else {
            printf("1");
            expo = expo | 0x1;
        }
        expo = (expo << 1);
        p = (p << 1);
    }
    expo = (expo >> 1);

   for(int i=0;i<23;i++) {
        if( (p & 0x80000000) == 0) {
            printf("0");
        } else {
            printf("1");
            fraction = fraction | 0x1;
        }
        fraction = (fraction << 1);
        p = (p << 1);
    }
    fraction = (fraction >> 1);

    printf("\nSign: %c\n", (sign == 0) ? '+' : '-');
    printf("Expo: %d\n", (int) (expo - 127));
    printf("Frac: ");
    print_bin32_fraction_expansion(fraction);
    printf("Fixed point fraction: ");
    print_fixed_point(calc_bin32_fraction_fixed(fraction));
    printf("\n");
    printf("Fixed point expo: ");
    print_fixed_point(calc_bin32_expo_fixed(expo));
    printf("\n");
    printf("Fixed point reconstructed float is: ");
    print_fixed_point(calc_expo_fixed(calc_bin32_fraction_fixed(fraction), (int) (expo - 127)));
    printf("\n");
}

void main(void) {
    decode_binary32((float) 0.15625);
    decode_binary32((float) 0.12);
    decode_binary32((float) 12.334);
    decode_binary32((float) 121.009);
}