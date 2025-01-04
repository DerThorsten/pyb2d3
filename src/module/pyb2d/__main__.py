import os


def get_incude_dir():
    return os.path.join(os.path.dirname(__file__), "include")


if __name__ == "__main__":
    import argparse

    # pyb2d --include-dir

    parser = argparse.ArgumentParser()
    parser.add_argument("--include-dir", action="store_true")

    args = parser.parse_args()

    if args.include_dir:
        print(get_incude_dir())
    else:
        parser.print_help()
