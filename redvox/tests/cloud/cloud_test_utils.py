import os
from typing import Optional, Callable, TypeVar, Union

from redvox.cloud.client import CloudClient

T = TypeVar('T')


def throwing_getenv(key: str,
                    default: Optional[str] = None,
                    transform: Optional[Callable[[str], T]] = None) -> Union[str, T]:
    res: Optional[str] = os.getenv(key, default)

    if res:
        return transform(res) if transform else res

    raise EnvironmentError(f"{key} is not in the environment and a default was not provided")


class CloudEnvKeys:
    USERNAME: str = "REDVOX_SDK_CLOUD_USER"
    PASSWORD: str = "REDVOX_SDK_CLOUD_PASS"
    SECRET: str = "REDVOX_SDK_CLOUD_SECRET"
    PROTOCOL: str = "REDVOX_SDK_CLOUD_PROTOCOL"
    HOST: str = "REDVOX_SDK_CLOUD_HOST"
    PORT: str = "REDVOX_SDK_CLOUD_PORT"


def cloud_credentials_provided() -> bool:
    try:
        throwing_getenv(CloudEnvKeys.USERNAME)
        throwing_getenv(CloudEnvKeys.PASSWORD)
        throwing_getenv(CloudEnvKeys.SECRET)
        return True
    except EnvironmentError:
        return False


def client_from_credentials() -> CloudClient:
    return CloudClient(
        throwing_getenv(CloudEnvKeys.USERNAME),
        throwing_getenv(CloudEnvKeys.PASSWORD),
        ApiConfig(
            throwing_getenv(CloudEnvKeys.PROTOCOL, "https"),
            throwing_getenv(CloudEnvKeys.HOST, "redvox.io"),
            throwing_getenv(CloudEnvKeys.PORT, "8080", int),
        ),
        throwing_getenv(CloudEnvKeys.SECRET)
    )


def cloud_env_template() -> str:
    return f"{CloudEnvKeys.USERNAME}= {CloudEnvKeys.PASSWORD}= {CloudEnvKeys.SECRET}= {CloudEnvKeys.PROTOCOL}= " \
           f"{CloudEnvKeys.HOST}= {CloudEnvKeys.PORT}="
