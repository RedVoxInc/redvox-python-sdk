"""
This module provides a CLI for working with RedVox API 900 files.
"""

import typing

import redvox.api900.reader as reader


def to_json(paths: typing.List[str]):
    def _to_json(path: str):
        pb_packet = reader.read_file(path)
        new_path = path.replace(".rdvxz", ".json")
        print("Converting %s -> %s" % (path, new_path))
        with open(new_path, "w") as fout:
            fout.write(reader.to_json(pb_packet))

    list(map(_to_json, paths))


def to_rdvxz(paths: typing.List[str]):
    def _to_rdvxz(path: str):
        with open(path, "r") as json_in:
            json = json_in.read()

        new_path = path.replace(".json", ".rdvxz")
        print("Converting %s -> %s" % (path, new_path))
        reader.write_file(new_path, reader.from_json(json))

    list(map(_to_rdvxz, paths))


def string(paths: typing.List[str]):
    for path in paths:
        print(" ------------- Contents of %s" % path)
        print(reader.read_file(path))


if __name__ == "__main__":
    import argparse

    argparse = argparse.ArgumentParser("api900-cli")

    argparse.add_argument("cmd",
                          choices=[
                              "to_json",
                              "to_rdvxz",
                              "print"
                          ],
                          help="Conversion type.")

    argparse.add_argument("file_paths",
                          help="One or more files to convert.",
                          nargs="+")

    args = argparse.parse_args()
    paths = args.file_paths
    if args.cmd == "to_json":
        to_json(args.file_paths)
    elif args.cmd == "to_rdvxz":
        to_rdvxz(args.file_paths)
    else:
        string(args.file_paths)
