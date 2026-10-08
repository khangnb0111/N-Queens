from AMO import binary, binomial, commander, product, sequential
from core import run

ENCODINGS = {
    "binomial": binomial,
    "binary": binary,
    "sequential": sequential,
    "commander": commander,
    "product": product,
}


def ask_n():
    while True:
        value = input("Enter n: ").strip()
        if value.isdigit() and int(value) > 0:
            return int(value)
        print("n must be a positive integer.")


def ask_encoding():
    names = list(ENCODINGS)
    for index, name in enumerate(names, 1):
        print("  %d. %s" % (index, name))
    while True:
        value = input("Choose AMO (number or name): ").strip().lower()
        if value in ENCODINGS:
            return value
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
    amo = ask_encoding()
    show = ask_show_board()

    print("Solving n = %d with AMO = %s" % (n, amo))
    run(ENCODINGS[amo].at_most_one, n, show=show)


if __name__ == "__main__":
    main()
