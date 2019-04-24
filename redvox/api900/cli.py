"""
This module provides a CLI for working with RedVox API 900 files.
"""

import os
import typing

import redvox.api900.reader as reader
import redvox.api900.reader_utils as reader_utils


def to_json(paths: typing.List[str]):
    """
    Given a list of paths of .rdvxz files, convert the .rdvxz files to RedVox API 900 compliant .json files.
    :param paths: List of paths to .rdvxz files.
    """
    def _to_json(_path: str):
        """
        Converts a .rdvxz file at path to json and writes the file to the same directory as the .rdvxz file was read
        from.
        :param _path: Path to the rdvxz file to convert.
        """
        pb_packet = reader.read_file(_path)
        new_path = _path.replace(".rdvxz", ".json")
        print("Converting %s -> %s" % (_path, new_path))
        with open(new_path, "w") as fout:
            fout.write(reader_utils.to_json(pb_packet))

    list(map(_to_json, paths))


def to_rdvxz(paths: typing.List[str]):
    """
    Given a list of paths of RedVox API 900 compliant .json files, convert the .json files to .rdvxz files.
    :param paths: List of paths to RedVox API 900 compliant .json files.
    """
    def _to_rdvxz(_path: str):
        """
        Converts a RedVox API 900 compliant .json file at path to a .rdvxz file in the same directory.
        :param _path: Path to the RedVox API 900 compliant json file.
        """
        with open(_path, "r") as json_in:
            json = json_in.read()

        new_path = _path.replace(".json", ".rdvxz")
        print("Converting %s -> %s" % (_path, new_path))
        reader_utils.write_file(new_path, reader_utils.from_json(json))

    list(map(_to_rdvxz, paths))


def string(paths: typing.List[str]):
    """
    For each path passed in, print out the contents of the .rdvxz file using protobuf's string serialization.
    :param paths: Paths of .rdvxz files.
    """
    for _path in paths:
        print(" ------------- Contents of %s" % _path)
        print(reader.read_file(_path))


# Entry point to CLI.
if __name__ == "__main__":
    import argparse

    ARGPARSE = argparse.ArgumentParser("api900-cli")

    ARGPARSE.add_argument("cmd",
                          choices=[
                              "to_json",
                              "to_rdvxz",
                              "print"
                          ],
                          help="Conversion type.")

    ARGPARSE.add_argument("file_paths",
                          help="One or more files to convert.",
                          nargs="+")

    ARGS = ARGPARSE.parse_args()
    PATHS = ARGS.file_paths

    # Check that paths exist
    for path in PATHS:
        if not os.path.isfile(path):
            print("Error: File with path %s not found." % path)
            exit(1)

    if ARGS.cmd == "to_json":
        to_json(ARGS.file_paths)
    elif ARGS.cmd == "to_rdvxz":
        to_rdvxz(ARGS.file_paths)
    else:
        string(ARGS.file_paths)
