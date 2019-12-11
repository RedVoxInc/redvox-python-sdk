# RedVox CLI Documentation

This SDK provides a command line interface (CLI) that can be called from a user's terminal. The CLI provides the following features:

* Convert RedVox .rdvxz files to RedVox formatted .json files
* Convert RedVox formatted .json files to RedVox .rdvxz files
* Print contents of RedVox .rdvxz files to stdout
* Perform batch data downloaded of RedVox data (requires a redvox.io account)

## Using the CLI

The CLI is installed when this SDK is installed from pip.

The CLI can be accessed by opening a terminal and running ```redvox-cli```.

Documentation for the CLI can be accessed with ```redvox-cli --help``` for the high-level documentation and ```redvox-cli [command] --help``` for detailed documentation about any of the CLI's commands.

### CLI Commands

The following commands are available for the redvox-cli.

```
usage: redvox-cli [-h] [--verbose] {to_json,to_rdvxz,print,data_req} ...

Command line tools for viewing, converting, and downloading RedVox data.

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         Enable verbose logging

command:
  {to_json,to_rdvxz,print,data_req}
    to_json             Convert rdvxz files to json files
    to_rdvxz            Convert json files to rdvxz files
    print               Print contents of rdvxz files to stdout
    data_req            Request bulk RedVox data from the RedVox servers
```

#### to_json

```
usage: redvox-cli to_json [-h] [--out_dir OUT_DIR]
                          rdvxz_paths [rdvxz_paths ...]

positional arguments:
  rdvxz_paths           One or more rdvxz files to convert to json files

optional arguments:
  -h, --help            show this help message and exit
  --out_dir OUT_DIR, -o OUT_DIR
                        Optional output directory (will use same directory as
                        source files by default)
```

#### to_rdvxz

```
usage: redvox-cli to_rdvxz [-h] [--out_dir OUT_DIR]
                           json_paths [json_paths ...]

positional arguments:
  json_paths            One or more json files to convert to rdvxz files

optional arguments:
  -h, --help            show this help message and exit
  --out_dir OUT_DIR, -o OUT_DIR
                        Optional output directory (will use same directory as
                        source files by default)
```

#### print

```
usage: redvox-cli print [-h] rdvxz_paths [rdvxz_paths ...]

positional arguments:
  rdvxz_paths  One or more rdvxz files to print

optional arguments:
  -h, --help   show this help message and exit
```

#### data_req

```
usage: redvox-cli data_req [-h] [--out_dir OUT_DIR] [--retries {0,1,2,3,4,5}]
                           host port email password req_start_s req_end_s
                           redvox_ids [redvox_ids ...]

positional arguments:
  host                  Data server host
  port                  Data server port
  email                 redvox.io account email
  password              redvox.io account password
  req_start_s           Data request start as number of seconds since the
                        epoch UTC
  req_end_s             Data request end as number of seconds since the epoch
                        UTC
  redvox_ids            A list of RedVox ids delimited by a space

optional arguments:
  -h, --help            show this help message and exit
  --out_dir OUT_DIR, -o OUT_DIR
                        The output directory that RedVox files will be written
                        to.
  --retries {0,1,2,3,4,5}, -r {0,1,2,3,4,5}
                        The number of times the client should retry getting a
                        file on failure
```