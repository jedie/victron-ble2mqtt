"""
    CLI for usage
"""

import asyncio
import logging

import rich_click as click
from bleak import AdvertisementData, BLEDevice
from cli_base.cli_tools.verbosity import OPTION_KWARGS_VERBOSE, setup_logging
from cli_base.toml_settings.api import TomlSettings
from ha_services.mqtt4homeassistant.mqtt import get_connected_client
from rich import print  # noqa
from victron_ble.scanner import BaseScanner

from victron_ble2mqtt.cli_app import cli
from victron_ble2mqtt.cli_app.settings import get_settings
from victron_ble2mqtt.mqtt import VictronMqttDeviceHandler
from victron_ble2mqtt.user_settings import UserSettings
from victron_ble2mqtt.victron_ble_utils import DeviceHandler


logger = logging.getLogger(__name__)


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE | {'default': 0})
def publish_loop(verbosity: int):
    """
    Publish MQTT messages in endless loop (Entrypoint from systemd)
    """
    setup_logging(verbosity=verbosity)

    toml_settings: TomlSettings = get_settings()
    user_settings: UserSettings = toml_settings.get_user_settings(debug=verbosity > 1)

    keys = user_settings.device_keys
    print(f'Use device {len(keys)} device keys.')

    class MqttPublisher(BaseScanner):
        def __init__(
            self,
            *,
            keys: list[str],
            user_settings: UserSettings,
        ):
            super().__init__()
            self.device_handler = DeviceHandler(keys)
            self.victron_mqtt_handler = VictronMqttDeviceHandler(user_settings=user_settings)

            self.mqtt_client = get_connected_client(settings=user_settings.mqtt, verbosity=verbosity)
            self.mqtt_client.loop_start()

            self.wifi_info = None

            self.rssi_info = {}

        def _detection_callback(self, device: BLEDevice, advertisement: AdvertisementData):
            self.rssi_info[device.address] = advertisement.rssi
            return super()._detection_callback(device, advertisement)

        def callback(self, ble_device: BLEDevice, raw_data: bytes):
            logger.debug(f'Received data from {ble_device.address.lower()}: {raw_data.hex()}')

            if generic_device := self.device_handler.get_generic_device(ble_device, raw_data):
                self.victron_mqtt_handler.publish(
                    ble_device=ble_device,
                    raw_data=raw_data,
                    generic_device=generic_device,
                    rssi=self.rssi_info.get(ble_device.address),
                    mqtt_client=self.mqtt_client,
                )
            else:
                logger.warning(f'Unsupported: {ble_device.name} ({ble_device.address})')

            #     self.wifi_info = WifiInfo2Mqtt(device=self.device, verbosity=self.verbosity)
            #
            # self.rssi_sensor.set_state(self.rssi)
            # self.device_address.set_state(ble_device.address)
            #
            # # Information about WIFI quality:
            # self.wifi_info.poll_and_publish(self.mqtt_client)
            #
            # try:
            #     device = self.get_device(ble_device, raw_data)
            # except UnknownDeviceError as e:
            #     logger.error(e)
            # else:
            #     data: DeviceData = device.parse(raw_data)
            #     data_dict = values2dict(data)
            #
            #     for key, value in data_dict.items():
            #
            #         if sensor := self.sensors.get(key):
            #             sensor.set_state(value)
            #             sensor.publish(self.mqtt_client)
            #         else:
            #             logger.warning(f'No mapping for: {key=} {value=}')

    async def scan(*, keys: list[str], user_settings: UserSettings):
        scanner = MqttPublisher(
            keys=keys,
            user_settings=user_settings,
        )
        await scanner.start()

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(
        scan(
            keys=keys,
            user_settings=user_settings,
        )
    )
    loop.run_forever()
