import argparse
from iterast import iterast_start


def main():
    parser = argparse.ArgumentParser(prog='iterast')
    parser.add_argument('filename')
    parser.add_argument('--no-clear', action='store_true')
    args = parser.parse_args()
    iterast_start(args.filename, not args.no_clear)


if __name__ == "__main__":
    main()
