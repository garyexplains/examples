#include <stdio.h>
#include "pico/stdlib.h"
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>


#define boardSize 15
#define MAXN 31

int nqueens(int n)
{
    int q0, q1;
    int cols[MAXN], diagl[MAXN], diagr[MAXN], posibs[MAXN]; // Our backtracking 'stack'
    int num = 0;
    //
    // The top level is two fors, to save one bit of symmetry in the enumeration by forcing second queen to
    // be AFTER the first queen.
    //
    for (q0 = 0; q0 < n - 2; q0++)
    {
        for (q1 = q0 + 2; q1 < n; q1++)
        {
            int bit0 = 1 << q0;
            int bit1 = 1 << q1;
            int d = 0;                         // d is our depth in the backtrack stack
            cols[0] = bit0 | bit1 | (-1 << n); // The -1 here is used to fill all 'coloumn' bits after n ...
            diagl[0] = (bit0 << 1 | bit1) << 1;
            diagr[0] = (bit0 >> 1 | bit1) >> 1;

            //  The variable posib contains the bitmask of possibilities we still have to try in a given row ...
            int posib = ~(cols[0] | diagl[0] | diagr[0]);

            while (d >= 0)
            {
                while (posib)
                {
                    int bit = posib & -posib; // The standard trick for getting the rightmost bit in the mask
                    int ncols = cols[d] | bit;
                    int ndiagl = (diagl[d] | bit) << 1;
                    int ndiagr = (diagr[d] | bit) >> 1;
                    int nposib = ~(ncols | ndiagl | ndiagr);
                    posib ^= bit; // Eliminate the tried possibility.

                    // The following is the main additional trick here, as recognizing solution can not be done using stack level (d),
                    // since we save the depth+backtrack time at the end of the enumeration loop. However by noticing all coloumns are
                    // filled (comparison to -1) we know a solution was reached ...
                    // Notice also that avoiding an if on the ncols==-1 comparison is more efficient!
                    num += ncols == -1;

                    if (nposib)
                    {
                        if (posib)
                        {                        // This if saves stack depth + backtrack operations when we passed the last possibility in a row
                            posibs[d++] = posib; // Go lower in stack ..
                        }
                        cols[d] = ncols;
                        diagl[d] = ndiagl;
                        diagr[d] = ndiagr;
                        posib = nposib;
                    }
                }
                posib = posibs[--d]; // backtrack ...
            }
        }
    }
    return num * 2;
}

int main()
{
    stdio_init_all();
    printf("Init...\n");
    stdio_flush();
    sleep_ms(5000);
#if PICO_RP2350
    printf("I'm an RP2350 ");
    #ifdef __riscv
        printf("running RISC-V\n");
    #else
        printf("running ARM\n");
    #endif
#endif    
    printf("Start...\n");
    stdio_flush();

    clock_t startt = clock();
    printf("Started at %u\n", startt);
    int n = nqueens(boardSize);
    printf("Total solutions: %d\n", n);
    clock_t endt = clock();
    printf("Ended at %u\n", endt);
    printf("%d\n", (int)(endt - startt));
    for (;;)
    {
        sleep_ms(10000);
    }
}
