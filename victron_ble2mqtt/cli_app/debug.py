"""
    CLI for usage
"""

import asyncio
import logging
from datetime import datetime

import rich_click as click
from bleak import BLEDevice
from cli_base.cli_tools.verbosity import OPTION_KWARGS_VERBOSE, setup_logging
from cli_base.toml_settings.api import TomlSettings
from rich import print  # noqa
from victron_ble.scanner import BaseScanner, Scanner

from victron_ble2mqtt.cli_app import cli
from victron_ble2mqtt.cli_app.settings import get_settings
from victron_ble2mqtt.user_settings import UserSettings


logger = logging.getLogger(__name__)


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


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
@click.argument('mac', envvar='MAC', type=str, required=False, default=None)
@click.argument('key', envvar='KEY', type=str, required=False, default=None)
def debug_read(verbosity: int, mac: str = None, key: str = None):
    """
    Read data from specified devices and print them.
    MAC / KEY are used from config file, if not given.
    """
    setup_logging(verbosity=verbosity)

    toml_settings: TomlSettings = get_settings()
    user_settings: UserSettings = toml_settings.get_user_settings(debug=verbosity > 1)

    if not mac:
        mac = user_settings.device_address
    print(f'Use device MAC address: {mac!r}')

    if not key:
        key = user_settings.device_key
    print(f'Use device key: {key!r}')

    device_keys = {mac: key}

    async def scan(keys):
        scanner = Scanner(keys)
        await scanner.start()

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(scan(device_keys))
    loop.run_forever()
