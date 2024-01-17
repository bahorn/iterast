import argparse
from iterast import iterast_start


def main():
    parser = argparse.ArgumentParser(prog='iterast')
    parser.add_argument('filename')
    args = parser.parse_args()
    iterast_start(args.filename)


if __name__ == "__main__":
    main()
