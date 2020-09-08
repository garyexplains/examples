# Example of John von Neumann fair coin

import random

def biasedcoin():
    b = random.randint(1,10)
    if b > 7:
        return 1
    else:
        return 0

# This works because the chance of getting a BIASED result and then an UNBIASED result
# is the same as getting an UNBIASED result and then a BIASED result
# 50/50
def unbiasedcoin():
    while True:
        b1 = biasedcoin()
        b2 = biasedcoin()
        if b1 == 1 and b2 == 0:
            return 0
        if b1 == 0 and b2 == 1:
            return 1
    
# BIASED
print("BIASED")
count0 = 0
count1 = 0
for x in range(1000):
    b = biasedcoin()
    if b == 1:
        count1 = count1 + 1
    else:
        count0 = count0 + 1

print("Count0 is", count0)
print("Count1 is", count1)

#UNBIASED
print("UNBIASED")
count0 = 0
count1 = 0
for x in range(1000):
    b = unbiasedcoin()
    if b == 1:
        count1 = count1 + 1
    else:
        count0 = count0 + 1

print("Count0 is", count0)
print("Count1 is", count1)
