def next_layer(layer):
    n = len(layer)
    return tuple(
        layer[i] ^ layer[(i + 1) % n]
        for i in range(n)
    )


def canonical_rotation(seq):
    n = len(seq)
    return min(
        seq[i:] + seq[:i]
        for i in range(n)
    )


def count_distinct_cyclic_xor_layers(n, max_layers=None):
    # Each vertex is represented as one bit.
    layer = tuple(1 << i for i in range(n))

    seen = set()

    if max_layers is None:
        # Safe upper bound for small/medium n.
        # The state space is finite, so the process must eventually cycle.
        max_layers = 1 << n

    for _ in range(max_layers):
        key = canonical_rotation(layer)

        if key in seen:
            return len(seen)

        seen.add(key)
        layer = next_layer(layer)

    raise RuntimeError("Cycle not found. Increase max_layers.")


seq = []
for n in range(3, 46):
    seq.append(count_distinct_cyclic_xor_layers(n))

print(seq)