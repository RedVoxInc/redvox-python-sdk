import argparse
import os.path
import sys
from typing import *

import redvox.api900.reader as reader
import redvox.api900.reader_utils as reader_utils
import redvox.cli.data_req as data_req


def log(msg: str, verbose: bool) -> None:
    if verbose:
        print(msg)


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


def to_json(paths: List[str], out_dir: Optional[str] = None, verbose: bool = False) -> bool:
    # Check paths
    if not check_files(paths, ".rdvxz"):
        return False

    # Check out_dir
    if not check_out_dir(out_dir):
        return False

    for path in paths:
        pb_packet = reader.read_file(path)

        if out_dir is not None:
            file_name: str = os.path.basename(path).replace(".rdvxz", ".json")
            new_path = f"{out_dir}/{file_name}"
        else:
            new_path = path.replace(".rdvxz", ".json")

        with open(new_path, "w") as fout:
            fout.write(reader_utils.to_json(pb_packet))

        log(f"Converted {path} to {new_path}", verbose)

    return True


def to_rdvxz(paths: List[str], out_dir: Optional[str] = None, verbose: bool = False) -> bool:
    # Check paths
    if not check_files(paths, ".json"):
        return False

    # Check out_dir
    if not check_out_dir(out_dir):
        return False

    for path in paths:
        with open(path, "r") as fin:
            json: str = fin.read()

            if out_dir is not None:
                file_name: str = os.path.basename(path).replace(".json", ".rdvxz")
                new_path = f"{out_dir}/{file_name}"
            else:
                new_path = path.replace(".json", ".rdvxz")

            reader_utils.write_file(new_path, reader_utils.from_json(json))

            log(f"Converted {path} to {new_path}", verbose)

    return True


def print_stdout(paths: List[str]) -> bool:
    # Check paths
    if not check_files(paths, ".rdvxz"):
        return False

    for path in paths:
        print(reader.read_file(path))

    return True


def determine_exit(status: bool, verbose: bool = False) -> None:
    if status:
        log("Exiting with status=0", verbose)
        sys.exit(0)

    log("Exiting with status=1", verbose)
    sys.exit(1)


def to_json_args(args) -> None:
    determine_exit(to_json(args.rdvxz_paths, args.out_dir, args.verbose), args.verbose)


def to_rdvxz_args(args) -> None:
    determine_exit(to_rdvxz(args.json_paths, args.out_dir, args.verbose), args.verbose)


def print_stdout_args(args) -> None:
    determine_exit(print_stdout(args.rdvxz_paths), args.verbose)


def data_req_args(args) -> None:
    if check_out_dir(args.out_dir):
        determine_exit(data_req.make_data_req(args.out_dir,
                                              args.host,
                                              args.port,
                                              args.email,
                                              args.password,
                                              args.req_start_s,
                                              args.req_end_s,
                                              args.redvox_ids,
                                              args.verbose),
                       args.verbose)
    else:
        determine_exit(False, args.verbose)


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser("redvox-cli",
                                                              description="Command line tools for viewing, converting,"
                                                                          " and downloading RedVox data.")
    parser.add_argument("--verbose",
                        "-v",
                        help="Enable verbose logging",
                        action="store_true")

    sub_parser = parser.add_subparsers(title="command", dest="command", required=True)

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

    # data_req
    data_req_parser = sub_parser.add_parser("data_req",
                                            help="Request bulk RedVox data from the RedVox servers")
    data_req_parser.add_argument("--out_dir",
                                 "-o",
                                 help="The output directory that RedVox files will be written to.",
                                 default=".")
    data_req_parser.add_argument("host",
                                 help="Data server host")
    data_req_parser.add_argument("port",
                                 type=int,
                                 help="Data server port")
    data_req_parser.add_argument("email",
                                 help="redvox.io account email")
    data_req_parser.add_argument("password",
                                 help="redvox.io account password")
    data_req_parser.add_argument("req_start_s",
                                 type=int,
                                 help="Data request start as number of seconds since the epoch UTC")
    data_req_parser.add_argument("req_end_s",
                                 type=int,
                                 help="Data request end as number of seconds since the epoch UTC")
    data_req_parser.add_argument("redvox_ids",
                                 nargs="+",
                                 help="A list of RedVox ids delimited by a space")
    data_req_parser.set_defaults(func=data_req_args)

    # Parse the args and call the appropriate function
    args = parser.parse_args()
    log(f"Running with args={str(args)}", args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
