import time
from collections import defaultdict

from pysat.solvers import Glucose3


class VarPool:
    def __init__(self, top):
        self.top = top

    def new(self, count):
        first = self.top + 1
        self.top += count
        return list(range(first, self.top + 1))


def generate_variables(n):
    return [[i * n + j + 1 for j in range(n)] for i in range(n)]


def diagonals(n, variables):
    # Ô cùng i + j nằm trên một đường chéo phụ, cùng i - j trên một đường chéo chính
    anti, main = defaultdict(list), defaultdict(list)
    for i in range(n):
        for j in range(n):
            anti[i + j].append(variables[i][j])
            main[i - j].append(variables[i][j])
    # Đường chéo một ô không cần ràng buộc
    return [d for d in list(anti.values()) + list(main.values()) if len(d) > 1]


def exactly_one(clauses, variables, pool, at_most_one):
    clauses.append(list(variables))
    at_most_one(clauses, variables, pool)


def generate_clauses(n, variables, pool, at_most_one):
    clauses = []

    # Chính xác một quân hậu trong mỗi hàng
    for row in variables:
        exactly_one(clauses, row, pool, at_most_one)

    # Chinh xác một quân hậu trong mỗi cột
    for col in range(n):
        exactly_one(clauses, [variables[row][col] for row in range(n)], pool, at_most_one)

    # Chính xác một quân hậu trên mỗi đường chéo
    for diagonal in diagonals(n, variables):
        at_most_one(clauses, diagonal, pool)

    return clauses


def solve_n_queens(n, at_most_one):
    variables = generate_variables(n)
    pool = VarPool(n * n)
    clauses = generate_clauses(n, variables, pool, at_most_one)

    with Glucose3(bootstrap_with=clauses) as solver:
        if not solver.solve():
            return None
        model = solver.get_model()

    return [[int(model[variables[i][j] - 1] > 0) for j in range(n)] for i in range(n)]


def print_solution(solution):
    if solution is None:
        print("No solution found.")
    else:
        for row in solution:
            print(" ".join("Q" if cell else "." for cell in row))


def run(at_most_one, n, show=True):
    start_time = time.time()
    solution = solve_n_queens(n, at_most_one)
    if show:
        print_solution(solution)
    print("n = %d, run time: %s seconds" % (n, time.time() - start_time))
    return solution
