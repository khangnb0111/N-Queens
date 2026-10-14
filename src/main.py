from AMO import binary, binomial, commander, product, sequential
from core import run, run_solver
from Solvers import cplex_cp, cplex_mip, cpsat, gurobi

ENCODINGS = {
    "binomial": binomial,
    "binary": binary,
    "sequential": sequential,
    "commander": commander,
    "product": product,
}

SOLVERS = {
    "Gurobi": gurobi,
    "CPLEX MIP": cplex_mip,
    "CPLEX CP": cplex_cp,
    "CP-SAT": cpsat,
}


def ask_n():
    while True:
        value = input("Enter n: ").strip()
        if value.isdigit() and int(value) > 0:
            return int(value)
        print("n must be a positive integer.")


def ask_method():
    names = ["SAT " + name for name in ENCODINGS] + list(SOLVERS)
    for index, name in enumerate(names, 1):
        print("  %d. %s" % (index, name))
    lowered = {name.lower(): name for name in names}
    lowered.update({name: "SAT " + name for name in ENCODINGS})
    while True:
        value = input("Choose method (number or name): ").strip().lower()
        if value in lowered:
            return lowered[value]
        if value.isdigit() and 1 <= int(value) <= len(names):
            return names[int(value) - 1]
        print("Invalid choice.")


def ask_show_board():
    while True:
        value = input("Print the board? (Y/N): ").strip().upper()
        if value in ("Y", "N"):
            return value == "Y"
        print("Please enter Y or N.")


def main():
    n = ask_n()
    method = ask_method()
    show = ask_show_board()

    print("Solving n = %d with %s" % (n, method))
    if method.startswith("SAT "):
        run(ENCODINGS[method[4:]].at_most_one, n, show=show)
    else:
        run_solver(SOLVERS[method].solve, n, show=show)


if __name__ == "__main__":
    main()
