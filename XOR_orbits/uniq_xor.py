from string import ascii_uppercase


def xor_layer(layer):
    """Return the next cyclic adjacent-XOR layer."""
    n = len(layer)
    return [
        layer[i] ^ layer[(i + 1) % n]
        for i in range(n)
    ]


def mask_to_expr(mask, labels):
    """Convert a bitmask into a readable XOR expression."""
    if mask == 0:
        return "0"

    parts = []
    for i, label in enumerate(labels):
        if mask & (1 << i):
            parts.append(label)

    return "^".join(parts)


def sequence_to_strings(seq, labels):
    """Convert a sequence of bitmasks into readable strings."""
    return [mask_to_expr(x, labels) for x in seq]


def rotations(seq):
    """All cyclic rotations of a sequence."""
    n = len(seq)
    return [
        tuple(seq[i:] + seq[:i])
        for i in range(n)
    ]


def canonical_rotation(seq):
    """
    Return a canonical form of the cyclic sequence.

    This lets us treat:
        [A^B, B^C, C^D, D^A]

    as equivalent to:
        [B^C, C^D, D^A, A^B]
    """
    return min(rotations(seq))


def print_unique_cyclic_sequences(n, max_layers=None):
    if n > len(ascii_uppercase):
        raise ValueError("This demo supports up to 26 vertices.")

    labels = list(ascii_uppercase[:n])

    # layer 0 is the original vertices:
    # A, B, C, D, ...
    layer = [
        1 << i
        for i in range(n)
    ]

    seen = set()

    if max_layers is None:
        # Enough to see the cycle for typical small n
        max_layers = 4 * n * n

    for k in range(max_layers):
        key = canonical_rotation(layer)

        readable = sequence_to_strings(layer, labels)
        print(f"Layer {k}:")
        print(readable)
#        print()

        if key in seen:
            print(f"Cycle repeats at layer {k}.\n")
            break

        seen.add(key)


        layer = xor_layer(layer)


n = 3
#while n < 27:
while n < 7:
    print("#", n)
    print_unique_cyclic_sequences(n)
    n = n + 1
