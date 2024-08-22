#include <stdio.h>
#include "pico/stdlib.h"
#include <time.h>
#include <stdlib.h>

#define MEMBASH_SZ 196 * 1024
#define ITERS 2048

int main()
{
    stdio_init_all();
    int iters = 0;

    printf("Init...\n");
    sleep_ms(5000);
    printf("Start...\n");

#if PICO_RP2350
    printf("I'm an RP2350 ");
#ifdef __riscv
    printf("running RISC-V\n");
#else
    printf("running ARM\n");
#endif
#else
    printf("I'm an RP2040\n");
#endif

    clock_t startt = clock();
    printf("8-bit started at %u\n", startt);

    unsigned char *membash_buffer = malloc(MEMBASH_SZ);
    if (membash_buffer == NULL)
    {
        printf("Malloc failed for %d bytes\n", MEMBASH_SZ);
        while (true)
        {
            sleep_ms(1000);
        }
    }

    //
    // 8-bit
    //
    for (iters = 0; iters < ITERS; iters++)
    {
        // Fill 8 bit
        unsigned char *p8 = membash_buffer;
        for (int i = 0; i < MEMBASH_SZ; i++)
        {
            *p8 = (unsigned char)(i & 0xFF);
            p8++;
        }

        // XOR everything with 0x42
        p8 = membash_buffer;
        for (int i = 0; i < MEMBASH_SZ; i++)
        {
            *p8 = *p8 ^ 0x42;
            p8++;
        }
    }
    clock_t endt = clock();
    printf("8-bit ended at %u\n", endt);
    printf("%d\n", (int)(endt - startt));


    //
    // 32-bit
    //
    startt = clock();
    printf("32-bit started at %u\n", startt);

    for (iters = 0; iters < ITERS; iters++)
    {
        // Fill 32 bit
        uint32_t *p32 = (uint32_t *) membash_buffer;
        for (unsigned int i = 0; i < MEMBASH_SZ/4; i++)
        {
            *p32 = (uint32_t)(i & 0xFFFFFFFF);
            p32++;
        }

        // XOR everything with 0x42
        p32 = (uint32_t *) membash_buffer;
        for (unsigned int i = 0; i < MEMBASH_SZ/4; i++)
        {
            *p32 = *p32 ^ 0x42424242;
            p32++;
        }
    }

    endt = clock();
    printf("32-bit ended at %u\n", endt);
    printf("%d\n", (int)(endt - startt));

    while (true)
    {
        sleep_ms(1000);
    }
}
