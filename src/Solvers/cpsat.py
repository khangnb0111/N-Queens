from ortools.sat.python import cp_model


def solve(n, time_limit=None):
    m = cp_model.CpModel()
    q = [m.new_int_var(0, n - 1, "") for _ in range(n)]
    m.add_all_different(q)
    m.add_all_different([q[i] + i for i in range(n)])
    m.add_all_different([q[i] - i for i in range(n)])
    solver = cp_model.CpSolver()
    if time_limit:
        solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 1
    if solver.solve(m) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return [solver.value(v) for v in q]
