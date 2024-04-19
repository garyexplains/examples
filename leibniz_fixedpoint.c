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

#define FIXED_FACTOR 1000000000000000000
#define FIXED_PLACES 18

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

#define ITERATIONS 10000000

void main(void) {
    uint64_t pi = set_fixed_point_int(1);

    int series = 3;
    for(int i=0;i<ITERATIONS;i++) {
        pi = pi - fixed_point_dec_expansion(1, series);
        pi = pi + fixed_point_dec_expansion(1, series+2);
        series = series + 4;
    }

    print_fixed_point(pi*4); printf("\n");
}