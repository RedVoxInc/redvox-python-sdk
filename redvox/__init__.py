"""
Provides library level metadata and constants.
"""

NAME: str = "redvox"
VERSION: str = "3.6.6"


def version() -> str:
    """Returns the version number of this library."""
    return VERSION


def print_version() -> None:
    """Prints the version number of this library"""
    print(version())


def print_redvox_info() -> None:
    """
    Prints information about this library to standard out.
    """
    import redvox.settings

    print()
    print(f"version: {VERSION}")
    print(f"parallelism enabled: {redvox.settings.is_parallelism_enabled()}")
    print(f"native extra enabled: {redvox.settings.is_native_extra_enabled()}")
    print(f"gui extra enabled: {redvox.settings.is_gui_extra_enabled()}")
    print()
