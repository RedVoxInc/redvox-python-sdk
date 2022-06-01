"""
A simple WebSocket API for subscribing to live RedVox data.
"""

from dataclasses import dataclass
import logging
import threading
import time
from typing import Optional, List, Iterator, TypeVar, Generic
from queue import Empty, Queue

import lz4.frame  # type: ignore
from dataclasses_json import dataclass_json
from websocket import WebSocketApp  # type: ignore

from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.cloud.client import CloudClient


logger: logging.Logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class PubHeader:
    """
    A header that is optionally included with messages from subscription producers.
    """

    file_path: str


T = TypeVar("T", bytes, RedvoxPacketM, WrappedRedvoxPacketM)
R = TypeVar("R", RedvoxPacketM, WrappedRedvoxPacketM)


@dataclass
class PubMsg(Generic[T]):
    """
    A message from a RedVox publisher.
    """

    header: Optional[PubHeader]
    msg: T

    def map(self, msg: R) -> "PubMsg[R]":
        """
        Converts the body of this message to another type while maintaining the header.
        :param msg: The message to replace with.
        :return: A PubMsg with an updated msg body.
        """
        return PubMsg(self.header, msg)

    @staticmethod
    def parse(msg: bytes) -> "PubMsg":
        """
        Parses the published message.
        :param msg: The message to parse.
        :return: An instance of a PubMsg.
        """

        # Header is included
        if msg[:3] == b"\xc0\xff\xee":
            header_len: int = int.from_bytes(msg[3:5], "little", signed=False)
            json: str = msg[5 : 5 + header_len].decode("utf-8")
            pub_header: PubHeader = PubHeader.from_json(json)  # type: ignore
            return PubMsg(pub_header, msg[5 + header_len :])
        # Header is not included
        else:
            return PubMsg(None, msg)


def fmt_uri(
    base: str,
    auth_token: str,
    station_ids: Optional[List[str]] = None,
    server_id: Optional[str] = None,
) -> str:
    """
    Formats the subscription URL from the given base URL, authentication token, and optional station IDs.
    :param base: The base URL.
    :param auth_token: A current and valid authentication token.
    :param station_ids: An optional list of station IDs to subscribe to.
    :param server_id: An optional server ID for working with distributed acquisition servers.
    :return: The formatted URI.
    """
    station_ids_query: str
    if station_ids is None or len(station_ids) == 0:
        station_ids_query = ""
    else:
        station_ids_query = "".join(
            map(lambda station_id: f"&station_id={station_id}", station_ids)
        )

    server_id_query: str
    if server_id is None or len(server_id) == 0:
        server_id_query = ""
    else:
        server_id_query = f"&sid={server_id}"

    return f"{base}?auth_token={auth_token}{station_ids_query}&include_header=true{server_id_query}"


def subscribe_bytes_queue(
    base_uri: str,
    queue: Queue[PubMsg[bytes]],
    client: CloudClient,
    station_ids: Optional[List[str]] = None,
    server_id: Optional[str] = None,
) -> None:
    """
    Create a subscription on the raw compressed bytes.
    :param base_uri: The base URI to the acquisition subscription service.
    :param queue: A queue for transferring when received by the subscriber.
    :param client: An instance of the RedVox CloudClient.
    :param station_ids: An optional list of station IDs to subscribe to.
    :param server_id: An optional server ID for working with distributed acquisition servers.
    """

    while True:
        uri: str = fmt_uri(base_uri, client.auth_token, station_ids, server_id)
        logger.info(f"Connecting to {uri}")
        # noinspection PyTypeChecker
        ws_app: WebSocketApp = WebSocketApp(
            uri,
            on_message=lambda ws, msg: queue.put(PubMsg.parse(msg)),
            on_open=lambda ws: logger.info(f"Connection established for {uri}"),
            on_error=lambda ws, ex: logger.info(f"Connection error for {uri}: {ex}"),
            on_close=lambda ws, code, reason: logger.info(
                f"Connection closed for {uri}: code={code} reason={reason}"
            ),
        )

        ws_app.run_forever()

        logger.info("Subscription stream ended. Attempting to reconnect...")
        time.sleep(1)


# noinspection PyDefaultArgument
def subscribe_bytes(
    base_uri: str,
    client: CloudClient,
    station_ids: Optional[List[str]] = None,
    server_ids: Optional[List[str]] = ["0", "1"],
) -> Iterator[PubMsg[bytes]]:
    """
    Create a subscription on the RedVox packet compressed bytes objects.
    :param base_uri: The base URI to the acquisition subscription service.
    :param client: An instance of the RedVox CloudClient.
    :param station_ids: An optional list of station IDs to subscribe to.
    :param server_ids: An optional list of server IDs for working with distributed acquisition servers.
    :return: An iterator over RedVox compressed bytes instances.
    """
    queue: Queue[PubMsg[bytes]] = Queue()

    if server_ids is None:
        subscription_thread: threading.Thread = threading.Thread(
            target=subscribe_bytes_queue, args=(base_uri, queue, client, station_ids)
        )
        subscription_thread.start()
    else:
        server_id: str
        for server_id in server_ids:
            subscription_thread = threading.Thread(
                target=subscribe_bytes_queue,
                args=(base_uri, queue, client, station_ids, server_id),
            )
            subscription_thread.start()

    while True:
        try:
            yield queue.get(True)
        except Empty:
            break


# noinspection PyDefaultArgument
def subscribe_proto(
    base_uri: str,
    client: CloudClient,
    station_ids: Optional[List[str]] = None,
    server_ids: Optional[List[str]] = ["0", "1"],
) -> Iterator[PubMsg[RedvoxPacketM]]:
    """
    Create a subscription on the RedVox packet protobuf objects (RedvoxPacketM).
    :param base_uri: The base URI to the acquisition subscription service.
    :param client: An instance of the RedVox CloudClient.
    :param station_ids: An optional list of station IDs to subscribe to.
    :param server_ids: An optional list of server IDs for working with distributed acquisition servers.
    :return: An iterator over RedvoxPacketM instances.
    """
    pub_msg: PubMsg[bytes]
    for pub_msg in subscribe_bytes(base_uri, client, station_ids, server_ids):
        decompressed_bytes: bytes = lz4.frame.decompress(pub_msg.msg, False)
        proto: RedvoxPacketM = RedvoxPacketM()
        proto.ParseFromString(decompressed_bytes)
        yield pub_msg.map(proto)


# noinspection PyDefaultArgument
def subscribe_packet(
    base_uri: str,
    client: CloudClient,
    station_ids: Optional[List[str]] = None,
    server_ids: Optional[List[str]] = ["0", "1"],
) -> Iterator[PubMsg[WrappedRedvoxPacketM]]:
    """
    Create a subscription on the RedVox wrapped packet objects (WrappedRedvoxPacketM).
    :param base_uri: The base URI to the acquisition subscription service.
    :param client: An instance of the RedVox CloudClient.
    :param station_ids: An optional list of station IDs to subscribe to.
    :param server_ids: An optional list of server IDs for working with distributed acquisition servers.
    :return: An iterator over WrappedRedvoxPacketM instances.
    """
    pub_msg: PubMsg[RedvoxPacketM]
    for pub_msg in subscribe_proto(base_uri, client, station_ids, server_ids):
        yield pub_msg.map(WrappedRedvoxPacketM(pub_msg.msg))
