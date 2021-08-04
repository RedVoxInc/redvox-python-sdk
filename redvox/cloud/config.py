"""
This module contains capabilities for loading RedVox specific configurations from the user's environment if it exists.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

# noinspection Mypy
import redvox.common.errors as errors

# noinspection PyPackageRequirements,Mypy
from serde import deserialize, serialize

# noinspection PyPackageRequirements,Mypy
from serde.toml import from_toml, to_toml

REDVOX_CONFIG_FILE_NAME: str = ".redvox.toml"
REDVOX_USERNAME_ENV_KEY: str = "REDVOX_USERNAME"
REDVOX_PASSWORD_ENV_KEY: str = "REDVOX_PASSWORD"
REDVOX_PROTOCOL_ENV_KEY: str = "REDVOX_PROTOCOL"
REDVOX_HOST_ENV_KEY: str = "REDVOX_HOST"
REDVOX_PORT_ENV_KEY: str = "REDVOX_PORT"
REDVOX_SECRET_TOKEN_ENV_KEY: str = "REDVOX_SECRET_TOKEN"


@serialize
@deserialize
@dataclass
class RedVoxConfig:
    """
    Configuration options specific for accessing the cloud services.
    """

    username: str
    password: str
    protocol: str = "https"
    host: str = "redvox.io"
    port: int = 8080
    secret_token: Optional[str] = None

    @staticmethod
    def from_auth_token(
            auth_token: str,
            protocol: str = "https",
            host: str = "redvox.io",
            port: int = 8080,
            secret_token: Optional[str] = None) -> "RedVoxConfig":
        return RedVoxConfig("auth_token", auth_token, protocol, host, port, secret_token)

    @staticmethod
    def from_env() -> "RedVoxConfig":
        """
        Attempts to load the configuration from the environment.
        :return: An instance of RedvoxConfig or raises a RedvoxError.
        """
        # At least the username and password must be provided
        username: Optional[str] = os.environ.get(REDVOX_USERNAME_ENV_KEY)
        password: Optional[str] = os.environ.get(REDVOX_PASSWORD_ENV_KEY)

        if username is None:
            raise errors.RedVoxError(
                f"{REDVOX_USERNAME_ENV_KEY} is not in the environment"
            )

        if password is None:
            raise errors.RedVoxError(
                f"{REDVOX_PASSWORD_ENV_KEY} is not in the environment"
            )

        redvox_config: RedVoxConfig = RedVoxConfig(username, password)

        # If anything else is provided, overwrite the defaults
        protocol: Optional[str] = os.environ.get(REDVOX_PROTOCOL_ENV_KEY)
        if protocol is not None:
            redvox_config.protocol = protocol

        host: Optional[str] = os.environ.get(REDVOX_HOST_ENV_KEY)
        if host is not None:
            redvox_config.host = host

        port: Optional[str] = os.environ.get(REDVOX_PORT_ENV_KEY)
        if port is not None:
            # Make sure the port is actually an integer and parse it as such
            try:
                port_int: int = int(port)
                redvox_config.port = port_int
            except ValueError:
                raise errors.RedVoxError(
                    f"Provided environment variable={REDVOX_PORT_ENV_KEY} for port={port} is not integer"
                )

        secret_token: Optional[str] = os.environ.get(REDVOX_SECRET_TOKEN_ENV_KEY)
        if secret_token is not None:
            redvox_config.secret_token = secret_token

        return redvox_config

    @staticmethod
    def from_file(path: Path) -> "RedVoxConfig":
        """
        Attempts to load the configuration from a TOML file.
        :return: An instance of RedvoxConfig or raises a RedvoxError.
        """
        with open(path, "r") as toml_in:
            content: str = toml_in.read()
            try:
                return from_toml(RedVoxConfig, content)
            except Exception as e:
                raise errors.RedVoxError(
                    f"Error parsing RedVox configuration file: {e}"
                )

    @staticmethod
    def from_home() -> "RedVoxConfig":
        """
        Attempts to load the configuration file .redvox.toml from the user's home directory.
        :return: An instance of RedvoxConfig or raises a RedvoxError.
        """
        home_path: Path = Path.home()
        credentials_path: Path = home_path.joinpath(REDVOX_CONFIG_FILE_NAME)

        if not credentials_path.exists():
            raise errors.RedVoxError("RedVox configuration file does not exist")

        return RedVoxConfig.from_file(credentials_path)

    @staticmethod
    def find() -> Optional["RedVoxConfig"]:
        """
        Attempts to load the configuration either from the user's home directory or from the environment.
        :return: An instance of RedvoxConfig or raises a RedvoxError.
        """

        # First try to load the configuration from the user's home directory
        try:
            return RedVoxConfig.from_home()
        except errors.RedVoxError:
            pass

        # If that doesn't work, try to load the configuration from the environment
        try:
            return RedVoxConfig.from_env()
        except errors.RedVoxError:
            return None

    def save_to_file(self, path: Path) -> None:
        """
        Saves this configuration to the specified file path.
        :param path: Path to save this configuration to.
        """
        with open(path, "w") as toml_out:
            toml_out.write(to_toml(self))

    def save_to_home(self) -> Path:
        """
        Saves this configuration file to the user's home directory as .redvox.toml.
        :return: The path that the configuration was saved to.
        """
        home_path: Path = Path.home()
        credentials_path: Path = home_path.joinpath(REDVOX_CONFIG_FILE_NAME)
        self.save_to_file(credentials_path)
        return credentials_path

    def url(self, end_point: str) -> str:
        """
        Formats the API URL.
        :param end_point: Endpoint to use.
        :return: The formatted API URL.
        """
        return f"{self.protocol}://{self.host}:{self.port}{end_point}"
