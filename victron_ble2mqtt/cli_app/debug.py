"""
    CLI for usage
"""

import asyncio
import logging
from datetime import datetime

from bleak import BLEDevice
from cli_base.cli_tools.verbosity import setup_logging
from cli_base.toml_settings.api import TomlSettings
from cli_base.tyro_commands import TyroVerbosityArgType
from rich import print  # noqa
from victron_ble.devices import detect_device_type
from victron_ble.scanner import BaseScanner

from victron_ble2mqtt.cli_app import app
from victron_ble2mqtt.cli_app.settings import get_settings
from victron_ble2mqtt.user_settings import UserSettings
from victron_ble2mqtt.victron_ble_utils import DeviceHandler


logger = logging.getLogger(__name__)


@app.command
def discover(verbosity: TyroVerbosityArgType):
    """
    Discover Victron devices with Instant Readout
    """
    setup_logging(verbosity=verbosity)

    class Scanner(BaseScanner):

        def callback(self, device: BLEDevice, raw_data: bytes):
            print(datetime.now())
            data = dict(name=device.name, address=device.address, details=device.details)
            print(data)
            if DeviceClass := detect_device_type(raw_data):
                print(f'Device type: {DeviceClass.__name__}')
            else:
                print(f'Unknown device type: {raw_data.hex()}')

    async def scan():
        scanner = Scanner()
        await scanner.start()

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(scan())
    loop.run_forever()


@app.command
def debug_read(verbosity: TyroVerbosityArgType, keys: list[str] | None = None):
    """
    Read data from devices and print them.
    Device keys are used from config file, if not given.
    """
    setup_logging(verbosity=verbosity)

    toml_settings: TomlSettings = get_settings()
    user_settings: UserSettings = toml_settings.get_user_settings(debug=verbosity > 1)

    if not keys:
        keys = user_settings.device_keys
    print(f'Use device {len(keys)} device keys.')

    class Scanner(BaseScanner):
        def __init__(self, keys: list[str]):
            super().__init__()
            self.device_handler = DeviceHandler(keys)

        def callback(self, ble_device: BLEDevice, raw_data: bytes):
            print(datetime.now(), ble_device.name, end=' ')
            if generic_device := self.device_handler.get_generic_device(ble_device, raw_data):
                data_dict = generic_device.parse(raw_data=raw_data)
                print(data_dict)
                print()
            else:
                print('Unknown device type!')

    async def scan(keys):
        scanner = Scanner(keys)
        await scanner.start()

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(scan(keys))
    loop.run_forever()
