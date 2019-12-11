#!/usr/bin/env python3

"""
This module provides a CLI for performing bulk data downloads.
"""

import bz2
import multiprocessing
import os
from typing import Callable, Dict, List, Tuple, Union

import numpy as np
import requests


def log(msg: str, verbose: bool) -> None:
    if verbose:
        print(msg)


class ProcessPool:
    """
    Creates a process pool used for fetching the files from S3.
    """

    def __init__(self,
                 num_processes: int,
                 func: Callable[[List[str], str], None],
                 data: List[str],
                 out_dir: str,
                 verbose: bool = False):
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
        self.verbose = verbose

    def run(self):
        processes: List[multiprocessing.Process] = []

        for i in range(self.num_processes):
            process: multiprocessing.Process = multiprocessing.Process(target=self.func, args=(self.data[i],
                                                                                               self.out_dir,
                                                                                               self.verbose))
            processes.append(process)
            process.start()

        for process in processes:
            process.join()


def find_between(start: str, end: str, contents: str) -> str:
    s = contents.find(start)
    e = contents.find(end)
    return contents[s + len(start):e]


def get_file(url: str, session: requests.Session, out_dir: str, verbose: bool = False) -> Tuple[str, int]:
    resp: requests.Response = session.get(url)
    if resp.status_code == 200:
        data_key = find_between("/rdvxdata/", "?X-Amz-Algorithm=", url)

        directory = os.path.dirname(data_key)
        full_dir = f"{out_dir}/{directory}"
        if not os.path.exists(full_dir):
            log(f"Directory {full_dir} does not exist, creating it", verbose)
            os.makedirs(full_dir)

        full_path = f"{out_dir}/{data_key}"
        with open(full_path, "wb") as fout:
            fout.write(resp.content)
            log(f"Wrote {full_path}", verbose)

        return data_key, len(resp.content)

    else:
        log(f"Received error response when requesting data for url={url}: {resp.status_code} {resp.text}", True)
        return "", 0


def get_files(urls: List[str], out_dir: str, verbose: bool = False) -> None:
    session: requests.Session = requests.Session()

    for url in urls:
        data_key, resp_len = get_file(url, session, out_dir, verbose)
        log(f"Recv {data_key} with len={resp_len}", verbose)


def handle_ok_resp(resp: requests.Response, out_dir: str, verbose: bool = False) -> bool:
    log("Handling ok response", verbose)

    compressed_index: bytes = resp.content
    log(f"Got compressed index ({len(compressed_index)} bytes)", verbose)

    decompressed_index: bytes = bz2.decompress(compressed_index)
    log(f"Got decompressed index ({len(decompressed_index)} bytes)", verbose)

    str_data: str = decompressed_index.decode()
    parsed_data: List[str] = list(map(lambda line: line.strip(), str_data.split("\n")))
    log(f"Got parsed data ({len(parsed_data)} entries)", verbose)

    process_pool: ProcessPool = ProcessPool(4, get_files, parsed_data, out_dir, verbose)
    process_pool.run()

    return True


def make_data_req(out_dir: str,
                  host: str,
                  port: int,
                  email: str,
                  password: str,
                  req_start_s: int,
                  req_end_s: int,
                  redvox_ids: List[str],
                  verbose: bool = False) -> bool:
    req: Dict[str, Union[str, int, List[str]]] = {"email": email,
                                                  "password": password,
                                                  "start_ts_s": req_start_s,
                                                  "end_ts_s": req_end_s,
                                                  "redvox_ids": redvox_ids}
    url: str = f"http://{host}:{port}/req"

    resp: requests.Response = requests.post(url, json=req)

    if resp.status_code == 200:
        log("Recv ok response.", verbose)
        return handle_ok_resp(resp, out_dir, verbose)
    elif resp.status_code == 400:
        log(f"Bad request error: {resp.status_code} {resp.text}", True)
        return False
    elif resp.status_code == 401:
        log(f"Authentication error: {resp.status_code} {resp.text}", True)
        return False
    else:
        log(f"Server error: {resp.status_code} {resp.text}", True)
        return False

