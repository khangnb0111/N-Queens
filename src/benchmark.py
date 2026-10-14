import csv
import multiprocessing as mp
import os
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from pysat.solvers import Glucose3

from core import VarPool, generate_clauses, generate_variables
from main import ENCODINGS
from Solvers import cplex_cp, cplex_mip, cpsat, gurobi

SIZES = [8, 16, 24, 32, 40, 64, 128, 256, 512, 1024]
VAR_LIMIT: dict = {}
TIME_LIMIT = 600
REPEATS = 3
MAX_CLAUSES = 40_000_000
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")


def valid(n, cols):
    return (sorted(cols) == list(range(n))
            and len({c + i for i, c in enumerate(cols)}) == n
            and len({c - i for i, c in enumerate(cols)}) == n)


def binomial_clause_count(n):
    pairs = lambda k: k * (k - 1) // 2
    diag = 2 * (2 * sum(pairs(k) for k in range(2, n)) + pairs(n))
    return 2 * n * (pairs(n) + 1) + diag


def sat_worker(name, n, queue):

    t0 = time.perf_counter()
    variables = generate_variables(n)
    pool = VarPool(n * n)
    clauses = generate_clauses(n, variables, pool, ENCODINGS[name].at_most_one)
    t1 = time.perf_counter()
    with Glucose3(bootstrap_with=clauses) as solver:
        ok = solver.solve()
        model = solver.get_model()
    t2 = time.perf_counter()
    cols = [next(j for j in range(n) if model[variables[i][j] - 1] > 0) for i in range(n)]
    queue.put(dict(vars=pool.top, clauses=len(clauses), encode=t1 - t0,
                   solve=t2 - t1, total=t2 - t0, valid=ok and valid(n, cols)))


def solver_worker(module, n, queue):
    t0 = time.perf_counter()
    cols = module.solve(n, TIME_LIMIT)
    total = time.perf_counter() - t0
    if cols is None:
        queue.put(dict(status="TO", total=total, valid=False))
        return
    queue.put(dict(total=total, valid=valid(n, cols)))


def gurobi_worker(n, queue):
    solver_worker(gurobi, n, queue)


def cplex_mip_worker(n, queue):
    solver_worker(cplex_mip, n, queue)


def cplex_cp_worker(n, queue):
    solver_worker(cplex_cp, n, queue)


def cpsat_worker(n, queue):
    solver_worker(cpsat, n, queue)


SOLVERS = {"Gurobi": gurobi_worker, "CPLEX MIP": cplex_mip_worker,
           "CPLEX CP": cplex_cp_worker, "CP-SAT": cpsat_worker}


def run_isolated(target, args):
    queue = mp.Queue()
    p = mp.Process(target=target, args=(*args, queue))
    p.start()
    p.join(TIME_LIMIT + 60 if TIME_LIMIT else None)
    if p.is_alive():
        p.kill()
        return {"status": "TO"}
    if p.exitcode != 0 or queue.empty():
        return {"status": "ERR(%s)" % p.exitcode}
    return {"status": "OK", **queue.get()}


def median_runs(target, args):
    runs = []
    for _ in range(REPEATS):
        r = run_isolated(target, args)
        if r["status"] != "OK":
            return r
        runs.append(r)
    out = dict(runs[0])
    for key in ("encode", "solve", "total"):
        if key in out:
            out[key] = statistics.median(r[key] for r in runs)
    out["valid"] = all(r["valid"] for r in runs)
    return out


SAT_FIELDS = ["encoding", "n", "status", "vars", "clauses", "encode_s", "solve_s", "total_s", "valid"]
SOLVER_FIELDS = ["solver", "n", "status", "total_s", "valid"]


def run_config(row, kind):
    n = int(row["n"])
    if kind == "sat":
        r = median_runs(sat_worker, (row["encoding"], n))
        row.update(vars=r.get("vars"), clauses=r.get("clauses"), encode_s=r.get("encode"),
                   solve_s=r.get("solve"))
        name = row["encoding"]
    else:
        r = median_runs(SOLVERS[row["solver"]], (n,))
        name = row["solver"]
    row.update(status=r["status"], total_s=r.get("total"), valid=r.get("valid"))
    print(name, n, r, flush=True)


def run_all(tasks, jobs):
    lock = threading.Lock()

    def job(task):
        path, fields, rows, row, kind = task
        run_config(row, kind)
        with lock:
            write_csv(path, fields, rows)

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for fut in [ex.submit(job, task) for task in tasks]:
            fut.result()


