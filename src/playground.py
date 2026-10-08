from core import run
from main import ENCODINGS, ask_encoding

board_sizes = [4, 8, 16, 32, 64, 128, 256, 512]

if __name__ == "__main__":
    amo = ask_encoding()

    print("Benchmark AMO = %s" % amo)
    for n in board_sizes:
        run(ENCODINGS[amo].at_most_one, n, show=False)
