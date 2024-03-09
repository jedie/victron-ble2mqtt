"""
    CLI for usage
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import rich_click as click
from bleak import BLEDevice
from cli_base.cli_tools.verbosity import OPTION_KWARGS_VERBOSE, setup_logging
from cli_base.cli_tools.version_info import print_version
from rich import print  # noqa
from rich.console import Console
from rich.traceback import install as rich_traceback_install
from rich_click import RichGroup
from victron_ble.scanner import BaseScanner

import victron_ble2mqtt
from victron_ble2mqtt import constants


logger = logging.getLogger(__name__)


OPTION_ARGS_DEFAULT_TRUE = dict(is_flag=True, show_default=True, default=True)
OPTION_ARGS_DEFAULT_FALSE = dict(is_flag=True, show_default=True, default=False)
ARGUMENT_EXISTING_DIR = dict(
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path)
)
ARGUMENT_NOT_EXISTING_DIR = dict(
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        readable=False,
        writable=True,
        path_type=Path,
    )
)
ARGUMENT_EXISTING_FILE = dict(
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path)
)


class ClickGroup(RichGroup):  # FIXME: How to set the "info_name" easier?
    def make_context(self, info_name, *args, **kwargs):
        info_name = './cli.py'
        return super().make_context(info_name, *args, **kwargs)


@click.group(
    cls=ClickGroup,
    epilog=constants.CLI_EPILOG,
)
def cli():
    pass


@click.command()
def version():
    """Print version and exit"""
    # Pseudo command, because the version always printed on every CLI call ;)
    sys.exit(0)


cli.add_command(version)


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE | {'default': 2})
def discover(verbosity: int):
    """
    Discover Victron devices with Instant Readout
    """
    setup_logging(verbosity=verbosity)

    class Scanner(BaseScanner):

        def callback(self, device: BLEDevice, advertisement: bytes):
            print(datetime.now())
            data = dict(name=device.name, address=device.address, details=device.details)
            print(data)

    async def scan():
        scanner = Scanner()
        await scanner.start()

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(scan())
    loop.run_forever()


def main():
    print_version(victron_ble2mqtt)

    console = Console()
    rich_traceback_install(
        width=console.size.width,  # full terminal width
        show_locals=True,
        suppress=[click],
        max_frames=2,
    )

    # Execute Click CLI:
    cli.name = './cli.py'
    cli()