def write_csv(path, fields, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def full_run(which, jobs):
    tasks = []
    if "sat" in which:
        path, rows = os.path.join(RESULTS, "sat.csv"), []
        for name in ENCODINGS:
            for n in SIZES:
                row = dict.fromkeys(SAT_FIELDS)
                row.update(encoding=name, n=n)
                rows.append(row)
                if name == "binomial" and binomial_clause_count(n) > MAX_CLAUSES:
                    row["status"] = "MO"
                else:
                    tasks.append((path, SAT_FIELDS, rows, row, "sat"))
        write_csv(path, SAT_FIELDS, rows)
    if "solvers" in which:
        path, rows = os.path.join(RESULTS, "solvers.csv"), []
        for name in SOLVERS:
            for n in SIZES:
                row = dict.fromkeys(SOLVER_FIELDS)
                row.update(solver=name, n=n)
                rows.append(row)
                mip_vars = n if name == "CPLEX CP" else n * n
                if mip_vars > VAR_LIMIT.get(name, float("inf")):
                    row["status"] = "SL"
                else:
                    tasks.append((path, SOLVER_FIELDS, rows, row, "solvers"))
        write_csv(path, SOLVER_FIELDS, rows)
    run_all(tasks, jobs)


def ask_choice(prompt, names):
    for index, name in enumerate(names, 1):
        print("  %d. %s" % (index, name))
    while True:
        value = input(prompt).strip()
        lowered = {name.lower(): name for name in names}
        if value.lower() in lowered:
            return lowered[value.lower()]
        if value.isdigit() and 1 <= int(value) <= len(names):
            return names[int(value) - 1]
        print("Invalid choice.")


def ask_int(prompt, default):
    while True:
        value = input("%s [%d]: " % (prompt, default)).strip()
        if not value:
            return default
        if value.isdigit() and int(value) > 0:
            return int(value)
        print("Please enter a positive integer.")


def ask_sizes():
    while True:
        value = input("Enter n (or 'all' for %s): " % SIZES).strip().lower()
        if value == "all":
            return list(SIZES)
        if value.isdigit() and int(value) > 0:
            return [int(value)]
        print("n must be a positive integer or 'all'.")


def ask_yes_no(prompt):
    while True:
        value = input(prompt).strip().upper()
        if value in ("Y", "N"):
            return value == "Y"
        print("Please enter Y or N.")


def single_run():
    global REPEATS
    methods = ["SAT " + name for name in ENCODINGS] + list(SOLVERS)
    method = ask_choice("Choose method (number or name): ", methods)
    sizes = ask_sizes()
    REPEATS = ask_int("Number of runs", REPEATS)

    if method.startswith("SAT "):
        kind, key, name, fname = "sat", "encoding", method[4:], "sat.csv"
        target = sat_worker
    else:
        kind, key, name, fname = "solvers", "solver", method, "solvers.csv"
        target = SOLVERS[method]
    for n in sizes:
        print("Running %s, n = %d, %d run(s), time limit %s" %
              (method, n, REPEATS, "%d s" % TIME_LIMIT if TIME_LIMIT else "none"))
        if kind == "sat" and name == "binomial" and binomial_clause_count(n) > MAX_CLAUSES:
            r = {"status": "MO"}
        else:
            r = median_runs(target, (name, n) if kind == "sat" else (n,))

        if r["status"] != "OK":
            print("Status:", r["status"])
        else:
            if "clauses" in r:
                print("Variables: %d, clauses: %d" % (r["vars"], r["clauses"]))
                print("Encode: %.4f s, solve: %.4f s" % (r["encode"], r["solve"]))
            print("Total (median): %.4f s" % r["total"])
            print("Valid solution:", r["valid"])
        save_result(fname, key, name, n, kind, r)


def save_result(fname, key, name, n, kind, r):
    path = os.path.join(RESULTS, fname)
    fields = SAT_FIELDS if kind == "sat" else SOLVER_FIELDS
    rows = []
    if os.path.exists(path):
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
    row = next((x for x in rows if x[key] == name and int(x["n"]) == n), None)
    if row is None:
        row = dict.fromkeys(fields)
        row.update({key: name, "n": n})
        rows.append(row)
    row.update(status=r["status"], total_s=r.get("total"), valid=r.get("valid"))
    if kind == "sat":
        row.update(vars=r.get("vars"), clauses=r.get("clauses"),
                   encode_s=r.get("encode"), solve_s=r.get("solve"))
    write_csv(path, fields, rows)
    print("Saved to results/%s" % fname)


def main():
    os.makedirs(RESULTS, exist_ok=True)
    if ask_yes_no("Run full benchmark (all methods, all n)? (Y/N): "):
        full_run(["sat", "solvers"], 1)
    else:
        single_run()


if __name__ == "__main__":
    main()
