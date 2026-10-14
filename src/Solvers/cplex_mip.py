from docplex.mp.model import Model


def solve(n, time_limit=None):
    m = Model(log_output=False)
    m.parameters.threads = 1
    if time_limit:
        m.parameters.timelimit = time_limit
    x = {(i, j): m.binary_var() for i in range(n) for j in range(n)}
    for i in range(n):
        m.add_constraint(m.sum(x[i, j] for j in range(n)) == 1)
        m.add_constraint(m.sum(x[j, i] for j in range(n)) == 1)
    for d in range(-(n - 1), n):
        m.add_constraint(m.sum(x[i, i - d] for i in range(n) if 0 <= i - d < n) <= 1)
    for d in range(2 * n - 1):
        m.add_constraint(m.sum(x[i, d - i] for i in range(n) if 0 <= d - i < n) <= 1)
    s = m.solve()
    if s is None:
        return None
    return [next(j for j in range(n) if s.get_value(x[i, j]) > 0.5) for i in range(n)]
