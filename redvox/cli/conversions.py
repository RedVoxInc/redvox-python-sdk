import logging
import os.path
from typing import *

import redvox.api900.reader as reader
import redvox.api900.reader_utils as reader_utils


log = logging.getLogger(__name__)


def to_json(paths: List[str], out_dir: Optional[str] = None) -> bool:
    for path in paths:
        pb_packet = reader.read_file(path)

        if out_dir is not None:
            file_name: str = os.path.basename(path).replace(".rdvxz", ".json")
            new_path = f"{out_dir}/{file_name}"
        else:
            new_path = path.replace(".rdvxz", ".json")

        with open(new_path, "w") as fout:
            fout.write(reader_utils.to_json(pb_packet))

        log.info(f"Converted {path} to {new_path}")

    return True


def to_rdvxz(paths: List[str], out_dir: Optional[str] = None) -> bool:
    for path in paths:
        with open(path, "r") as fin:
            json: str = fin.read()

            if out_dir is not None:
                file_name: str = os.path.basename(path).replace(".json", ".rdvxz")
                new_path = f"{out_dir}/{file_name}"
            else:
                new_path = path.replace(".json", ".rdvxz")

            reader_utils.write_file(new_path, reader_utils.from_json(json))

            log.info(f"Converted {path} to {new_path}")

    return True


def print_stdout(paths: List[str]) -> bool:
    for path in paths:
        print(reader.read_file(path))

    return True
