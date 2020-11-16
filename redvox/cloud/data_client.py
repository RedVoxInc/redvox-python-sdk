from dataclasses import dataclass
from typing import List
from multiprocessing import cpu_count, Manager, Process, Queue
import time

import requests

from redvox.cloud.data_io import download_file


@dataclass
class DownloadResult:
    data_key: str
    resp_len: int


def download_process(input_queue: Queue, result_queue: Queue, out_dir: str, retries: int):
    session: requests.Session = requests.Session()
    try:
        while True:
            url: str = input_queue.get(True, None)
            data_key: str
            resp_len: int
            data_key, resp_len = download_file(url, session, out_dir, retries)
            result_queue.put(DownloadResult(data_key, resp_len), True, None)
    # Thrown when the queue is closed by the client
    except (ValueError, OSError):
        session.close()


def download_files(urls: List[str], out_dir: str, retries: int, num_processes: int = cpu_count()) -> None:
    manager: Manager = Manager()
    url_queue: Queue = manager.Queue(len(urls))
    result_queue: Queue = manager.Queue(len(urls))
    processes: List[Process] = []

    # Add all URLs to shared queue
    for url in urls:
        url_queue.put(url)

    # Create the process pool
    for _ in range(num_processes):
        process: Process = Process(target=download_process, args=(url_queue, result_queue, out_dir, retries))
        processes.append(process)
        process.start()

    i: int = 0
    total_bytes: int = 0
    start_time = time.monotonic_ns()
    while i < len(urls):
        res: DownloadResult = result_queue.get(True, None)
        ts = time.monotonic_ns()
        time_range = (ts - start_time) / 1_000_000_000.0
        percentage: float = (float(i + 1) / float(len(urls))) * 100.0
        remaining: float = ((100.0 / percentage) * time_range) - time_range

        total_bytes += res.resp_len
        print(f"\r[{(i + 1):5} / {len(urls):5}] [{percentage:3.2f}%] "
              f"[{total_bytes:6} bytes] [est time remaining {remaining:.1f}s] {res.data_key}",
              end="")
        i += 1

    # Wait for all processes in pool to finish
    for process in processes:
        process.join()
