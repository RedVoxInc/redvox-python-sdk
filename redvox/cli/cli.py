"""
This module provides a command line interface (CLI) for converting, viewing, and downloading RedVox data files.
"""

import argparse
import logging
import os.path
import sys
from typing import Dict, List, Optional, Any, Callable

from redvox.api1000.wrapped_redvox_packet.sensors.image import Image, ImageCodec
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.cloud.data_api import DataRangeReqType

import redvox.cloud.client as cloud_client
from redvox.cloud.config import RedVoxConfig
import redvox.cloud.data_api as data_api
import redvox.cli.conversions as conversions
import redvox.cli.data_req as data_req
import redvox.common.io as io
from redvox.common.gui import cloud_data_retrieval

# pylint: disable=C0103
log = logging.getLogger(__name__)


def map_or_default(val: Any, apply: Callable[[Any], Any], default: Any) -> Any:
    if val is None:
        return default
    return apply(val)


def check_path(
    path: str, path_is_file: bool = True, file_ext: Optional[str] = None
) -> bool:
    """
    Checks that the passed in path exists.
    :param file_ext: Optional extension to check.
    :param path: The path to check.
    :param path_is_file: The path is a file when True or a directory when False.
    :return: True if the path exists, False otherwise.
    """
    if path_is_file:
        return os.path.isfile(path) and (
            file_ext is None or os.path.basename(path).endswith(file_ext)
        )
    else:
        return os.path.isdir(path)


def check_files(paths: List[str], file_ext: Optional[str] = None) -> bool:
    """
    Checks this given files to determine if they exist.
    :param paths: The paths to check.
    :param file_ext: An optional file extension to filter against.
    :return: True if all paths exist, False otherwise
    """
    invalid_paths: List[str] = list(
        filter(lambda path: not check_path(path, file_ext=file_ext), paths)
    )
    if len(invalid_paths) > 0:
        log.error("%d invalid paths found", len(invalid_paths))
        for invalid_path in invalid_paths:
            log.error("Invalid path %s", invalid_path)
        return False
    return True


def check_out_dir(out_dir: Optional[str] = None) -> bool:
    """
    Checks if a given directory exists.
    :param out_dir: The directory to check.
    :return: True if it exists, False otherwise.
    """
    if out_dir is not None and not check_path(out_dir, path_is_file=False):
        log.error("out_dir is invalid: %s", out_dir)
        return False
    return True


def determine_exit(status: bool) -> None:
    """
    Determine the exit status and exit the CLI.
    :param status: True will exit with a status of 0 and False will exit with a status of 1.
    """
    if status:
        log.info("Exiting with status = 0")
        sys.exit(0)

    log.error("Exiting with status = 1")
    sys.exit(1)


def rdvxz_to_rdvxm(args) -> None:
    """
    Convert rdvxz to rdvxm
    :param args: Args from argparse.
    """
    if not check_files(args.rdvxz_paths, ".rdvxz"):
        determine_exit(False)

    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(conversions.rdvxz_to_rdvxm(args.rdvxz_paths, args.out_dir))


def rdvxm_to_rdvxz(args) -> None:
    """
    Convert rdvxm to rdvxz
    :param args: Args from argparse.
    """
    if not check_files(args.rdvxm_paths, ".rdvxm"):
        determine_exit(False)

    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(conversions.rdvxm_to_rdvxz(args.rdvxm_paths, args.out_dir))


def rdvxz_to_json_args(args) -> None:
    """
    Wrapper function that calls the to_json conversion.
    :param args: Args from argparse.
    """
    if not check_files(args.rdvxz_paths, ".rdvxz"):
        determine_exit(False)

    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(conversions.rdvxz_to_json(args.rdvxz_paths, args.out_dir))


def rdvxm_to_json_args(args) -> None:
    """
    Wrapper function that calls the to_json conversion.
    :param args: Args from argparse.
    """
    if not check_files(args.rdvxm_paths, ".rdvxm"):
        determine_exit(False)

    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(conversions.rdvxm_to_json(args.rdvxm_paths, args.out_dir))


def json_to_rdvxz_args(args) -> None:
    """
    Wrapper function that calls the to_rdvxz conversion.
    :param args: Args from argparse.
    """
    if not check_files(args.json_paths, ".json"):
        determine_exit(False)

    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(conversions.json_to_rdvxz(args.json_paths, args.out_dir))


