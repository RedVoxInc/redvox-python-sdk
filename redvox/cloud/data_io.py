"""
This module contains functions for downloading data from AWS S3 via signed URLs.
"""

import logging
import multiprocessing
import os
from typing import Callable, List, Tuple, Optional

import numpy as np
import requests

# pylint: disable=C0103
log = logging.getLogger(__name__)


class ProcessPool:
    """
    Creates a process pool used for fetching files from S3.
    """

    def __init__(self,
                 num_processes: int,
                 func: Callable[[List[str], str, int], None],
                 data: List[str],
                 out_dir: str,
                 retries: int):
        """
        Instantiates a new process pool.
        :param num_processes: The number of processes to create.
        :param func: The function to run which should take a list of strings representing data keys and a string
                     representing the out_dir.
        :param data: The list of data keys to process.
        :param out_dir: The output directory to write the data files to.
        :param retries: The number of times the HTTP client should retry getting a file.
        """

        self.num_processes: int = num_processes
        self.func: Callable[[List[str], str, int], None] = func
        self.data: List[List[str]] = list(map(list, np.array_split(np.array(data), num_processes)))
        self.out_dir = out_dir
        self.retries = retries

    def run(self):
        """
        Runs this process pool. This will block until all processes finish fetching data.
        """
        processes: List[multiprocessing.Process] = []

        for i in range(self.num_processes):
            process: multiprocessing.Process = multiprocessing.Process(target=self.func, args=(self.data[i],
                                                                                               self.out_dir,
                                                                                               self.retries))
            processes.append(process)
            process.start()

        # Wait for all processes to finish
        for process in processes:
            process.join()


def find_between(start: str, end: str, contents: str) -> str:
    """
    Find the string contents between two other strings.
    :param start: The first string.
    :param end: The seconds string.
    :param contents: The full string.
    :return: The contents between the start and end strings.
    """
    s_idx = contents.find(start)
    e_idx = contents.find(end)
    return contents[s_idx + len(start):e_idx]


def get_file(url: str,
             retries: int,
             session: requests.Session = requests.Session()) -> Optional[bytes]:
    """
    Attempts to download a file with a configurable amount of retries.
    :param url: The url to download.
    :param retries: Number of retries.
    :param session: An instance of a session.
    :return: The bytes of the file.
    """
    try:
        resp: requests.Response = session.get(url)
        if resp.status_code == 200:
            return resp.content
        else:
            log.error("Received error response when requesting data for url=%s: %d %s",
                      url,
                      resp.status_code,
                      resp.text)
            if retries > 0:
                log.info("Retrying with %d retries", retries)
                return get_file(url, retries - 1, session)

            log.error("All retries exhausted, could not get %s", url)
            return None
    except Exception as e:
        log.error("Encountered an error while getting data for %s: %s", url, str(e))
        if retries > 0:
            log.info("Retrying with %d retries", retries)
            return get_file(url, retries - 1, session)
        log.error("All retries exhausted, could not get %s", url)
        return None


def download_file(url: str,
                  session: requests.Session,
                  out_dir: str,
                  retries: int) -> Tuple[str, int]:
    """
    Attempts to download a file from S3.
    :param url: The URL to retrieve.
    :param session: The HTTP session.
    :param out_dir: The output directory where files will be stored.
    :param retries: The number of times to retry failed file downloads.
    :return: A tuple containing the data_key and the length of the download response.
    """
    buf: Optional[bytes] = get_file(url, retries, session)

    if buf:
        data_key = find_between("/rdvxdata/", "?X-Amz-Algorithm=", url)

        directory = os.path.dirname(data_key)
        full_dir = f"{out_dir}/{directory}"
        if not os.path.exists(full_dir):
            log.info("Directory %s does not exist, creating it", full_dir)
            os.makedirs(full_dir)

        full_path = f"{out_dir}/{data_key}"
        with open(full_path, "wb") as fout:
            bytes_written = fout.write(buf)
            log.info("Wrote %s %d", full_path, bytes_written)

        return data_key, len(buf)

    return "", 0


def download_files(urls: List[str], out_dir: str, retries: int) -> None:
    """
    Download files from S3.
    :param urls: The URL of the files to download.
    :param out_dir: The output directory to store the downloaded files.
    :param retries: The number of retries for failed downloads.
    """
    session: requests.Session = requests.Session()

    for url in urls:
        data_key, resp_len = download_file(url, session, out_dir, retries)
        log.info("Recv %s with len=%d", data_key, resp_len)

    session.close()


def download_files_parallel(urls: List[str], out_dir: str, retries: int) -> None:
    """
    Distributes the file downloading across a process pool.
    :param urls: The signed URLs to download.
    :param out_dir: The output directory.
    :param retries: The number of times to retry downloading a file on failure.
    """
    process_pool: ProcessPool = ProcessPool(4,
                                            download_files,
                                            urls,
                                            out_dir,
                                            retries)
    process_pool.run()
