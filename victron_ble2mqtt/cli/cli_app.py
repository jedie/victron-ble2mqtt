"""
    CLI for usage
"""

import asyncio
import logging
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

import rich_click as click
from bleak import AdvertisementData, BLEDevice
from cli_base.cli_tools.verbosity import OPTION_KWARGS_VERBOSE, setup_logging
from cli_base.cli_tools.version_info import print_version
from cli_base.systemd.api import ServiceControl
from cli_base.toml_settings.api import TomlSettings
from ha_services.mqtt4homeassistant.converter import values2mqtt_payload
from ha_services.mqtt4homeassistant.data_classes import HaValue, HaValues
from ha_services.mqtt4homeassistant.mqtt import HaMqttPublisher
from rich import print  # noqa
from rich.console import Console
from rich.traceback import install as rich_traceback_install
from rich_click import RichGroup
from victron_ble.devices import DeviceData
from victron_ble.exceptions import UnknownDeviceError
from victron_ble.scanner import BaseScanner, Scanner

import victron_ble2mqtt
from victron_ble2mqtt import constants
from victron_ble2mqtt.mapping import VICTRON_VALUES
from victron_ble2mqtt.user_settings import SystemdServiceInfo, UserSettings
from victron_ble2mqtt.victron_ble_utils import values2dict
from victron_ble2mqtt.wifi_info import get_wifi_info_ha_values


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


##################################################################################################


def get_settings() -> TomlSettings:
    return TomlSettings(
        dir_name='victron-ble2mqtt',
        file_name='victron-ble2mqtt',
        settings_dataclass=UserSettings(),
    )


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def edit_settings(verbosity: int):
    """
    Edit the settings file. On first call: Create the default one.
    """
    setup_logging(verbosity=verbosity)
    toml_settings: TomlSettings = get_settings()
    toml_settings.open_in_editor()


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def print_settings(verbosity: int):
    """
    Display (anonymized) MQTT server username and password
    """
    setup_logging(verbosity=verbosity)
    toml_settings: TomlSettings = get_settings()
    toml_settings.print_settings()


######################################################################################################
# Manage systemd service commands:


def get_systemd_settings(verbosity: int) -> SystemdServiceInfo:
    toml_settings: TomlSettings = get_settings()
    user_settings: UserSettings = toml_settings.get_user_settings(debug=verbosity > 0)
    systemd_settings: SystemdServiceInfo = user_settings.systemd
    return systemd_settings


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def systemd_debug(verbosity: int):
    """
    Print Systemd service template + context + rendered file content.
    """
    setup_logging(verbosity=verbosity)
    systemd_settings: SystemdServiceInfo = get_systemd_settings(verbosity)

    ServiceControl(info=systemd_settings).debug_systemd_config()


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def systemd_setup(verbosity: int):
    """
    Write Systemd service file, enable it and (re-)start the service. (May need sudo)
    """
    setup_logging(verbosity=verbosity)
    systemd_settings: SystemdServiceInfo = get_systemd_settings(verbosity)

    ServiceControl(info=systemd_settings).setup_and_restart_systemd_service()


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def systemd_remove(verbosity: int):
    """
    Remove Systemd service file. (May need sudo)
    """
    setup_logging(verbosity=verbosity)
    systemd_settings: SystemdServiceInfo = get_systemd_settings(verbosity)

    ServiceControl(info=systemd_settings).remove_systemd_service()


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def systemd_status(verbosity: int):
    """
    Display status of systemd service. (May need sudo)
    """
    setup_logging(verbosity=verbosity)
    systemd_settings: SystemdServiceInfo = get_systemd_settings(verbosity)

    ServiceControl(info=systemd_settings).status()


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def systemd_stop(verbosity: int):
    """
    Stops the systemd service. (May need sudo)
    """
    setup_logging(verbosity=verbosity)
    systemd_settings: SystemdServiceInfo = get_systemd_settings(verbosity)

    ServiceControl(info=systemd_settings).stop()


