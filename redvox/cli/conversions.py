"""
This module contains functions for performing RedVox data conversions and displaying the contents of rdvxz files.
"""

import logging
import os.path
from typing import List, Optional

import redvox.api900.reader as reader
import redvox.api900.reader_utils as reader_utils
import redvox.common.api_conversions as api_conversions
import redvox.api900.lib.api900_pb2 as api_900
import redvox.api1000.proto.redvox_api_m_pb2 as api_1000

import lz4.frame

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM

# pylint: disable=C0103
log = logging.getLogger(__name__)


def validate_rdvxm(paths: List[str]) -> bool:
    """
    Validates the correctness of rdvxm files.
    :param paths: Paths to the files.
    :return: True if all valid, False otherwise
    """
    for path in paths:
        wrapped_packet: WrappedRedvoxPacketM = (
            WrappedRedvoxPacketM.from_compressed_path(path)
        )
        validation_results: List[str] = wrapped_packet.validate()

        if len(validation_results) > 0:
            print(
                f"{len(validation_results)} validation issues found for file at path {path}"
            )
            for i, validation_result in enumerate(validation_results):
                print(f"{i} {validation_result}")

    return True


def rdvxz_to_json(paths: List[str], out_dir: Optional[str] = None) -> bool:
    """
    Converts .rdvxz files to .json files.
    :param paths: Paths of .rdvxz files to convert.
    :param out_dir: An optional output directory (will use input directory by default)
    :return: True if this succeeds, False otherwise
    """
    for path in paths:
        pb_packet = reader.read_file(path)

        if out_dir is not None:
            file_name: str = os.path.basename(path).replace(".rdvxz", ".json")
            new_path = f"{out_dir}/{file_name}"
        else:
            new_path = path.replace(".rdvxz", ".json")

        with open(new_path, "w") as fout:
            fout.write(reader_utils.to_json(pb_packet))

        log.info("Converted %s to %s", path, new_path)

    return True


def rdvxm_to_json(paths: List[str], out_dir: Optional[str] = None) -> bool:
    """
    Converts .rdvxm files to .json files.
    :param paths: Paths of .rdvxm files to convert.
    :param out_dir: An optional output directory (will use input directory by default)
    :return: True if this succeeds, False otherwise
    """
    out_dir = out_dir if out_dir is not None else "."
    for path in paths:
        wrapped_packet: WrappedRedvoxPacketM = (
            WrappedRedvoxPacketM.from_compressed_path(path)
        )

        wrapped_packet.write_json_to_file(out_dir)
        log.info("Converted %s to json", path)

    return True


def json_to_rdvxz(paths: List[str], out_dir: Optional[str] = None) -> bool:
    """
    Converts .json files to .rdvxz files.
    :param paths: Paths of .json files to convert.
    :param out_dir: An optional output directory (will use input directory by default)
    :return: True if this succeeds, False otherwise
    """
    for path in paths:
        with open(path, "r") as fin:
            json: str = fin.read()

            if out_dir is not None:
                file_name: str = os.path.basename(path).replace(".json", ".rdvxz")
                new_path = f"{out_dir}/{file_name}"
            else:
                new_path = path.replace(".json", ".rdvxz")

            reader_utils.write_file(new_path, reader_utils.from_json(json))

            log.info("Converted %s to %s", path, new_path)

    return True


def json_to_rdvxm(paths: List[str], out_dir: Optional[str] = None) -> bool:
    """
    Converts .json files to .rdvxm files.
    :param paths: Paths of .json files to convert.
    :param out_dir: An optional output directory (will use input directory by default)
    :return: True if this succeeds, False otherwise
    """
    out_dir = out_dir if out_dir is not None else "."
    for path in paths:
        wrapped_packet: WrappedRedvoxPacketM = WrappedRedvoxPacketM.from_json_path(path)
        wrapped_packet.write_compressed_to_file(out_dir)
        log.info("Converted %s to .rdvxm", path)

    return True


def rdvxz_to_rdvxm(paths: List[str], out_dir: Optional[str] = None) -> bool:
    """
    Convert rdvxz files to rdvxm files
    :param paths: Paths of original files to convert
    :param out_dir: Optional output directory of converted files (default "./")
    :return: True if completed successfully
    """
    out_dir = out_dir if out_dir is not None else "."
    for path in paths:
        packet_900: api_900.RedvoxPacket = reader.read_file(path, True)
        packet_1000: api_1000.RedvoxPacketM = (
            api_conversions.convert_api_900_to_1000_raw(packet_900)
        )
        file_name: str = f"{packet_1000.station_information.id}_{int(packet_1000.timing_information.packet_start_mach_timestamp)}.rdvxm"
        with lz4.frame.open(os.path.join(out_dir, file_name), "wb", compression_level=12) as fout:
            fout.write(packet_1000.SerializeToString())
        # wrapped_packet_900: reader.WrappedRedvoxPacket = reader.read_rdvxz_file(path)
        # wrapped_packet_1000: WrappedRedvoxPacketM = api_conversions.convert_api_900_to_1000(wrapped_packet_900)
        # wrapped_packet_1000.write_compressed_to_file(out_dir)

    return True


def rdvxm_to_rdvxz(paths: List[str], out_dir: Optional[str] = None) -> bool:
    """
    Convert rdvxm files to rdvxz files
    :param paths: Paths of original files to convert
    :param out_dir: Optional output directory of converted files (default "./")
    :return: True if completed successfully
    """
    out_dir = out_dir if out_dir is not None else "."
    for path in paths:
        wrapped_packet_1000: WrappedRedvoxPacketM = (
            WrappedRedvoxPacketM.from_compressed_path(path)
        )
        wrapped_packet_900: reader.WrappedRedvoxPacket = (
            api_conversions.convert_api_1000_to_900(wrapped_packet_1000)
        )
        wrapped_packet_900.write_rdvxz(out_dir)

    return True


def rdvxz_print_stdout(paths: List[str]) -> bool:
    """
    Prints the contends of rdvxz files to sdtout.
    :param paths: Paths to .rdvxz files to print.
    :return: True if this succeeds, False otherwise.
    """
    for path in paths:
        print(reader.read_file(path))

    return True


def rdvxm_print_stdout(paths: List[str]) -> bool:
    """
    Prints the contends of rdvxm files to sdtout.
    :param paths: Paths to .rdvxm files to print.
    :return: True if this succeeds, False otherwise.
    """
    for path in paths:
        print(WrappedRedvoxPacketM.from_compressed_path(path))

    return True
