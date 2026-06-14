# Number of unique layers in an XOR closed loop
## OEIS
I am trying to get this sequence into the OEIS [A396572](https://oeis.org/draft/A396572)

## Sequence 
Starting at n = 3

2, 5, 4, 4, 8, 9, 8, 8, 32, 8, 64, 16, 16, 17, 16, 16, 512, 16, 64, 64, 2048, 16, 1024, 128, 512, 32, 16384, 32, 32, 33, 32, 32, 4096, 32, 87382, 1024, 4096, 32, 1024, 128, 128, 128, 4096

## Intro
You have a sequence of nodes in a closed loop, with numbers at the vertices, say A,B,C that form the loop AB,BC,CA (let's call this layer 0).

Perform XOR (^) on each connection so A XOR B, B XOR C, C XOR A results in a new layer (layer 1): ['A^B', 'B^C', 'A^C'].

If you then repeat this and use XOR on layer 1 you get ['A^B^B^C', 'B^C^A^C', 'A^C^A^B'] which simplifies to ['A^C', 'B^A', 'C^B'] which is the same as layer 1, but just a different order.

So a loop of 3 numbers (3 vertices), a triangle, has two unique layers, the original [A, B, C] and layer 1 ['A^B', 'B^C', 'A^C'].

In the example below you can see that layer 2 is in fact layer 1 but just in a different order.
```
Layer 0:
['A', 'B', 'C']
Layer 1:
['A^B', 'B^C', 'A^C']
Layer 2:
['A^C', 'A^B', 'B^C']
Cycle repeats at layer 2.
```

If you try this for closed loops with 4 vertices or 5, etc you get a different number of unique layers (as shown in the above sequence) before the layers start repeating.

Interestingly they repeat in a cyclic fashion. For example, for 5 vertices there are 4 unique layers (layers 0 to 3). Layer 4 is a repeat of layer 1 (in a different order) and layer 5 is repeat of layer 2, etc.

Here is a loop of 7 numbers:
```
# 7
Layer 0:
['A', 'B', 'C', 'D', 'E', 'F', 'G']
Layer 1:
['A^B', 'B^C', 'C^D', 'D^E', 'E^F', 'F^G', 'A^G']
Layer 2:
['A^C', 'B^D', 'C^E', 'D^F', 'E^G', 'A^F', 'B^G']
Layer 3:
['A^B^C^D', 'B^C^D^E', 'C^D^E^F', 'D^E^F^G', 'A^E^F^G', 'A^B^F^G', 'A^B^C^G']
Layer 4:
['A^E', 'B^F', 'C^G', 'A^D', 'B^E', 'C^F', 'D^G']
Layer 5:
['A^B^E^F', 'B^C^F^G', 'A^C^D^G', 'A^B^D^E', 'B^C^E^F', 'C^D^F^G', 'A^D^E^G']
Layer 6:
['A^C^E^G', 'A^B^D^F', 'B^C^E^G', 'A^C^D^F', 'B^D^E^G', 'A^C^E^F', 'B^D^F^G']
Layer 7:
['B^C^D^E^F^G', 'A^C^D^E^F^G', 'A^B^D^E^F^G', 'A^B^C^E^F^G', 'A^B^C^D^F^G', 'A^B^C^D^E^G', 'A^B^C^D^E^F']
Layer 8:
['A^B', 'B^C', 'C^D', 'D^E', 'E^F', 'F^G', 'A^G']
Cycle repeats at layer 8.
```

### When n is a power of 2
When n is a power of 2 (i.e. 4, 8, 16, 32, etc) then the sequecne always reaches 0. The step to reach 0 adds a extra layer, so the total number of unique layers is n + 1.

```
Layer 0:
['A', 'B', 'C', 'D']
Layer 1:
['A^B', 'B^C', 'C^D', 'A^D']
Layer 2:
['A^C', 'B^D', 'A^C', 'B^D']
Layer 3:
['A^B^C^D', 'A^B^C^D', 'A^B^C^D', 'A^B^C^D']
Layer 4:
['0', '0', '0', '0']
Cycle repeats at layer 5.
```

## In other words
Imagine n items arranged in a circle. In each step (or "layer"), you update every item by taking the XOR of its current value and the value of the item next to it.

You treat cyclic rotations as identical (e.g., A^B, B^C, C^A is the same state as B^C, C^A, A^B).

The question is: How many unique layers exist before the pattern repeats?

## A006519(n) + A085587(n)
It turns out that the sequence is the same as OEIS A006519(n) + A085587(n), the preperiodic part + the period.

### A006519
A006519 is the highest power of 2 dividing n.

1, 2, 1, 4, 1, 2, 1, 8, 1, 2, 1, 4, 1, 2, 1, 16, 1, 2, 1, 4, 1, 2, 1, 8, 1, 2, 1, 4, 1, 2, 1, 32, 1, 2, 1, 4, 1, 2, 1, 8, 1, 2, 1, 4, 1, 2, 1, 16, 1, 2, 1, 4, 1, 2, 1, 8, 1, 2, 1, 4, 1, 2, 1, 64, 1, 2, 1, 4, 1, 2, 1, 8, 1, 2, 1, 4, 1, 2, 1, 16, 1, 2, 1, 4, 1, 2, 1, 8, 1, 2, 1, 4, 1, 2, 1, 32, 1, 2, 1, 4, 1, 2

### A085587
A085587 is the eventual period of a single cell in rule 90 cellular automaton in a cyclic universe of width n.

1, 1, 1, 1, 3, 2, 7, 1, 7, 6, 31, 4, 63, 14, 15, 1, 15, 14, 511, 12, 63, 62, 2047, 8, 1023, 126, 511, 28, 16383, 30, 31, 1, 31, 30, 4095, 28, 87381, 1022, 4095, 24, 1023, 126, 127, 124, 4095, 4094, 8388607, 16, 2097151, 2046, 255, 252, 67108863, 1022, 1048575, 56, 511, 32766, 536870911, 60

## Simulation vs number theory
### Simulation
There are some different programs here in this folder. The Python programs do "simulation".

They create the starting layer, calculate the exact XOR expressions for the next layer using layer[i] ^ layer[(i + 1) % n], find the canonical (minimum) rotation, and save it to a memory set().

It keeps simulating layer after layer until it finds a sequence it has already seen.

There is one script that demonstrates the idea and another that just counts.

__Limitations:__ Because the number of unique states grows exponentially, this script is incredibly slow. By n=26, it is generating thousands of expressions. If you asked it to solve for n=1024, your computer would run out of memory and the universe would end before it finished counting.

### Number theory

Previously there was a C program in this repo that tried to calculate the exact number of unique layers instantly using number theory over Galois Field of 2, denoted as GF(2).

The C program assumed that because the XOR operation is linear, the repeated application of adjacent XORs follows predictable algebraic patterns based on polynomials. The C program breaks n down into its power-of-2 component (s) and its odd multiplier (m) so that n=2s⋅m.

It was WRONG.

### ERROR

The C programmer fell victim to what mathematicians call the **"Strong Law of Small Numbers"**—observing a pattern that perfectly holds true for small inputs and incorrectly assuming it is a universal law. $n=37$ is the exact moment that pattern breaks.

In the algebraic theory of Cellular Automata, the period of a cyclic grid of width $n$ does not necessarily *equal* $2^k - 1$; the actual rule is that the period must **divide** $2^k - 1$.

For every single odd number up to $n = 35$, the period of the automaton just so happens to perfectly equal $2^k - 1$. 

**$n = 37$ is the very first integer where the period is a *proper fraction* of $2^k - 1$.**

The C program predicted the cycle length to be ($2^{18} - 1 = 262,143$). The real answer is 87382 which is (262143 / 3) + 1 
