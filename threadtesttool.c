//Copyright (C) <2018>, Gary Sims
//All rights reserved.
//
//Redistribution and use in source and binary forms, with or without
//modification, are permitted provided that the following conditions are met:
//
//1. Redistributions of source code must retain the above copyright notice, this
//   list of conditions and the following disclaimer.
//2. Redistributions in binary form must reproduce the above copyright notice,
//   this list of conditions and the following disclaimer in the documentation
//   and/or other materials provided with the distribution.
//
//THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
//ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
//WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
//DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
//ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
//(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
//LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
//ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
//(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//

//
// Comile with:
// gcc -lpthread -o threadtesttool threadtesttool.c
//

//
// Usage:
// threadtesttool [[num_threads] num_primes_to_find]
//
// OR
//
// nothreadtesttool [[num_threads] num_primes_to_find]
//
// Note to create "nothreadtesttool" use:
// ln -s threadtesttool nothreadtesttool

//
// Notes:
// This is very easy to break. There should be much more error checking etc
//

#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <stdlib.h>
#include <unistd.h>

#define MAX_NUM_THREADS 50
#define DEFAULT_NUM_THREADS 10
#define DEFAULT_PRIMES_TO_FIND 250000

pthread_t tid[MAX_NUM_THREADS];
int * ptr[MAX_NUM_THREADS];
int gPrimesToFind = DEFAULT_PRIMES_TO_FIND;
int gNumThreads = DEFAULT_NUM_THREADS;
int gNoThreads = 0;

int is_prime(unsigned int n) {
    unsigned int p;
    if (!(n & 1) || n < 2) return n == 2;

    for (p = 3; p <= n / p; p += 2)
        if (!(n % p)) return 0;
    return 1;
}

void * doSomeThing(void * arg) {
    int count = 0;
    int i = 0;
    while (i < gPrimesToFind) {
        if (is_prime(i) != 0) {
            count++;
        }
        i = i + 1;
    }

    if(!gNoThreads)
    	pthread_exit( & count);
}

int main(int argc, char * argv[]) {
    if(strstr(argv[0], "nothreadtesttool")!=NULL) {
	gNoThreads = 1;
    }
    if (argc == 2) {
        gPrimesToFind = (int) strtol(argv[1], NULL, 10);
    }

    if (argc == 3) {
        gNumThreads = (int) strtol(argv[1], NULL, 10);
        gPrimesToFind = (int) strtol(argv[2], NULL, 10);
        if (gNumThreads > MAX_NUM_THREADS) {
            printf("Too many threads\n");
            exit(-1);
        }
    }

    printf("Threading test tool V1.0. (C) Gary Sims 2018\n");
    if(!gNoThreads) {
	    printf("Threads: %d. Primes to find: %d\n", gNumThreads, gPrimesToFind);
    } else {
	    printf("Iterations: %d. Primes to find: %d\n", gNumThreads, gPrimesToFind);
    }

    int i = 0;
    int err;

    if(gNoThreads) {
	while(i < gNumThreads) {
		doSomeThing(NULL);
		i++;
	}
    } else {
    	while (i < gNumThreads) {
        	err = pthread_create( & (tid[i]), NULL, & doSomeThing, NULL);
        	if (err != 0)
            		printf("\nCan't create thread :[%s]", strerror(err));
        	i++;
    	}

    	i = 0;
	while (i < gNumThreads) {
        	pthread_join(tid[i], (void ** ) & (ptr[i]));
        	i++;
	}
    }
    return 0;
}
