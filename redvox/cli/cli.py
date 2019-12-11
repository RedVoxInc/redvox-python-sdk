import argparse
import os.path
from typing import *

import redvox.api900.reader as reader
import redvox.api900.reader_utils as reader_utils


def check_path(path: str, path_is_file: bool = True, file_ext: Optional[str] = None) -> bool:
    """
    Checks that the passed in path exists.
    :param path: The path to check.
    :param path_is_file: The path is a file when True or a directory when False.
    :return: True if the path exists, False otherwise.
    """
    if path_is_file:
        return os.path.isfile(path) and (file_ext is None or os.path.basename(path).endswith(file_ext))
    else:
        return os.path.isdir(path)


def check_files(paths: List[str], file_ext: Optional[str] = None) -> bool:
    invalid_paths: List[str] = list(filter(lambda path: not check_path(path, file_ext=file_ext), paths))
    if len(invalid_paths) > 0:
        print(f"{len(invalid_paths)} invalid paths found")
        for invalid_path in invalid_paths:
            print(f"Invalid path {invalid_path}")
        return False
    return True


def check_out_dir(out_dir: Optional[str] = None) -> bool:
    if out_dir is not None and not check_path(out_dir, path_is_file=False):
        print(f"out_dir is invalid: {out_dir}")
        return False
    return True


def to_json(paths: List[str], out_dir: Optional[str] = None) -> None:
    # Check paths
    if not check_files(paths, ".rdvxz"):
        return

    # Check out_dir
    if not check_out_dir(out_dir):
        return

    for path in paths:
        pb_packet = reader.read_file(path)

        if out_dir is not None:
            file_name: str = os.path.basename(path).replace(".rdvxz", ".json")
            new_path = f"{out_dir}/{file_name}"
        else:
            new_path = path.replace(".rdvxz", ".json")

        with open(new_path, "w") as fout:
            fout.write(reader_utils.to_json(pb_packet))


def to_rdvxz(paths: List[str], out_dir: Optional[str] = None) -> None:
    # Check paths
    if not check_files(paths, ".json"):
        return

    # Check out_dir
    if not check_out_dir(out_dir):
        return

    for path in paths:
        with open(path, "r") as fin:
            json: str = fin.read()

            if out_dir is not None:
                file_name: str = os.path.basename(path).replace(".json", ".rdvxz")
                new_path = f"{out_dir}/{file_name}"
            else:
                new_path = path.replace(".json", ".rdvxz")

            reader_utils.write_file(new_path, reader_utils.from_json(json))


def print_stdout(paths: List[str]) -> None:
    # Check paths
    if not check_files(paths, ".rdvxz"):
        return

    for path in paths:
        print(reader.read_file(path))


def to_json_args(args) -> None:
    to_json(args.rdvxz_paths, args.out_dir)


def to_rdvxz_args(args) -> None:
    to_rdvxz(args.json_paths, args.out_dir)


def print_stdout_args(args) -> None:
    print_stdout(args.rdvxz_paths)


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser("redvox-cli",
                                                              description="Command line tools for viewing, converting,"
                                                                          " and downloading RedVox data.")
    parser.add_argument("--verbose",
                        "-v",
                        help="Enable verbose logging",
                        action="store_true")

    sub_parser = parser.add_subparsers(title="command")

    # rdvxz -> json
    to_json_parser = sub_parser.add_parser("to_json",
                                           help="Convert rdvxz files to json files")
    to_json_parser.add_argument("rdvxz_paths",
                                help="One or more rdvxz files to convert to json files",
                                nargs="+")
    to_json_parser.add_argument("--out_dir",
                                "-o",
                                help="Optional output directory (will use same directory as source files by default)")
    to_json_parser.set_defaults(func=to_json_args)

    # json -> rdvxz
    to_rdvxz_parser = sub_parser.add_parser("to_rdvxz",
                                            help="Convert json files to rdvxz files")
    to_rdvxz_parser.add_argument("json_paths",
                                 help="One or more json files to convert to rdvxz files",
                                 nargs="+")
    to_rdvxz_parser.add_argument("--out_dir",
                                 "-o",
                                 help="Optional output directory (will use same directory as source files by default)")
    to_rdvxz_parser.set_defaults(func=to_rdvxz_args)

    # print
    print_parser = sub_parser.add_parser("print",
                                         help="Print contents of rdvxz files to stdout")
    print_parser.add_argument("rdvxz_paths",
                              help="One or more rdvxz files to print",
                              nargs="+")
    print_parser.set_defaults(func=print_stdout_args)

    # Parse the args and call the appropriate function
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
