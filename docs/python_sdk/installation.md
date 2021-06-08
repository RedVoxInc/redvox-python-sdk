## RedVox SDK Installation

### Installing/upgrading with pip

The recommended way of installing the RedVox SDK is through [pip](https://pip.pypa.io/en/stable/). The RedVox SDK pip distribution is hosted on PyPI at https://pypi.org/project/redvox/.

The following command can be used to both install the RedVox SDK and to upgrade previous RedVox SDK installations to the latest stable version:

```
pip install redvox --upgrade
```

### Verifying the installation

Run the following snippet of code in the Python environment that the SDK was installed to:

```python
import redvox
print(redvox.VERSION)
```

If the installation was successful, you will see the latest installed version of the SDK printed to output.

### Installing optional dependencies

The RedVox SDK provides several optional "extras" that provide additional functionality in the SDK. These packages are considered optional and are not included in the base installation because they may not be supported by all platforms or architectures.

The following table describes the available extras and their limitations.

| Extra Name | Description | Additional Libraries | Caveats |
|------------|-------------|----------------------|---------|
| GUI        | Provides additional graphical user interfaces and plotting | [PySide6](https://pypi.org/project/PySide6/), [matplotlib](https://pypi.org/project/matplotlib/) | PySide6 may not be available for all platforms |
| native     | Increase performance by providing natively compiled alternatives for selected code routines | [redvox_native](https://pypi.org/project/redvox-native/) | Only on Linux and Intel bases OS X (does not support Apple M1 or Windows) |
| all | Installs both the GUI and the native extras | | |

The following syntax is used to install a dependency with extras:

`pip install "library_name[extra_0 ,extra_1,...,extra_n]"  --upgrade`

For example, to install the `GUI` extra:

```
pip install "redvox[GUI] --upgrade"
```

To install the `native` extra:

```
pip install "redvox[native] --upgrade"
```

To install both extras:

```
pip install "redvox[GUI,native] --upgrade"
```

To install both extras with the `full` extra shortcut.

```
pip install redvox[full] --upgrade
```

### Source Distributions

Official source distributions of the SDK are provided on GitHub at: https://github.com/RedVoxInc/redvox-python-sdk/releases