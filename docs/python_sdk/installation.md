# <img src="img/redvox_logo.png" height="25"> **RedVox SDK Installation**

## Table of Contents

<!-- toc -->

- [Installing/upgrading with pip](#installingupgrading-with-pip)
- [Verifying the installation](#verifying-the-installation)
- [Installing optional dependencies](#installing-optional-dependencies)
    + [Verifying installation of the GUI extra](#verifying-installation-of-the-gui-extra)
    + [Verifying installation of the native extra](#verifying-installation-of-the-native-extra)
- [Source Distributions](#source-distributions)

<!-- tocstop -->

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

The RedVox SDK provides several [optional dependencies (sometimes called extras)](https://setuptools.readthedocs.io/en/latest/userguide/dependency_management.html#optional-dependencies) that provide additional functionality in the SDK. These packages are considered optional and are not included in the base installation because they may not be supported by all platforms or architectures.

The following table describes the available extras and their limitations.

| Extra Name | Description | Additional Libraries | Caveats |
|------------|-------------|----------------------|---------|
| GUI        | Provides additional graphical user interfaces and plotting | [PySide6](https://pypi.org/project/PySide6/), [matplotlib](https://pypi.org/project/matplotlib/) | PySide6 may not be available for all platforms |
| native     | Increase performance by providing natively compiled alternatives for selected code routines | [redvox_native](https://pypi.org/project/redvox-native/) | Only available on Linux, Windows, and Intel based OS X (does not currently support Apple M1) |
| all | Installs both the GUI and the native extras | See above | See above |

The following syntax is used to install a dependency with extras:

`pip install "library_name[extra_0 ,extra_1,...,extra_n]"  --upgrade`

For example, to install the `GUI` extra:

```
pip install "redvox[GUI]" --upgrade
```

To install the `native` extra:

```
pip install "redvox[native]" --upgrade
```

To install both extras:

```
pip install "redvox[GUI,native]" --upgrade
```

To install both extras with the `full` extra shortcut.

```
pip install "redvox[full]" --upgrade
```

##### Verifying installation of the GUI extra

To verify installation of the GUI extra, you can attempt to open the GUI data download interface with the following command:

```
redvox-cli cloud-download
```

If the GUI dependencies were installed correctly, you will see the data download user interface. If the GUI dependencies were not installed correctly, you will see the following error message:

```
UserWarning: GUI dependencies are not installed. Install the 'GUI' extra to enable this functionality.
  warnings.warn(
[ERROR:82112:cli.py:cli:main:721:2021-06-08 10:14:33,148] Encountered an error: module 'redvox.common.gui.cloud_data_retrieval' has no attribute 'run_gui'
```

##### Verifying installation of the native extra

To verify the installation of the `native` extra, you may attempt to import the redvox_native library from your Python environment.

```python
import redvox_native
```

If the native extra was installed successfully, you will not see any errors. If the native extra was not installed, you will see the following error:

```
ModuleNotFoundError: No module named 'redvox_native'
```

### Source Distributions

Official source distributions of the SDK are provided on GitHub at: https://github.com/RedVoxInc/redvox-python-sdk/releases
