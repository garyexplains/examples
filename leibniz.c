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

#include <gmp.h>
#include <stdio.h>
#include <pthread.h>
#include <string.h>

// Prereq: sudo apt install libgmp-dev
// Compile: gcc -o leibniz leibniz.c -lgmp -pthread

//#define ITERATIONS 1000000000
#define ITERATIONS 100000000
#define PERC 512
/*
 * Shock, horror: globals!
 */
mpf_t pi4_plus;
mpf_t pi4_minus;

void *do_pi_minus(void *arg) {
	unsigned long int i;
	mpf_t oneoveri;
	mpf_init2 (oneoveri, PERC);

	for(i=3;i<ITERATIONS;i=i+4) {
		mpf_set_ui(oneoveri, 1);
		mpf_div_ui(oneoveri, oneoveri, i);
		mpf_sub(pi4_minus, pi4_minus, oneoveri);
	}
	gmp_printf("%.*Ff\n",80, pi4_minus);
}

void *do_pi_plus(void * arg) {
	unsigned long int i;
	mpf_t oneoveri;
	mpf_init2 (oneoveri, PERC);

	for(i=5;i<ITERATIONS;i=i+4) {
		mpf_set_ui(oneoveri, 1);
		mpf_div_ui(oneoveri, oneoveri, i);
		mpf_add(pi4_plus, pi4_plus, oneoveri);
	}
	gmp_printf("%.*Ff\n",80, pi4_plus);
}

int main() {
	unsigned long int i;
	mpf_t pi;
	pthread_t plus_tid;
	pthread_t minus_tid;
	int err;

	mpf_init2 (pi, PERC);
	mpf_init2 (pi4_plus, PERC);
	mpf_init2 (pi4_minus, PERC);
	mpf_set_ui(pi4_minus, 1);


	err = pthread_create( &minus_tid, NULL, &do_pi_minus, NULL);
        if (err != 0)
        	printf("\nCan't create thread :[%s]", strerror(err));

	err = pthread_create( &plus_tid, NULL, &do_pi_plus, NULL);
        if (err != 0)
        	printf("\nCan't create thread :[%s]", strerror(err));

	pthread_join(minus_tid, NULL);
	pthread_join(plus_tid, NULL);

	mpf_add(pi, pi4_plus, pi4_minus);
	mpf_mul_ui(pi, pi, 4);
	gmp_printf("%.*Ff\n",80, pi);

}
