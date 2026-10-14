import gurobipy as gp

from env import gurobi_params


def solve(n, time_limit=None):
    params = gurobi_params()
    params["OutputFlag"] = 0
    m = gp.Model(env=gp.Env(params=params))
    m.Params.Threads = 1
    if time_limit:
        m.Params.TimeLimit = time_limit
    x = m.addVars(n, n, vtype=gp.GRB.BINARY)
    for i in range(n):
        m.addConstr(x.sum(i, "*") == 1)
        m.addConstr(x.sum("*", i) == 1)
    for d in range(-(n - 1), n):
        m.addConstr(gp.quicksum(x[i, i - d] for i in range(n) if 0 <= i - d < n) <= 1)
    for d in range(2 * n - 1):
        m.addConstr(gp.quicksum(x[i, d - i] for i in range(n) if 0 <= d - i < n) <= 1)
    m.optimize()
    if m.SolCount == 0:
        return None
    return [next(j for j in range(n) if x[i, j].X > 0.5) for i in range(n)]
