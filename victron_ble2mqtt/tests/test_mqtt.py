from unittest import TestCase

from bleak import BLEDevice
from ha_services.mqtt4homeassistant.data_classes import MqttSettings
from ha_services.mqtt4homeassistant.device import MainMqttDevice
from ha_services.tests.base import ComponentTestMixin
from paho.mqtt.client import Client
from paho.mqtt.enums import CallbackAPIVersion
from victron_ble.devices import BatteryMonitor

from victron_ble2mqtt.mqtt import BatteryMonitorHandler, SolarChargerHandler
from victron_ble2mqtt.user_settings import UserSettings


class MqttTestCase(ComponentTestMixin, TestCase):
    def test_battery_monitor_handler(self):
        dummy_ble_device = BLEDevice(
            address='dummy_address',
            name='dummy-name',
            details={},
        )
        main_mqtt_device = MainMqttDevice(name='foo', uid='bar')
        victron_device = BatteryMonitor(advertisement_key='fake-key')
        mqtt_client = Client(callback_api_version=CallbackAPIVersion.VERSION2)
        user_settings = UserSettings(mqtt=MqttSettings(main_uid='foo_bar'))

        handler = BatteryMonitorHandler(
            ble_device=dummy_ble_device,
            main_mqtt_device=main_mqtt_device,
            victron_device=victron_device,
            mqtt_client=mqtt_client,
            user_settings=user_settings,
        )

        # Now the test: Initialize all sensors, so that ha-services will validate them:
        handler.setup(data_dict={'model_name': 'SmartShunt 500A/50mV'})

    def test_solar_charger_handler(self):
        dummy_ble_device = BLEDevice(
            address='dummy_address',
            name='dummy-name',
            details={},
        )
        main_mqtt_device = MainMqttDevice(name='foo', uid='bar')
        victron_device = BatteryMonitor(advertisement_key='fake-key')
        mqtt_client = Client(callback_api_version=CallbackAPIVersion.VERSION2)
        user_settings = UserSettings(mqtt=MqttSettings(main_uid='foo_bar'))

        handler = SolarChargerHandler(
            ble_device=dummy_ble_device,
            main_mqtt_device=main_mqtt_device,
            victron_device=victron_device,
            mqtt_client=mqtt_client,
            user_settings=user_settings,
        )

        # Now the test: Initialize all sensors, so that ha-services will validate them:
        handler.setup(data_dict={'model_name': 'SmartSolar MPPT 100|20 48V'})
