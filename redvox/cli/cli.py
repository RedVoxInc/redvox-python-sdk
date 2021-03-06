"""
This module provides a command line interface (CLI) for converting, viewing, and downloading RedVox data files.
"""

import argparse
import logging
import os.path
import sys
from typing import Dict, List, Optional

import redvox.cloud.api as cloud_api
import redvox.cloud.client as cloud_client
import redvox.cloud.data_api as data_api
import redvox.cli.conversions as conversions
import redvox.cli.data_req as data_req

# pylint: disable=C0103
log = logging.getLogger(__name__)


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
    """
    Checks this given files to determine if they exist.
    :param paths: The paths to check.
    :param file_ext: An optional file extension to filter against.
    :return: True if all paths exist, False otherwise
    """
    invalid_paths: List[str] = list(filter(lambda path: not check_path(path, file_ext=file_ext), paths))
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


def to_json_args(args) -> None:
    """
    Wrapper function that calls the to_json conversion.
    :param args: Args from argparse.
    """
    if not check_files(args.rdvxz_paths, ".rdvxz"):
        determine_exit(False)

    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(conversions.to_json(args.rdvxz_paths, args.out_dir))


def to_rdvxz_args(args) -> None:
    """
    Wrapper function that calls the to_rdvxz conversion.
    :param args: Args from argparse.
    """
    if not check_files(args.json_paths, ".json"):
        determine_exit(False)

    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(conversions.to_rdvxz(args.json_paths, args.out_dir))


def print_stdout_args(args) -> None:
    """
    Wrapper function that calls the print to stdout.
    :param args: Args from argparse.
    """
    if not check_files(args.rdvxz_paths, ".rdvxz"):
        determine_exit(False)

    determine_exit(conversions.print_stdout(args.rdvxz_paths))


def data_req_args(args) -> None:
    """
    Wrapper function that calls the data_req.
    :param args: Args from argparse.
    """
    if not check_out_dir(args.out_dir):
        determine_exit(False)

    determine_exit(data_req.make_data_req(args.out_dir,
                                          args.protocol,
                                          args.host,
                                          args.port,
                                          args.email,
                                          args.password,
                                          args.req_start_s,
                                          args.req_end_s,
                                          args.redvox_ids,
                                          args.retries,
                                          args.secret_token))


def data_req_report(protocol: str,
                    host: str,
                    port: int,
                    email: str,
                    password: str,
                    report_id: str,
                    out_dir: str,
                    retries: int,
                    secret_token: Optional[str] = None) -> bool:
    """
    Uses the built-in cloud based HTTP API to generate a signed URL for report data and then downloads the report data.
    :param protocol: Either http or https.
    :param host: The data service host.
    :param port: The data service port.
    :param email: The email of the RedVox user.
    :param password: The password of the RedVox user.
    :param report_id: The full RedVox report id.
    :param out_dir: The output directory to play the report distribution.
    :param retries: Number of times to attempt to retry the download on failed attempts.
    :param secret_token: The shared secret if utilized by the API server.
    """
    api_config: cloud_api.ApiConfig = cloud_api.ApiConfig(protocol, host, port)
    client = cloud_client.CloudClient(email,
                                      password,
                                      api_conf=api_config,
                                      secret_token=secret_token)
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

    determine_exit(data_req_report(args.protocol,
                                   args.host,
                                   args.port,
                                   args.email,
                                   args.password,
                                   args.report_id,
                                   args.out_dir,
                                   args.retries,
                                   args.secret_token))


def main():
    """
    Entry point into the CLI.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser("redvox-cli",
                                                              description="Command line tools for viewing, converting,"
                                                                          " and downloading RedVox data.")
    parser.add_argument("--verbose",
                        "-v",
                        help="Enable verbose logging",
                        action="count",
                        default=0)

    sub_parser = parser.add_subparsers()
    sub_parser.required = True
    sub_parser.dest = "command"

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
                                 help="The output directory that RedVox files will be written to (default=.)",
                                 default=".")
    data_req_parser.add_argument("--retries",
                                 "-r",
                                 help="The number of times the client should retry getting a file on failure "
                                      "(default=1)",
                                 default=1,
                                 choices=set(range(0, 6)),
                                 type=int)
    data_req_parser.add_argument("--host",
                                 "-H",
                                 help="Data server host (default=redvox.io)",
                                 default="redvox.io")
    data_req_parser.add_argument("--port",
                                 "-p",
                                 type=int,
                                 help="Data server port (default=8080)",
                                 default=8080)
    data_req_parser.add_argument("--protocol",
                                 help="One of either http or https (default https)",
                                 choices=["https", "http"],
                                 default="https")
    data_req_parser.add_argument("--secret_token",
                                 help="A shared secret token provided by RedVox required for accessing the data "
                                      "request service")
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

    # data req report
    data_req_report_parser = sub_parser.add_parser("data_req_report",
                                                   help="Request bulk RedVox data from the RedVox servers")
    data_req_report_parser.add_argument("--out_dir",
                                        "-o",
                                        help="The output directory that RedVox files will be written to (default=.)",
                                        default=".")
    data_req_report_parser.add_argument("--retries",
                                        "-r",
                                        help="The number of times the client should retry getting a file on failure "
                                             "(default=1)",
                                        default=1,
                                        choices=set(range(0, 6)),
                                        type=int)
    data_req_report_parser.add_argument("--host",
                                        "-H",
                                        help="Data server host (default=redvox.io)",
                                        default="redvox.io")
    data_req_report_parser.add_argument("--port",
                                        "-p",
                                        type=int,
                                        help="Data server port (default=8080)",
                                        default=8080)
    data_req_report_parser.add_argument("--protocol",
                                        help="One of either http or https (default https)",
                                        choices=["https", "http"],
                                        default="https")
    data_req_report_parser.add_argument("--secret_token",
                                        help="A shared secret token provided by RedVox required for accessing the data "
                                             "request service")
    data_req_report_parser.add_argument("email",
                                        help="redvox.io account email")
    data_req_report_parser.add_argument("password",
                                        help="redvox.io account password")
    data_req_report_parser.add_argument("report_id",
                                        type=str,
                                        help="The full report id that data is being requested for")
    data_req_report_parser.set_defaults(func=data_req_report_args)

    # Parse the args
    args = parser.parse_args()

    # Setup logging
    log_levels: Dict[int, str] = {
        0: "WARN",
        1: "INFO",
        2: "DEBUG"
    }
    log_level: str = log_levels[args.verbose] if args.verbose in log_levels else log_levels[0]
    logging.basicConfig(level=log_level,
                        format="[%(levelname)s:%(process)d:%(filename)s:%(module)s:%(funcName)s:%(lineno)d:%(asctime)s]"
                               " %(message)s")

    log.info("Running with args=%s and log_level=%s",
             str(args),
             log_level)

    # Try calling the appropriate handler
    # pylint: disable=W0703
    try:
        args.func(args)
    except Exception as e:
        log.error("Encountered an error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
