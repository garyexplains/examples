//Copyright (C) <2022>, Gary Sims
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
// Compile:
// go build threadtesttool_go.go
//

//
// Usage:
// ./threadtesttool_go
//
// OR
// ./threadtesttool_go -goroutines=256 -numprimes=1000000
//
// Defaults are -goroutines=256 -numprimes=1000000
// Also try -goroutines=1 -numprimes=20000000
// Another interesting one is -goroutines=1000000 -numprimes=999

package main

import (
	"flag"
	"fmt"
)

func isPrime(n int) bool {
	if n < 0 {
		n = -n
	}
	switch {
	case n == 2:
		return true
	case n < 2 || n%2 == 0:
		return false

	default:
		for i := 3; i*i <= n; i += 2 {
			if n%i == 0 {
				return false
			}
		}
	}
	return true
}

func primality_test(n int, c chan int) {
	count := 0
	for i := 0; i < n; i++ {
		if isPrime(i) == true {
			count++
		}
	}
	c <- count
}

func main() {
	// Optional flags -goroutines and -numprimes
	numGoroutinesPtr := flag.Int("goroutines", 256, "number of concurrent goroutines to run")
	numPrimesPtr := flag.Int("numprimes", 1000000, "number of primes to test")

	flag.Parse()
	fmt.Println("goroutines:", *numGoroutinesPtr)
	fmt.Println("numprimes:", *numPrimesPtr)

	// Make the channel
	c := make(chan int, 100)

	// Start all the goroutines
	for i := 0; i < *numGoroutinesPtr; i++ {
		go primality_test(*numPrimesPtr, c)
	}

	// Read back the results
	totalprimes := 0
	for i := 0; i < *numGoroutinesPtr; i++ {
		totalprimes = totalprimes + <-c
	}
	fmt.Println("Total primes found", totalprimes)
}
