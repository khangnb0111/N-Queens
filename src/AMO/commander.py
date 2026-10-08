import math

from AMO import binary
from AMO import binomial
from core import run


def at_most_one(clauses, variables, pool):
    size = math.ceil(math.sqrt(len(variables)))
    groups = [variables[i:i + size] for i in range(0, len(variables), size)]
    commanders = pool.new(len(groups))
    binomial.at_most_one(clauses, commanders)

    for commander, group in zip(commanders, groups):
        if len(group) > 4:
            binary.at_most_one(clauses, group, pool)
        else:
            binomial.at_most_one(clauses, group)
        clauses.append(group + [-commander])
        for x in group:
            clauses.append([commander, -x])
