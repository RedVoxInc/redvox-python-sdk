"""
This module contains functions for downloading data from AWS S3 via signed URLs.
"""

import logging
import os
from typing import Tuple, Optional

import requests

# pylint: disable=C0103
log = logging.getLogger(__name__)


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
    return contents[s_idx + len(start) : e_idx]


def get_file(
    url: str, retries: int, session: requests.Session = requests.Session()
) -> Optional[bytes]:
    """
    Attempts to download a file with a configurable amount of retries.
    :param url: The url to download.
    :param retries: Number of retries.
    :param session: An instance of a session.
    :return: The bytes of the file.
    """
    # pylint: disable=W0702
    # noinspection PyBroadException
    try:
        resp: requests.Response = session.get(url)
        if resp.status_code == 200:
            return resp.content
        else:
            log.error(
                "Received error response when requesting data for url=%s: %d %s",
                url,
                resp.status_code,
                resp.text,
            )
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


def download_file(
    url: str, session: requests.Session, out_dir: str, retries: int
) -> Tuple[str, int]:
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
        if "/rdvxdata/" in url:
            data_key = find_between("/rdvxdata/", "?X-Amz-Algorithm=", url)
        else:
            data_key = find_between(
                "/rdvxdata.s3.amazonaws.com/", "?AWSAccessKeyId=", url
            )

        directory = os.path.dirname(data_key)
        full_dir = f"{out_dir}/{directory}"
        if not os.path.exists(full_dir):
            log.debug("Directory %s does not exist, creating it", full_dir)
            os.makedirs(full_dir)

        full_path = f"{out_dir}/{data_key}"
        with open(full_path, "wb") as fout:
            bytes_written = fout.write(buf)
            log.debug("Wrote %s %d", full_path, bytes_written)

        return data_key, len(buf)

    return "", 0
