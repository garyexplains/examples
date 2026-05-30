#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

/*
 * Compile with:
 *   gcc -O3 -Wall -Wextra -std=c11 xor_layers.c -o xor_layers
 *
 * On Windows, the output name can be:
 *   gcc -O3 -Wall -Wextra -std=c11 xor_layers.c -o xor_layers.exe
 */

typedef struct {
    int exponent;
    int plus_one;
} Count;

static Count count_distinct(int n) {
    if (n < 1)
        return (Count){0, 0};

    int s = 0;
    int odd = n;
    while ((odd & 1) == 0) {
        s++;
        odd >>= 1;
    }

    if (odd == 1)
        return (Count){s, 1};

    int value = 1 % odd;
    int k = 0;
    do {
        value = (value * 2) % odd;
        k++;
    } while (value != 1 && value != odd - 1);

    int exponent = s + k;
    return (Count){exponent, 0};
}

static void print_decimal_count(Count count) {
    int exponent = count.exponent;
    int capacity = exponent / 3 + 2;
    uint8_t *digits = calloc((size_t)capacity, sizeof(uint8_t));
    if (!digits) {
        fprintf(stderr, "out of memory\n");
        exit(EXIT_FAILURE);
    }

    int len = 1;
    digits[0] = 1;

    for (int i = 0; i < exponent; i++) {
        int carry = 0;
        for (int j = 0; j < len; j++) {
            int v = digits[j] * 2 + carry;
            digits[j] = (uint8_t)(v % 10);
            carry = v / 10;
        }
        if (carry)
            digits[len++] = (uint8_t)carry;
    }

    if (count.plus_one) {
        int carry = 1;
        for (int j = 0; j < len && carry; j++) {
            int v = digits[j] + carry;
            digits[j] = (uint8_t)(v % 10);
            carry = v / 10;
        }
        if (carry)
            digits[len++] = (uint8_t)carry;
    }

    for (int i = len - 1; i >= 0; i--)
        putchar('0' + digits[i]);

    free(digits);
}

static void print_exponent_count(Count count) {
    printf("%d", count.exponent);
    if (count.plus_one)
        printf(" (+1)");
}

int main(int argc, char **argv) {
    int first = 3;
    int last = 1024;
    int exponent_only = 0;
    int numbers[2];
    int number_count = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-e") == 0) {
            exponent_only = 1;
        } else if (number_count < 2) {
            numbers[number_count++] = atoi(argv[i]);
        } else {
            fprintf(stderr, "usage: %s [-e] [first_n [last_n]]\n", argv[0]);
            return EXIT_FAILURE;
        }
    }

    if (number_count > 0) {
        first = numbers[0];
        last = first;
    }
    if (number_count > 1)
        last = numbers[1];
    if (first < 1 || last < first) {
        fprintf(stderr, "usage: %s [-e] [first_n [last_n]]\n", argv[0]);
        return EXIT_FAILURE;
    }

    printf("n\t%s\n", exponent_only ? "exponent" : "count");
    for (int n = first; n <= last; n++) {
        printf("%d\t", n);
        fflush(stdout);
        Count c = count_distinct(n);

        if (exponent_only)
            print_exponent_count(c);
        else
            print_decimal_count(c);
        putchar('\n');

        fflush(stdout);
    }
    return 0;
}
