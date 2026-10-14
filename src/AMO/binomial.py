from core import run


def at_most_one(clauses, variables, pool=None):
    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            clauses.append([-variables[i], -variables[j]])
