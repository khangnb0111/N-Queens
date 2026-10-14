from docplex.cp.model import CpoModel


def solve(n, time_limit=None):
    m = CpoModel()
    q = m.integer_var_list(n, 0, n - 1)
    m.add(m.all_diff(q))
    m.add(m.all_diff([q[i] + i for i in range(n)]))
    m.add(m.all_diff([q[i] - i for i in range(n)]))
    limit = {"TimeLimit": time_limit} if time_limit else {}
    s = m.solve(Workers=1, LogVerbosity="Quiet", **limit)
    if not s:
        return None
    return [s[v] for v in q]
