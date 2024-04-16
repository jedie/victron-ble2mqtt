"""
    CLI for usage
"""

import asyncio
import logging
import time

import rich_click as click
from bleak import AdvertisementData, BLEDevice
from cli_base.cli_tools.verbosity import OPTION_KWARGS_VERBOSE, setup_logging
from cli_base.toml_settings.api import TomlSettings
from ha_services.mqtt4homeassistant.components.sensor import Sensor
from ha_services.mqtt4homeassistant.device import MainMqttDevice
from ha_services.mqtt4homeassistant.mqtt import get_connected_client
from rich import print  # noqa
from victron_ble.devices import DeviceData
from victron_ble.exceptions import UnknownDeviceError
from victron_ble.scanner import Scanner

from victron_ble2mqtt.cli_app import cli
from victron_ble2mqtt.cli_app.settings import get_settings
from victron_ble2mqtt.user_settings import UserSettings
from victron_ble2mqtt.victron_ble_utils import values2dict
from victron_ble2mqtt.wifi_info import WifiInfo2Mqtt


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

            self.mqtt_client = get_connected_client(settings=user_settings.mqtt, verbosity=verbosity)
            self.mqtt_client.loop_start()

            self.verbosity = verbosity

            self.device = None
            self.device_address = None

            self.wifi_info = None

            self.rssi = None
            self.rssi_sensor = None

        def _detection_callback(self, device: BLEDevice, advertisement: AdvertisementData):
            self.rssi = advertisement.rssi
            return super()._detection_callback(device, advertisement)

        def callback(self, ble_device: BLEDevice, raw_data: bytes):
            logger.debug(f"Received data from {ble_device.address.lower()}: {raw_data.hex()}")

            if self.device is None:
                self.device = MainMqttDevice(
                    name=user_settings.device_name,
                    uid=user_settings.mqtt.main_uid,
                    manufacturer='Victron Energy',
                    model=ble_device.name,
                    sw_version=None,  # TODO
                    config_throttle_sec=user_settings.mqtt.publish_config_throttle_seconds,
                )
                self.rssi_sensor = Sensor(
                    device=self.device,
                    name='RSSI',
                    uid='rssi',
                    state_class='measurement',
                )
                self.device_address = Sensor(
                    device=self.device,
                    name='Device Address',
                    uid='device_address',
                )

                self.sensors = {
                    'battery_charging_current': Sensor(
                        device=self.device,
                        name='Battery Charging',
                        uid='battery_charging_current',
                        device_class='current',
                        state_class='measurement',
                        unit_of_measurement='A',
                    ),
                    'battery_voltage': Sensor(
                        device=self.device,
                        name='Battery',
                        uid='battery_voltage',
                        device_class='voltage',
                        state_class='measurement',
                        unit_of_measurement='V',
                    ),
                    'charge_state': Sensor(
                        device=self.device,
                        uid='charge_state',
                        name='Charge State',
                    ),
                    'external_device_load': Sensor(
                        device=self.device,
                        name='Load',
                        uid='load',
                        device_class='current',
                        state_class='measurement',
                        unit_of_measurement='A',
                    ),
                    'model_name': Sensor(
                        device=self.device,
                        uid='model_name',
                        name='Model Name',
                    ),
                    'solar_power': Sensor(
                        device=self.device,
                        name='Solar',
                        uid='solar_power',
                        device_class='energy',
                        state_class='measurement',
                        unit_of_measurement='W',
                    ),
                    'yield_today': Sensor(
                        device=self.device,
                        name='Yield Today',
                        uid='yield_today',
                        device_class='energy',
                        state_class='measurement',
                        unit_of_measurement='Wh',
                    ),
                }

                self.wifi_info = WifiInfo2Mqtt(device=self.device, verbosity=self.verbosity)

            self.rssi_sensor.set_state(self.rssi)
            self.device_address.set_state(ble_device.address)

            # Information about WIFI quality:
            self.wifi_info.poll_and_publish(self.mqtt_client)

            try:
                device = self.get_device(ble_device, raw_data)
            except UnknownDeviceError as e:
                logger.error(e)
            else:
                data: DeviceData = device.parse(raw_data)
                data_dict = values2dict(data)

                for key, value in data_dict.items():

                    if sensor := self.sensors.get(key):
                        sensor.set_state(value)
                        sensor.publish(self.mqtt_client)
                    else:
                        logger.warning(f'No mapping for: {key=} {value=}')

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
