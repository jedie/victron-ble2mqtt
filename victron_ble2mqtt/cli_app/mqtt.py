"""
    CLI for usage
"""

import asyncio
import logging
import time

from bleak import AdvertisementData, BLEDevice
from cli_base.cli_tools.verbosity import setup_logging
from cli_base.toml_settings.api import TomlSettings
from cli_base.tyro_commands import TyroVerbosityArgType
from ha_services.mqtt4homeassistant.mqtt import get_connected_client
from rich import print  # noqa
from victron_ble.scanner import BaseScanner

from victron_ble2mqtt.cli_app import app
from victron_ble2mqtt.cli_app.settings import get_settings
from victron_ble2mqtt.mqtt import VictronMqttDeviceHandler
from victron_ble2mqtt.user_settings import UserSettings
from victron_ble2mqtt.victron_ble_utils import DeviceHandler


logger = logging.getLogger(__name__)


@app.command
def publish_loop(verbosity: TyroVerbosityArgType):
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

            self.rssi_info = {}

            self.next_publish = 0

        def _detection_callback(self, device: BLEDevice, advertisement: AdvertisementData):
            self.rssi_info[device.address] = advertisement.rssi
            return super()._detection_callback(device, advertisement)

        def callback(self, ble_device: BLEDevice, raw_data: bytes):
            logger.debug(f'Received data from {ble_device.address.lower()}: {raw_data.hex()}')

            if generic_device := self.device_handler.get_generic_device(ble_device, raw_data):
                if time.monotonic() < self.next_publish:
                    logger.debug(f'Skipping publish for {ble_device.name} ({ble_device.address}) due to throttle.')
                    return

                self.victron_mqtt_handler.publish(
                    ble_device=ble_device,
                    raw_data=raw_data,
                    generic_device=generic_device,
                    rssi=self.rssi_info.get(ble_device.address),
                    mqtt_client=self.mqtt_client,
                )
                self.next_publish = time.monotonic() + user_settings.publish_throttle_seconds
            else:
                logger.warning(f'Unsupported: {ble_device.name} ({ble_device.address})')

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
