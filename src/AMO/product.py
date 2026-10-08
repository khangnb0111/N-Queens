import math

from AMO import binary
from AMO import binomial
from core import run


def at_most_one(clauses, variables, pool):
    k = len(variables)
    p = math.ceil(math.sqrt(k))
    q = math.ceil(k / p)
    rows = pool.new(p)
    cols = pool.new(q)

    sub_amo = binary.at_most_one if k > 10 else binomial.at_most_one
    sub_amo(clauses, rows, pool)
    sub_amo(clauses, cols, pool)

    for index, x in enumerate(variables):
        i, j = divmod(index, q)
        clauses.append([-x, rows[i]])
        clauses.append([-x, cols[j]])
