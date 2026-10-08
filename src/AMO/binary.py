from core import run


def at_most_one(clauses, variables, pool):
    bits = pool.new((len(variables) - 1).bit_length())
    for i, x in enumerate(variables):
        for t, bit in enumerate(bits):
            clauses.append([-x, bit if (i >> t) & 1 else -bit])