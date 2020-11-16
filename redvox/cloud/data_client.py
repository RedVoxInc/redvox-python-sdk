import logging as log
from dataclasses import dataclass
from typing import List
from multiprocessing import cpu_count, Process, Queue

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
    url_queue: Queue = Queue(len(urls))
    result_queue: Queue = Queue(len(urls))
    processes: List[Process] = []

    for url in urls:
        url_queue.put(url, True, None)

    for _ in range(num_processes):
        process: Process = Process(target=download_process, args=(url_queue, result_queue, out_dir, retries))
        processes.append(process)
        process.run()

    while True:
        print(result_queue.get(True, None))

    pass
