# <img src="../img/redvox_logo.png" height="25"> **RedVox Python SDK Cloud Access Manual**

The RedVox SDK provides access to RedVox cloud services. These services allow users to access cloud based metadata, raw data, and report data from the SDK. The SDK provides access to cloud services both through its CLI and through its API.

RedVox cloud services can only be accessed when utilizing a Premium RedVox subscription.

## Table of Contents

<!-- toc -->

- [Authenticating with RedVox Cloud Services](#authenticating-with-redvox-cloud-services)
  * [Storing authentication information in a file](#storing-authentication-information-in-a-file)
  * [Storing authentication information in the environment](#storing-authentication-information-in-the-environment)
- [Setting up the Cloud Client](#setting-up-the-cloud-client)
- [Retrieving Timing Statistics](#retrieving-timing-statistics)
- [Ranged Data Requests](#ranged-data-requests)

<!-- tocstop -->

## Authenticating with RedVox Cloud Services

When utilizing the SDK to access RedVox Cloud services, authentication information must be passed either to the CLI or the API. 

Instead of passing your RedVox username and password to the API or CLI each time it's used, we recommend storing your authentication information separately on your system. The SDK provides two methods of storing authentication state. You can store a `.redvox.toml` file in your "home directory" or you can export authentication fields as environmental variables. The SDK will automatically search these locations to try and load cloud based authentication information.

### Storing authentication information in a file

Create a file named `.redvox.toml` in your home directory. The [RedvoxConfig](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/config.html#redvox.cloud.config.RedVoxConfig) class provides a specification for which fields are required in the .toml file and which fields are optional (and their defaults).

An example `.redvox.toml` file is provided next.

```toml
username = "foo@bar.baz"
password = "hunter2"
protocol = "https"  # Optional, may be one of https (default) or http.
host = "redvox.io"  # Optional
port = 8080         # Optional
```

### Storing authentication information in the environment

Alternatively, environment variables can be used to store authentication information. The following environment variables are searched for and utilized by the SDK.

* `REDVOX_USERNAME`
* `REDVOX_PASSWORD`
* `REDVOX_PROTOCOL`
* `REDVOX_HOST`
* `REDVOX_PORT`

Only `REDVOX_USERNAME` and `REDVOX_PASSWORD` are required, otherwise defaults are used as described by the [RedvoxConfig](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/config.html#redvox.cloud.config.RedVoxConfig).

## Setting up the Cloud Client

The SDK provides a cloud client that implements Python's context manager interface (see: [cloud_client](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/client.html#redvox.cloud.client.cloud_client)). This means that the cloud client will close its connection and cleanup resources automatically when it's no longer used.

The `cloud_client` method takes an instance of a [RedvoxConfig](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/config.html#redvox.cloud.config.RedVoxConfig). If you do not wish to provide this manually, see [Authenticating with RedVox Cloud Services](#authenticating-with-redvox-cloud-services) for strategies on how to load this by automatically from the user's system.

The `cloud_client` method returns an instance of [CloudClient](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/client.html#redvox.cloud.client.CloudClient). 

Let's look at an example of setting up a cloud client.

```python
from redvox.cloud.client import cloud_client, CloudClient
from redvox.cloud.config import RedVoxConfig

cloud_config: RedVoxConfig = RedVoxConfig(username="foo@bar.baz", password="hunter2")

client: CloudClient
with cloud_client(cloud_config) as client:
    # Use client within this with block to access RedVox services
    pass
```

Of course, if your authentication details are stored on your system, this becomes:

```python
from redvox.cloud.client import cloud_client, CloudClient

client: CloudClient
with cloud_client() as client:
    # Use client within this with block to access RedVox services
    pass
```

## Retrieving Timing Statistics

The fields required to correct timing can be retrieved using the [request_station_stats](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/client.html#redvox.cloud.client.CloudClient.request_station_stats) method.

The above method returns a [StationStatsResp](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/station_stats.html#redvox.cloud.station_stats.StationStatResp) which contains a list of [StationStat](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/file_statistics.html#redvox.common.file_statistics.StationStat) objects.

## Ranged Data Requests

A ranged data request can be made with the [request_data_range](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/client.html#redvox.cloud.client.CloudClient.request_data_range) method.

The [DataRangeResp](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/data_api.html#redvox.cloud.data_api.DataRangeResp) will contain a list of the AWS S3 URLs which can be accessed to obtain the underlying data.
