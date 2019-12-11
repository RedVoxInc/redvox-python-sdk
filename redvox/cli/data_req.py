#!/usr/bin/env python3

"""
This module provides a CLI for performing bulk data downloads.
"""

import argparse
import bz2
import logging
import multiprocessing
import os
from typing import Callable, Dict, List, Tuple, Union

import numpy as np
import requests

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d\n -> %(message)s',
                    level=logging.DEBUG)


class ProcessPool:
    """
    Creates a process pool used for fetching the files from S3.
    """

    def __init__(self,
                 num_processes: int,
                 func: Callable[[List[str], str], None],
                 data: List[str],
                 out_dir: str):
        """
        Instantiates a new process pool.
        :param num_processes: The number of processes to create.
        :param func: The function to run which should take a list of strings representing data keys and a string
                     representing the out_dir.
        :param data: The list of data keys to process.
        :param out_dir: The output directory to write the data files to.
        """

        self.num_processes: int = num_processes
        self.func: Callable[[List[str]], None] = func
        self.data: List[List[str]] = list(map(list, np.array_split(np.array(data), num_processes)))
        self.out_dir = out_dir

    def run(self):
        processes: List[multiprocessing.Process] = []

        for i in range(self.num_processes):
            process: multiprocessing.Process = multiprocessing.Process(target=self.func, args=(self.data[i],
                                                                                               self.out_dir))
            processes.append(process)
            process.start()

        for process in processes:
            process.join()


def find_between(start: str, end: str, contents: str) -> str:
    s = contents.find(start)
    e = contents.find(end)
    return contents[s + len(start):e]


def get_file(url: str, session: requests.Session, out_dir: str) -> Tuple[str, int]:
    resp: requests.Response = session.get(url)
    if resp.status_code == 200:
        data_key = find_between("/rdvxdata/", "?X-Amz-Algorithm=", url)

        directory = os.path.dirname(data_key)
        full_dir = f"{out_dir}/{directory}"
        if not os.path.exists(full_dir):
            logging.debug(f"Directory {full_dir} does not exist, creating it")
            os.makedirs(full_dir)

        full_path = f"{out_dir}/{data_key}"
        with open(full_path, "wb") as fout:
            fout.write(resp.content)

        return data_key, len(resp.content)

    else:
        logging.error(f"Received error response when requesting data for url={url}: {resp.status_code} {resp.text}")
        return "", 0


def get_files(urls: List[str], out_dir: str) -> None:
    session: requests.Session = requests.Session()

    for url in urls:
        data_key, resp_len = get_file(url, session, out_dir)


def handle_ok_resp(resp: requests.Response, out_dir: str):
    logging.debug("Handling ok response")

    compressed_index: bytes = resp.content
    logging.debug(f"Got compressed index ({len(compressed_index)} bytes)")

    decompressed_index: bytes = bz2.decompress(compressed_index)
    logging.debug(f"Got decompressed index ({len(decompressed_index)} bytes)")

    str_data: str = decompressed_index.decode()
    parsed_data: List[str] = list(map(lambda line: line.strip(), str_data.split("\n")))
    logging.debug(f"Got parsed data ({len(parsed_data)} entries)")

    process_pool: ProcessPool = ProcessPool(4, get_files, parsed_data, out_dir)
    process_pool.run()


def make_data_req(out_dir: str,
                  host: str,
                  port: int,
                  email: str,
                  password: str,
                  req_start_s: int,
                  req_end_s: int,
                  redvox_ids: List[str]):
    req: Dict[str, Union[str, int, List[str]]] = {"email": email,
                                                  "password": password,
                                                  "start_ts_s": req_start_s,
                                                  "end_ts_s": req_end_s,
                                                  "redvox_ids": redvox_ids}
    url: str = f"http://{host}:{port}/req"

    resp: requests.Response = requests.post(url, json=req)

    if resp.status_code == 200:
        logging.debug(f"Received ok response.")
        handle_ok_resp(resp, out_dir)
    elif resp.status_code == 400:
        logging.error(f"Bad request error: {resp.status_code} {resp.text}")
    elif resp.status_code == 401:
        logging.error(f"Authentication error: {resp.status_code} {resp.text}")
    else:
        logging.error(f"Server error: {resp.status_code} {resp.text}")


def main():
    """
    Entry point to data_req.
    """
    parser = argparse.ArgumentParser("redvox-data-req",
                                     description="A CLI utility for performing batch downloads of RedVox data sets.")

    parser.add_argument("out_dir",
                        help="The output directory that RedVox files will be written to.")
    parser.add_argument("host",
                        help="Data server host")
    parser.add_argument("port",
                        type=int,
                        help="Data server port")
    parser.add_argument("email",
                        help="redvox.io account email")
    parser.add_argument("password",
                        help="redvox.io account password")
    parser.add_argument("req_start_s",
                        type=int,
                        help="Data request start as number of seconds since the epoch UTC")
    parser.add_argument("req_end_s",
                        type=int,
                        help="Data request end as number of seconds since the epoch UTC")
    parser.add_argument("redvox_ids",
                        nargs="+",
                        help="A list of RedVox ids delimited by a space")

    args = parser.parse_args()

    logging.debug(f"Starting data request with the following configuration: {args}")

    make_data_req(args.out_dir,
                  args.host,
                  args.port,
                  args.email,
                  args.password,
                  args.req_start_s,
                  args.req_end_s,
                  args.redvox_ids)


if __name__ == "__main__":
    main()
