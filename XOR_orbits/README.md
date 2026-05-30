# Number of unique layers in an XOR closed loop
## OEIS
I am trying to get this sequence into the OEIS [A396572](https://oeis.org/draft/A396572)

## Sequence
2, 5, 4, 4, 8, 9, 8, 8, 32, 8, 64, 16, 16, 17, 16, 16, 512, 16, 64, 64, 2048, 16, 1024, 128, 512, 32, 16384, 32, 32, 33, 32, 32, 4096, 32, 87382, 1024, 4096, 32, 1024, 128, 128, 128, 4096

## Intro
You have a sequence of nodes in a closed loop, with numbers at the vertices, say A,B,C that form the loop AB,BC,CA (let's called this layer 0).

Perform XOR (^) on each connection so A XOR B, B XOR C, C XOR A results in a new layer (layer 1): ['A^B', 'B^C', 'A^C'].

If you then repeat this and use XOR on layer 1 you get ['A^B^B^C', 'B^C^A^C', 'A^C^A^B'] which simplifies to ['A^C', 'B^A', 'C^B'] which is the same as layer 1, but just a different order.

So a loop of 3 number (3 vertices), a triangle, has two unique layers, the original [A, B, C] and layer 1 ['A^B', 'B^C', 'A^C'].

If you try this for closed loops with 4 vertices or 5, etc you get a different number of unique layers (as shown in the above sequence) before the layers start repeating.

Interesting they repeat in a cyclic fashion. For example for 5 vertices there are 4 unique layers (layers 0 to 3). Layer 4 is a repeat of layer 1 (in a different order) and layer 5 is repeat of layer 2, etc.

## In other words
Cyclic Adjacent-XOR

Imagine n items arranged in a circle. In each step (or "layer"), you update every item by taking the XOR of its current value and the value of the item next to it.

You treat cyclic rotations as identical (e.g., A^B, B^C, C^A is the same state as B^C, C^A, A^B).

The question is: How many unique layers exist before the pattern repeats?

## Simulation vs number theory
### Simulation
There are some different programs here in this folder. The Python programs do "simulation". 

They create the starting layer, calculates the exact XOR expressions for the next layer using layer[i] ^ layer[(i + 1) % n], finds the canonical (minimum) rotation, and saves it to a memory set().

It keeps simulating layer after layer until it finds a sequence it has already seen.

There is one script that demonstrates the idea and another that just counts.

__Limitations:__ Because the number of unique states grows exponentially, this script is incredibly slow. By n=26, it is generating thousands of expressions. If you asked it to solve for n=1024, your computer would run out of memory and the universe would end before it finished counting.

### Number theory

The C program skips the simulation entirely. It calculates the exact number of unique layers instantly using number theory over Galois Field of 2, denoted as GF(2).

#### How it works:
Because the XOR operation is linear, the repeated application of adjacent XORs follows predictable algebraic patterns based on polynomials.

The C program breaks n down into its power-of-2 component (s) and its odd multiplier (m) so that n=2s⋅m.

__The math:__
Instead of simulating the layers, it finds the multiplicative order of 2 modulo m (searching for k where 2k≡±1(modm)).

It then calculates the total number of unique states mathematically, which is 2s+k (or 2s+1 if n is a perfect power of 2).

#### The Advantage:
It takes a fraction of a millisecond to solve n=1024.

The only reason the C program is so long is that the mathematical answers get so massive (numbers with over 150 decimal digits) that it requires a custom arbitrary-precision (BigInt) engine to print the result.

### More math
For a ring size n, write:

`n = 2^s * m`

where m is odd.

If m = 1, meaning n is a power of two, then:

`count = n + 1`

Otherwise, find the smallest positive k such that:

`2^k ≡ 1 mod m`

or:

`2^k ≡ -1 mod m`

Then:

`count = 2^(s + k)`

#### Example for n = 47:
```
47 = 2^0 * 47
2^23 ≡ -1 mod 47
count = 2^(0 + 23) = 8388608
```

#### Short explanation
The XOR-layer step is equivalent to multiplying by (1 + x) in binary polynomial arithmetic, with x^n = 1 because the row wraps around. Over XOR arithmetic:

`(1 + x)^(2^k) = 1 + x^(2^k)`

So the pattern repeats, up to rotation, when 2^k lands at 1 or -1 modulo the odd part of n.

### What are n,m,k, and s in the explanation?

Use these definitions:

n = the size of the ring / number of bits / number of rows

Example: if the layer has 47 positions, then n = 47.

s = how many times n can be divided by 2

This is the power-of-two part of n.

m = what is left after removing all factors of 2 from n

So:

n = 2^s * m

where m is odd.

Examples:
```
n = 47
47 = 2^0 * 47
s = 0
m = 47
```
```
n = 12
12 = 2^2 * 3
s = 2
m = 3
```
```
n = 128
128 = 2^7 * 1
s = 7
m = 1
```
Then:

k = the first positive exponent where 2^k is either 1 or -1 modulo m

Example for m = 47:
```
2^1 mod 47 = 2
2^2 mod 47 = 4
...
2^23 mod 47 = 46
```
Since 46 is the same as -1 mod 47, we have:

`k = 23`

Then the count is:

`count = 2^(s + k)`

unless m = 1, in which case:

`count = n + 1`
