# RedVox CLI Documentation

The RedVox Python SDK provides a command line interface (CLI) that can be used from a user's terminal. The CLI provides the following features:

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

##### to_json examples

Convert a single file where the converted file is placed in the same directory as the original file.

```
redvox-cli to_json 1637110002_1574370993244.rdvxz
```

Convert multiple files.

```
redvox-cli to_json 1637110002_1574370993244.rdvxz 1637110003_1574370993244.rdvxz
``` 

Wild cards can also be used.

```
redvox-cli to_json data/*.rdvxz
``` 

Increase logging verbosity (not that -v can also be used).

```
redvox-cli --verbose to_json data/*.rdvxz
``` 

Specify output directory for converted files (note that -o can also be used). The output directory should already exist.

```
redvox-cli --verbose to_json --out_dir ./data/json ./data/*.rdvxz
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

##### to_rdvxz examples

Convert a single file where the converted file is placed in the same directory as the original file.

```
redvox-cli to_rdvxz 1637110002_1574370993244.json
```

Convert multiple files.

```
redvox-cli to_rdvxz 1637110002_1574370993244.json 1637110003_1574370993244.json
``` 

Wild cards can also be used.

```
redvox-cli to_rdvxz data/*.json
``` 

Increase logging verbosity (not that -v can also be used).

```
redvox-cli --verbose to_rdvxz data/*.json
``` 

Specify output directory for converted files (note that -o can also be used). The output directory should already exist.

```
redvox-cli --verbose to_rdvxz --out_dir ./data/converted_rdvxz ./data/*.json
``` 

#### print

```
usage: redvox-cli print [-h] rdvxz_paths [rdvxz_paths ...]

positional arguments:
  rdvxz_paths  One or more rdvxz files to print

optional arguments:
  -h, --help   show this help message and exit
```

##### print examples

Print the contents of a single .rdvxz file.

```
redvox-cli print 1637110002_1574370993244.rdvxz
```

Print the contents of multiple .rdvxz files.

```
redvox-cli print 1637110002_1574370993244.rdvxz 1637110002_1574370993244.rdvxz
```

Use a wild card to print multiple .rdvxz files.

```
redvox-cli print *.rdvxz
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

##### data_req examples

Request data from a single device.

```
redvox-cli data_req fake_host 8080 fake_email@foo.com fake_password 1574726400 1574730000 1637650005
```

Request data from multiple devices.

```
redvox-cli data_req fake_host 8080 fake_email@foo.com fake_password 1574726400 1574730000 1637650005 1637650006 1637650007
```

Store downloaded data is a specified output directory (note that -o can also be used).

```
redvox-cli data_req --out_dir /data fake_host 8080 fake_email@foo.com fake_password 1574726400 1574730000 1637650005 1637650006 1637650007
```

Increase verbosity during data download (not that -v can also be used).

```
redvox-cli data_req --verbose --out_dir /data fake_host 8080 fake_email@foo.com fake_password 1574726400 1574730000 1637650005 1637650006 1637650007
```

Increase verbosity even more to display output from dependencies (such as the HTTP client). Note that -v -v or -vv may also be used here.

```
redvox-cli data_req --verbose --verbose --out_dir /data fake_host 8080 fake_email@foo.com fake_password 1574726400 1574730000 1637650005 1637650006 1637650007
```