def json_to_rdvxm_args(args) -> None:
    """
    Wrapper function that calls the to_rdvxm conversion.
    :param args: Args from argparse.
    """
    if not check_files(args.json_paths, ".json"):
        determine_exit(False)

    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(conversions.json_to_rdvxm(args.json_paths, args.out_dir))


def rdvxz_print_stdout_args(args) -> None:
    """
    Wrapper function that calls the print to stdout.
    :param args: Args from argparse.
    """
    if not check_files(args.rdvxz_paths, ".rdvxz"):
        determine_exit(False)

    determine_exit(conversions.rdvxz_print_stdout(args.rdvxz_paths))


def rdvxm_print_stdout_args(args) -> None:
    """
    Wrapper function that calls the print to stdout.
    :param args: Args from argparse.
    """
    if not check_files(args.rdvxm_paths, ".rdvxm"):
        determine_exit(False)

    determine_exit(conversions.rdvxm_print_stdout(args.rdvxm_paths))


def validate_rdvxm_args(args) -> None:
    """
    Validates the args
    :param args: Args from argparse
    """
    if not check_files(args.rdvxm_paths, ".rdvxm"):
        determine_exit(False)

    determine_exit(conversions.validate_rdvxm(args.rdvxm_paths))


def data_req_args(args) -> None:
    """
    Wrapper function that calls the data_req.
    :param args: Args from argparse.
    """
    if not check_out_dir(args.out_dir):
        determine_exit(False)

    api_type: DataRangeReqType = DataRangeReqType[args.api_type]

    # Rebuild RedVox config from potentially optional passed in args
    if args.email is None:
        log.error(
            f"The argument 'email' is required, but was not found in the environment or provided."
        )
        determine_exit(False)

    if args.password is None:
        log.error(
            f"The argument 'password' is required, but was not found in the environment or provided."
        )
        determine_exit(False)

    redvox_config: RedVoxConfig = RedVoxConfig(
        args.email,
        args.password,
        args.protocol,
        args.host,
        args.port,
        args.secret_token,
    )

    determine_exit(
        data_req.make_data_req(
            args.out_dir,
            redvox_config,
            args.req_start_s,
            args.req_end_s,
            args.station_ids,
            api_type,
            args.retries,
            args.timeout,
            not args.disable_timing_correction
        )
    )


def data_req_report(
    redvox_config: RedVoxConfig,
    report_id: str,
    out_dir: str,
    retries: int,
) -> bool:
    """
    Uses the built-in cloud based HTTP API to generate a signed URL for report data and then downloads the report data.
    :param report_id: The full RedVox report id.
    :param out_dir: The output directory to play the report distribution.
    :param retries: Number of times to attempt to retry the download on failed attempts.
    """
    client = cloud_client.CloudClient(redvox_config)
    resp: Optional[data_api.ReportDataResp] = client.request_report_data(report_id)
    client.close()

    if resp:
        resp.download_fs(out_dir, retries)
        return True

    log.error("Response was None")
    return False


def data_req_report_args(args) -> None:
    """
    Wrapper function that calls the data_req_report.
    :param args: Args from argparse.
    """
    if not check_out_dir(args.out_dir):
        determine_exit(False)

    # Rebuild RedVox config from potentially optional passed in args
    if args.email is None:
        log.error(
            f"The argument 'email' is required, but was not found in the environment or provided."
        )
        determine_exit(False)

    if args.password is None:
        log.error(
            f"The argument 'password' is required, but was not found in the environment or provided."
        )
        determine_exit(False)

    redvox_config: RedVoxConfig = RedVoxConfig(
        args.email,
        args.password,
        args.protocol,
        args.host,
        args.port,
        args.secret_token,
    )

    determine_exit(
        data_req_report(
            redvox_config,
            args.report_id,
            args.out_dir,
            args.retries,
        )
    )