##################################################################################################


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


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE | {'default': 0})
def publish_loop(verbosity: int):
    """
    Publish MQTT messages in endless loop (Entrypoint from systemd)
    """
    toml_settings: TomlSettings = get_settings()
    user_settings: UserSettings = toml_settings.get_user_settings(debug=verbosity > 1)

    mac = user_settings.device_address
    logger.info('Use device MAC address: %r', mac)

    key = user_settings.device_key
    logger.info('Use device key: %r', key)

    device_keys = {mac: key}

    class MqttPublisher(Scanner):
        def __init__(
            self,
            *,
            device_keys: dict[str, str],
            user_settings: UserSettings,
            verbosity: int,
        ):
            super().__init__(device_keys)

            self.publisher = HaMqttPublisher(
                settings=user_settings.mqtt,
                verbosity=verbosity,
                config_count=1,  # Send every time the config
            )
            self.rssi = None
            self.hostname = socket.gethostname()

        def _detection_callback(self, device: BLEDevice, advertisement: AdvertisementData):
            self.rssi = advertisement.rssi
            return super()._detection_callback(device, advertisement)

        def callback(self, ble_device: BLEDevice, raw_data: bytes):
            logger.debug(f"Received data from {ble_device.address.lower()}: {raw_data.hex()}")

            values = [
                HaValue(
                    name='Hostname',
                    value=self.hostname,
                    device_class=None,
                    state_class=None,
                    unit=None,
                ),
                HaValue(
                    name='System load 1min.',
                    value=os.getloadavg()[0],
                    device_class=None,
                    state_class='measurement',
                    unit=None,
                ),
                HaValue(
                    name='Device Name',
                    value=ble_device.name,
                    device_class=None,
                    state_class=None,
                    unit=None,
                ),
                HaValue(
                    name='Device Address',
                    value=ble_device.address,
                    device_class=None,
                    state_class=None,
                    unit=None,
                ),
            ]

            if self.rssi is not None:
                values.append(
                    HaValue(
                        name='RSSI',
                        value=self.rssi,
                        device_class=None,
                        state_class=None,
                        unit=None,
                    )
                )

            # Add information about WIFI quality:
            values += get_wifi_info_ha_values()

            try:
                device = self.get_device(ble_device, raw_data)
            except UnknownDeviceError as e:
                logger.error(e)
            else:
                data: DeviceData = device.parse(raw_data)
                data_dict = values2dict(data)

                for key, value in data_dict.items():
                    if value_info := VICTRON_VALUES.get(key):
                        values.append(
                            HaValue(
                                name=value_info.name,
                                value=value,
                                device_class=value_info.device_class,
                                state_class=value_info.state_class,
                                unit=value_info.unit,
                            )
                        )
                    else:
                        logger.warning(f'No mapping for: {key=} {value=}')
                        values.append(
                            HaValue(
                                name=key,
                                value=value,
                                device_class='',
                                state_class='',
                                unit=None,
                            )
                        )

            # Collect information:
            ha_values = HaValues(
                device_name=user_settings.device_name,
                values=values,
            )

            # Create Payload:
            ha_mqtt_payload = values2mqtt_payload(
                values=ha_values,
                name_prefix=ble_device.address,
                default_device_class=None,
                default_state_class=None,
            )

            # Send vial MQTT to HomeAssistant:
            self.publisher.publish2homeassistant(ha_mqtt_payload=ha_mqtt_payload)

            time.sleep(1)

    async def scan(*, device_keys: dict[str, str], user_settings: UserSettings, verbosity: int):
        scanner = MqttPublisher(
            device_keys=device_keys,
            user_settings=user_settings,
            verbosity=verbosity,
        )
        await scanner.start()

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(
        scan(
            device_keys=device_keys,
            user_settings=user_settings,
            verbosity=verbosity,
        )
    )
    loop.run_forever()


##################################################################################################


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
