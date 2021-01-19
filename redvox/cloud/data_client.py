"""
This module provides a custom work-stealing thread pool for downloading API M data in parallel.
"""

from dataclasses import dataclass
import time
from typing import List
from multiprocessing import cpu_count, Manager, Process, Queue
import queue

import requests

from redvox.cloud.data_io import download_file


@dataclass
class DownloadResult:
    """
    The result of downloading a file.
    """

    data_key: str
    resp_len: int


def download_process(
    input_queue: Queue, result_queue: Queue, out_dir: str, retries: int
) -> None:
    """
    A function that runs in a separate process for downloading RedVox data.
    :param input_queue: A shared queue containing the list of items to be downloaded.
    :param result_queue: A queue used to send results from the process to the caller.
    :param out_dir: The directory downloaded data should be stored to.
    :param retries: Number of times to retry a failed download.
    """
    session: requests.Session = requests.Session()
    try:
        # While there is still data in the queue, retrieve it.
        while True:
            url: str = input_queue.get_nowait()
            data_key: str
            resp_len: int
            data_key, resp_len = download_file(url, session, out_dir, retries)
            result_queue.put(DownloadResult(data_key, resp_len), True, None)
    # Thrown when the queue is empty
    except queue.Empty:
        session.close()


def download_files(
    urls: List[str], out_dir: str, retries: int, num_processes: int = cpu_count()
) -> None:
    """
    Downloads files in parallel from the provided URLs.
    :param urls: URLs to files to retrieve.
    :param out_dir: The base output directory where files should be stored.
    :param retries: The number of times to retry a failed download.
    :param num_processes: Number of processes to create for downloading data.
    """
    manager: Manager = Manager()
    url_queue: Queue = manager.Queue(len(urls))
    result_queue: Queue = manager.Queue(len(urls))
    processes: List[Process] = []

    # Add all URLs to shared queue
    for url in urls:
        url_queue.put(url)

    # Create the process pool
    for _ in range(num_processes):
        process: Process = Process(
            target=download_process, args=(url_queue, result_queue, out_dir, retries)
        )
        processes.append(process)
        process.start()

    # Display download status
    i: int = 0
    total_bytes: int = 0
    start_time = time.monotonic_ns()
    while i < len(urls):
        res: DownloadResult = result_queue.get(True, None)
        timestamp = time.monotonic_ns()
        time_range = (timestamp - start_time) / 1_000_000_000.0
        percentage: float = (float(i + 1) / float(len(urls))) * 100.0
        remaining: float = ((100.0 / percentage) * time_range) - time_range

        total_bytes += res.resp_len
        print(
            f"\r[{(i + 1):5} / {len(urls):5}] [{percentage:04.1f}%] "
            f"[{total_bytes:10} bytes] [est time remaining {remaining:06.1f}s] {res.data_key:>55}",
            end="",
        )
        i += 1

    # Wait for all processes in pool to finish
    for process in processes:
        process.join()
