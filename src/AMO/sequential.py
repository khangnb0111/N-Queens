from core import run


def at_most_one(clauses, variables, pool):
    k = len(variables)
    if k <= 1:
        return
    s = pool.new(k - 1)
    clauses.append([-variables[0], s[0]])
    for i in range(1, k - 1):
        clauses.append([-variables[i], s[i]])
        clauses.append([-s[i - 1], s[i]])
        clauses.append([-s[i - 1], -variables[i]])
    clauses.append([-s[k - 2], -variables[k - 1]])
