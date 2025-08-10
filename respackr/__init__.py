# respackr/__init__.py

import logging as log

from termaconfig import ConfigValidationError, TermaConfig
from terminaltables3 import DoubleTable

log.basicConfig(
    level=log.INFO,
    format="%(asctime)s:%(name)s:%(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

__name__ = "Respackr"
__version__ = "3.0.0"


def main():
    log.info(f"{__name__} {__version__}")

    config_path = "respackr.toml"
    spec_path = "respackr/spec.toml"

    try:
        config = TermaConfig(
            config_path, spec_path, tabletype=DoubleTable, logging=False
        )
    except ConfigValidationError:
        print()
        print("Errors are present in configuration. Exiting...")
        exit()

    print("Testing config:", config["pack"]["name"])


if __name__ == "__main__":
    pass
main()
