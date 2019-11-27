"""
This module provides a CLI for performing bulk data downloads.
"""

import argparse
import bz2
import logging
import multiprocessing
import os
from typing import Dict, List, Tuple, Union

import requests

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d\n -> %(message)s',
                    level=logging.DEBUG)


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


def handle_ok_resp(resp: requests.Response, out_dir: str):
    logging.debug("Handling ok response")

    compressed_index = resp.content
    logging.debug(f"Got compressed index ({len(compressed_index)} bytes)")

    decompressed_index = bz2.decompress(compressed_index)
    logging.debug(f"Got decompressed index ({len(decompressed_index)} bytes)")

    str_data = decompressed_index.decode()
    parsed_data = list(map(lambda line: line.strip(), str_data.split("\n")))
    logging.debug(f"Got parsed data ({len(parsed_data)} entries)")


    session: requests.Session = requests.Session()
    pool = multiprocessing.Pool(processes=4)
    zipped_data = list(map(lambda line: (line, session, out_dir), parsed_data))
    handler = pool.starmap_async(get_file, zipped_data, callback=lambda t: logging.debug(f"Saved {t[0]} {t[1]} bytes"))
    handler.wait()

    # for line in parsed_data:
    #     get_file(line, session, out_dir)


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


if __name__ == "__main__":
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