def gallery(rdvxm_paths: List[str]) -> bool:
    """
    Displays a gallery of images from the combined images collected from the given paths.
    :param rdvxm_paths: Paths to collect images from.
    :return: True if this completes successfully, False otherwise
    """
    # Create a new image sensor to hold images from all packets
    try:
        from redvox.api1000.gui.image_viewer import start_gui
        image: Image = Image.new()
        # noinspection PyTypeChecker
        image.set_image_codec(ImageCodec.JPG)

        packets: List[WrappedRedvoxPacketM] = list(
            map(WrappedRedvoxPacketM.from_compressed_path, rdvxm_paths)
        )

        for packet in packets:
            image_sensor: Optional[Image] = packet.get_sensors().get_image()
            if image_sensor is not None:
                image.get_timestamps().append_timestamps(
                    image_sensor.get_timestamps().get_timestamps()
                )
                image.append_values(image_sensor.get_samples())

        start_gui(image)
        return True

    except ImportError:
        import warnings
        warnings.warn("GUI dependencies are not installed. Install the 'GUI' extra to enable this functionality.")


def gallery_args(args) -> None:
    """
    CLI function for opening image gallery.
    :param args: Args for passing to gallery function.
    """
    if not check_files(args.rdvxm_paths):
        determine_exit(False)

    determine_exit(gallery(args.rdvxm_paths))


def sort_unstructured(
    input_dir: str, out_dir: Optional[str] = None, copy: bool = True
) -> bool:
    out_dir = out_dir if out_dir is not None else "."
    io.sort_unstructured_redvox_data(input_dir, out_dir, copy=copy)
    return True


def sort_unstructured_args(args) -> None:
    if not check_out_dir(args.input_dir):
        determine_exit(False)

    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(sort_unstructured(args.input_dir, args.out_dir, not args.mv))


