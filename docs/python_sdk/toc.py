#!/usr/bin/env python3

"""
This module generates valid GSM ToC from a provided markdown source.
"""

import argparse


def linkify(line: str) -> str:
    return line.lower()\
        .replace(" ", "-")\
        .replace(".", "")\
        .replace("(", "")\
        .replace(")", "")\
        .replace('"', '')\
        .replace(',', '')


def generate_md_link(line: str, lvl: int) -> str:
    if lvl == 2:
        line = line.removeprefix("## ")
        return f"* [{line}](#{linkify(line)})"

    if lvl == 3:
        line = line.removeprefix("### ")
        return f"    * [{line}](#{linkify(line)})"

    if lvl == 4:
        line = line.removeprefix("#### ")
        return f"        * [{line}](#{linkify(line)})"

    return ""


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("path_to_markdown_file")

    args = parser.parse_args()

    markdown_path: str = args.path_to_markdown_file

    with open(markdown_path, "r") as markdown_in:
        line: str
        for line in markdown_in:
            line = line.strip()
            if line.startswith("####"):
                print(generate_md_link(line, 4))
            elif line.startswith("###"):
                print(generate_md_link(line, 3))
            elif line.startswith("##"):
                print(generate_md_link(line, 2))
            else:
                continue


if __name__ == "__main__":
    main()
