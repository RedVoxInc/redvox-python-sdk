"""
A simple WebSocket API for subscribing to live RedVox data.
"""

import time
import threading
from typing import Optional, List, Iterator
from queue import Empty, Queue

import lz4.frame
from websocket import WebSocketApp

from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.cloud.client import CloudClient


def fmt_uri(base: str, auth_token: str, station_ids: Optional[List[str]] = None) -> str:
    """
    Formats the subscription URL from the given base URL, authentication token, and optional station IDs.
    :param base: The base URL.
    :param auth_token: A current and valid authentication token.
    :param station_ids: An optional list of station IDs to subscribe to.
    :return: The formatted URI.
    """
    station_ids_query: str
    if station_ids is None or len(station_ids) == 0:
        station_ids_query = ""
    else:
        station_ids_query = "".join(
            map(lambda station_id: f"&station_id={station_id}", station_ids)
        )

    return f"{base}?auth_token={auth_token}{station_ids_query}"


def subscribe_bytes_queue(
    base_uri: str,
    queue: Queue[bytes],
    client: CloudClient,
    station_ids: Optional[List[str]] = None,
) -> None:
    """
    Create a subscription on the raw compressed bytes.
    :param base_uri: The base URI to the acquisition subscription service.
    :param queue: A queue for transferring when received by the subscriber.
    :param client: An instance of the RedVox CloudClient.
    :param station_ids: An optional list of station IDs to subscribe to.
    """

    def on_message(ws_app: WebSocketApp, msg: bytes) -> None:
        queue.put(msg)

    while True:
        uri: str = fmt_uri(base_uri, client.auth_token, station_ids)
        print(f"Connecting to {uri}")
        # noinspection PyTypeChecker
        ws_app: WebSocketApp = WebSocketApp(
            uri,
            on_message=on_message,
            on_open=lambda ws: print("Connection established"),
            on_error=lambda ws, ex: print(f"Connection error: {ex}"),
            on_close=lambda ws, code, reason: print(
                f"Connection closed: code={code} reason={reason}"
            ),
        )

        ws_app.run_forever()

        print("Subscription stream ended. Attempting to reconnect...")
        time.sleep(1)


def subscribe_bytes(
    base_uri: str,
    client: CloudClient,
    station_ids: Optional[List[str]] = None,
) -> Iterator[bytes]:
    """
    Create a subscription on the RedVox packet compressed bytes objects.
    :param base_uri: The base URI to the acquisition subscription service.
    :param client: An instance of the RedVox CloudClient.
    :param station_ids: An optional list of station IDs to subscribe to.
    :return: An iterator over RedVox compressed bytes instances.
    """
    queue: Queue = Queue()
    subscription_thread: threading.Thread = threading.Thread(
        target=subscribe_bytes_queue, args=(base_uri, queue, client, station_ids)
    )
    subscription_thread.start()

    while True:
        try:
            yield queue.get(True)
        except Empty:
            break


def subscribe_proto(
    base_uri: str,
    client: CloudClient,
    station_ids: Optional[List[str]] = None,
) -> Iterator[RedvoxPacketM]:
    """
    Create a subscription on the RedVox packet protobuf objects (RedvoxPacketM).
    :param base_uri: The base URI to the acquisition subscription service.
    :param client: An instance of the RedVox CloudClient.
    :param station_ids: An optional list of station IDs to subscribe to.
    :return: An iterator over RedvoxPacketM instances.
    """
    compressed_bytes: bytes
    for compressed_bytes in subscribe_bytes(base_uri, client, station_ids):
        decompressed_bytes: bytes = lz4.frame.decompress(compressed_bytes, False)
        proto: RedvoxPacketM = RedvoxPacketM()
        proto.ParseFromString(decompressed_bytes)
        yield proto


def subscribe_packet(
    base_uri: str,
    client: CloudClient,
    station_ids: Optional[List[str]] = None,
) -> Iterator[WrappedRedvoxPacketM]:
    """
    Create a subscription on the RedVox wrapped packet objects (WrappedRedvoxPacketM).
    :param base_uri: The base URI to the acquisition subscription service.
    :param client: An instance of the RedVox CloudClient.
    :param station_ids: An optional list of station IDs to subscribe to.
    :return: An iterator over WrappedRedvoxPacketM instances.
    """
    proto: RedvoxPacketM
    for proto in subscribe_proto(base_uri, client, station_ids):
        yield WrappedRedvoxPacketM(proto)