def main():
    """
    Entry point into the CLI.
    """
    redvox_config: Optional[RedVoxConfig] = RedVoxConfig.find()

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        "redvox-cli",
        description="Command line tools for viewing, converting,"
        " and downloading RedVox data.",
    )
    parser.add_argument(
        "--verbose", "-v", help="Enable verbose logging", action="count", default=0
    )

    sub_parser = parser.add_subparsers()
    sub_parser.required = True
    sub_parser.dest = "command"

    # Cloud data retrieval
    cloud_download_parser = sub_parser.add_parser("cloud-download")
    cloud_download_parser.set_defaults(func=lambda _: cloud_data_retrieval.run_gui())

    # Gallery
    gallery_parser = sub_parser.add_parser("gallery")
    gallery_parser.add_argument(
        "rdvxm_paths", help="One or more rdvxm files", nargs="+"
    )
    gallery_parser.set_defaults(func=gallery_args)

    # rdvxz -> rdvxm
    rdvxz_to_rdvxm_parser = sub_parser.add_parser(
        "rdvxz-to-rdvxm", help="Convert rdvxz (API 900) to rdvxm (API 1000/M) files"
    )
    rdvxz_to_rdvxm_parser.add_argument(
        "rdvxz_paths",
        help="One or more rdvxz files to convert to json files",
        nargs="+",
    )
    rdvxz_to_rdvxm_parser.add_argument(
        "--out-dir",
        "-o",
        help="Optional output directory (will use same directory as source files by "
        "default)",
    )
    rdvxz_to_rdvxm_parser.set_defaults(func=rdvxz_to_rdvxm)

    # rdvxm -> rdvxz
    rdvxm_to_rdvxz_parser = sub_parser.add_parser(
        "rdvxm-to-rdvxz", help="Convert rdvxm (API 1000/M) to rdvxx (API 900) files"
    )
    rdvxm_to_rdvxz_parser.add_argument(
        "rdvxm_paths",
        help="One or more rdvxm files to convert to json files",
        nargs="+",
    )
    rdvxm_to_rdvxz_parser.add_argument(
        "--out-dir",
        "-o",
        help="Optional output directory (will use same directory as source files by "
        "default)",
    )
    rdvxm_to_rdvxz_parser.set_defaults(func=rdvxm_to_rdvxz)

    # rdvxz -> json
    rdvxz_to_json_parser = sub_parser.add_parser(
        "rdvxz-to-json", help="Convert rdvxz files to json files"
    )
    rdvxz_to_json_parser.add_argument(
        "rdvxz_paths",
        help="One or more rdvxz files to convert to json files",
        nargs="+",
    )
    rdvxz_to_json_parser.add_argument(
        "--out-dir",
        "-o",
        help="Optional output directory (will use same directory as source files by "
        "default)",
    )
    rdvxz_to_json_parser.set_defaults(func=rdvxz_to_json_args)

    # rdvxm -> json
    rdvxm_to_json_parser = sub_parser.add_parser(
        "rdvxm-to-json", help="Convert rdvxm files to json files"
    )
    rdvxm_to_json_parser.add_argument(
        "rdvxm_paths",
        help="One or more rdvxm files to convert to json files",
        nargs="+",
    )
    rdvxm_to_json_parser.add_argument(
        "--out-dir",
        "-o",
        help="Optional output directory (will use same directory as source files by "
        "default)",
    )
    rdvxm_to_json_parser.set_defaults(func=rdvxm_to_json_args)

    # json -> rdvxz
    json_to_rdvxz_parser = sub_parser.add_parser(
        "json-to-rdvxz", help="Convert json files to rdvxz files"
    )
    json_to_rdvxz_parser.add_argument(
        "json_paths", help="One or more json files to convert to rdvxz files", nargs="+"
    )
    json_to_rdvxz_parser.add_argument(
        "--out-dir",
        "-o",
        help="Optional output directory (will use same directory as source files by "
        "default)",
    )
    json_to_rdvxz_parser.set_defaults(func=json_to_rdvxz_args)

    # json -> rdvxm
    json_to_rdvxm_parser = sub_parser.add_parser(
        "json-to-rdvxm", help="Convert json files to rdvxm files"
    )
    json_to_rdvxm_parser.add_argument(
        "json_paths", help="One or more json files to convert to rdvxm files", nargs="+"
    )
    json_to_rdvxm_parser.add_argument(
        "--out-dir",
        "-o",
        help="Optional output directory (will use same directory as source files by "
        "default)",
    )
    json_to_rdvxm_parser.set_defaults(func=json_to_rdvxm_args)

    # sort unstructured data into structured data
    sort_unstructured_parser = sub_parser.add_parser(
        "sort-unstructured",
        help="Sorts unstructured RedVox files into their structured counterpart",
    )
    sort_unstructured_parser.add_argument(
        "input_dir",
        help="Directory containing RedVox files to sort into a structured layout",
    )
    sort_unstructured_parser.add_argument(
        "--out-dir",
        "-o",
        help="Optional output directory (current working directory by default)",
    )
    sort_unstructured_parser.add_argument(
        "--mv",
        help="When set, file contents will be moved to the structured layout rather than copied.",
        action="store_true",
    )
    sort_unstructured_parser.set_defaults(func=sort_unstructured_args)

    # print rdvxz
    rdvxz_print_parser = sub_parser.add_parser(
        "print-z", help="Print contents of rdvxz files to stdout"
    )
    rdvxz_print_parser.add_argument(
        "rdvxz_paths", help="One or more rdvxz files to print", nargs="+"
    )
    rdvxz_print_parser.set_defaults(func=rdvxz_print_stdout_args)

    # print rdvxm
    rdvxm_print_parser = sub_parser.add_parser(
        "print-m", help="Print contents of rdvxm files to stdout"
    )
    rdvxm_print_parser.add_argument(
        "rdvxm_paths", help="One or more rdvxm files to print", nargs="+"
    )
    rdvxm_print_parser.set_defaults(func=rdvxm_print_stdout_args)

    # validation
    rdvxm_validation_parser = sub_parser.add_parser(
        "validate-m", help="Validate the structure of API M files"
    )
    rdvxm_validation_parser.add_argument(
        "rdvxm_paths", help="One or more rdvxm files to print", nargs="+"
    )
    rdvxm_validation_parser.set_defaults(func=validate_rdvxm_args)

    # data_req
    data_req_parser = sub_parser.add_parser(
        "data-req", help="Request bulk RedVox data from RedVox servers"
    )
    data_req_parser.add_argument(
        "--email",
        help="redvox.io account email",
        default=map_or_default(redvox_config, lambda config: config.username, None),
    )
    data_req_parser.add_argument(
        "--password",
        help="redvox.io account password",
        default=map_or_default(redvox_config, lambda config: config.password, None),
    )
    data_req_parser.add_argument(
        "--out-dir",
        help="The output directory that RedVox files will be written to (default=.)",
        default=".",
    )
    data_req_parser.add_argument(
        "--disable-timing-correction",
        help="Disables query timing correction",
        default=False,
        action="store_true"
    )
    data_req_parser.add_argument(
        "--retries",
        help="The number of times the client should retry getting a file on failure "
        "(default=1)",
        default=1,
        choices=set(range(0, 6)),
        type=int,
    )
    data_req_parser.add_argument(
        "--host",
        help="Data server host",
        default=map_or_default(redvox_config, lambda config: config.host, "redvox.io"),
    )
    data_req_parser.add_argument(
        "--port",
        type=int,
        help="Data server port",
        default=map_or_default(redvox_config, lambda config: config.port, 8080),
    )
    data_req_parser.add_argument(
        "--protocol",
        help="One of either http or https",
        choices=["https", "http"],
        default=map_or_default(redvox_config, lambda config: config.protocol, "https"),
    )
    data_req_parser.add_argument(
        "--secret-token",
        help="A shared secret token provided by RedVox required for accessing the data "
        "request service",
        default=map_or_default(redvox_config, lambda config: config.secret_token, None),
    )
    data_req_parser.add_argument(
        "--api-type",
        help="Data API to be retrieved",
        choices=["API_900", "API_1000", "API_900_1000"],
        default="API_900_1000",
    )
    data_req_parser.add_argument(
        "--timeout",
        help="Read timeout in seconds (default=10 seconds)",
        type=int,
        default=10
    )
    data_req_parser.add_argument(
        "req_start_s",
        type=int,
        help="Data request start as number of seconds since the epoch UTC",
    )
    data_req_parser.add_argument(
        "req_end_s",
        type=int,
        help="Data request end as number of seconds since the epoch UTC",
    )
    data_req_parser.add_argument(
        "station_ids", nargs="+", help="A list of RedVox ids delimited by a space"
    )
    data_req_parser.set_defaults(func=data_req_args)

    # data req report
    data_req_report_parser = sub_parser.add_parser(
        "data-req-report", help="Request bulk RedVox data from the RedVox servers"
    )
    data_req_report_parser.add_argument(
        "--out-dir",
        help="The output directory that RedVox files will be written to (default=.)",
        default=".",
    )
    data_req_report_parser.add_argument(
        "--email",
        help="redvox.io account email",
        default=map_or_default(redvox_config, lambda config: config.username, None),
    )
    data_req_report_parser.add_argument(
        "--password",
        help="redvox.io account password",
        default=map_or_default(redvox_config, lambda config: config.password, None),
    )
    data_req_report_parser.add_argument(
        "--retries",
        help="The number of times the client should retry getting a file on failure "
        "(default=1)",
        default=1,
        choices=set(range(0, 6)),
        type=int,
    )
    data_req_report_parser.add_argument(
        "--host",
        help="Data server host",
        default=map_or_default(redvox_config, lambda config: config.host, "redvox.io"),
    )
    data_req_report_parser.add_argument(
        "--port",
        type=int,
        help="Data server port",
        default=map_or_default(redvox_config, lambda config: config.port, 8080),
    )
    data_req_report_parser.add_argument(
        "--protocol",
        help="One of either http or https (default https)",
        choices=["https", "http"],
        default=map_or_default(redvox_config, lambda config: config.protocol, "https"),
    )
    data_req_report_parser.add_argument(
        "--secret-token",
        help="A shared secret token provided by RedVox required for accessing the data "
        "request service",
        default=map_or_default(redvox_config, lambda config: config.secret_token, None),
    )
    data_req_report_parser.add_argument(
        "report_id",
        type=str,
        help="The full report id that data is being requested for",
    )
    data_req_report_parser.set_defaults(func=data_req_report_args)

    # Parse the args
    args = parser.parse_args()

    # Setup logging
    log_levels: Dict[int, str] = {0: "WARN", 1: "INFO", 2: "DEBUG"}
    log_level: str = (
        log_levels[args.verbose] if args.verbose in log_levels else log_levels[0]
    )
    logging.basicConfig(
        level=log_level,
        format="[%(levelname)s:%(process)d:%(filename)s:%(module)s:%(funcName)s:%(lineno)d:%(asctime)s]"
        " %(message)s",
    )

    log.info("Running with args=%s and log_level=%s", str(args), log_level)

    # Try calling the appropriate handler
    # pylint: disable=W0703
    try:
        args.func(args)
    except Exception as e:
        log.error("Encountered an error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
