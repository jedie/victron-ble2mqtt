#
# TODO: Move to ha-services !
#
import inspect
import logging
from unittest import TestCase
from unittest.mock import patch

from bx_py_utils.test_utils.snapshot import assert_snapshot
from ha_services.mqtt4homeassistant.device import MainMqttDevice
from ha_services.mqtt4homeassistant.mocks.mqtt_client_mock import MqttClientMock

from victron_ble2mqtt.wifi_info import (
    WifiInfo,
    WifiInfo2Mqtt,
    WifiInfoValue,
    _convert_iwconfig_values,
    _get_iwconfig_values,
    get_wifi_infos,
)


class WifiInfoTestCase(TestCase):
    def test_happy_path(self):
        mocked_output = inspect.cleandoc(
            """
            lo        no wireless extensions.

            docker0   no wireless extensions.

            wlo1      IEEE 802.11  ESSID:"foobar"
                      Mode:Managed  Frequency:5.18 GHz  Access Point: 12:34:56:78:AB:CD
                      Bit Rate=29.2 Mb/s   Tx-Power=22 dBm
                      Retry short limit:7   RTS thr:off   Fragment thr:off
                      Power Management:on
                      Link Quality=45/70  Signal level=-65 dBm
                      Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
                      Tx excessive retries:0  Invalid misc:511   Missed beacon:0
            """
        )
        with (
            patch('victron_ble2mqtt.wifi_info.verbose_check_output', return_value=mocked_output),
            self.assertLogs('victron_ble2mqtt', level=logging.DEBUG),
        ):
            iwconfig_values = _get_iwconfig_values(verbosity=0)
        self.assertEqual(
            iwconfig_values,
            {
                'wlo1': {
                    'ESSID': 'foobar',
                    'bit_rate': '29.2',
                    'bit_rate_unit': 'Mb/s',
                    'frequency': '5.18',
                    'frequency_unit': 'GHz',
                    'link_quality': '45/70',
                    'signal_level': '-65',
                    'signal_level_unit': 'dBm',
                }
            },
        )

        ##########################################################################################

        WIFI_INFOS = [
            WifiInfo(
                device_name='wlo1',
                values=[
                    WifiInfoValue(slug='ESSID', name='Essid', value='foobar', unit=None),
                    WifiInfoValue(slug='bit_rate', name='Bit rate', value=29.2, unit='Mb/s'),
                    WifiInfoValue(slug='frequency', name='Frequency', value=5.18, unit='GHz'),
                    WifiInfoValue(slug='link_quality', name='Link quality', value='45/70', unit=None),
                    WifiInfoValue(slug='signal_level', name='Signal level', value=-65, unit='dBm'),
                ],
            )
        ]

        self.assertEqual(_convert_iwconfig_values(iwconfig_values), WIFI_INFOS)

        ##########################################################################################

        with (
            patch('victron_ble2mqtt.wifi_info.verbose_check_output', return_value=mocked_output),
            self.assertLogs('victron_ble2mqtt'),
        ):
            wifi_infos = get_wifi_infos(verbosity=0)
        self.assertEqual(wifi_infos, WIFI_INFOS)

        ##########################################################################################

        mqtt_client_mock = MqttClientMock()
        wifi_info2mqtt = WifiInfo2Mqtt(device=MainMqttDevice(name='Main Device', uid='main_uid'), verbosity=0)

        with patch('victron_ble2mqtt.wifi_info.get_wifi_infos', return_value=WIFI_INFOS):
            wifi_info2mqtt.poll_and_publish(client=mqtt_client_mock)

        # Some pre-checks:
        topics = [msg['topic'] for msg in mqtt_client_mock.messages]
        self.assertEqual(
            topics,
            [
                'homeassistant/sensor/main_uid/main_uid-wifi_device_name/config',
                'homeassistant/sensor/main_uid/main_uid-wifi_device_name/state',
                'homeassistant/sensor/main_uid/main_uid-ESSID/config',
                'homeassistant/sensor/main_uid/main_uid-ESSID/state',
                'homeassistant/sensor/main_uid/main_uid-bit_rate/config',
                'homeassistant/sensor/main_uid/main_uid-bit_rate/state',
                'homeassistant/sensor/main_uid/main_uid-frequency/config',
                'homeassistant/sensor/main_uid/main_uid-frequency/state',
                'homeassistant/sensor/main_uid/main_uid-link_quality/config',
                'homeassistant/sensor/main_uid/main_uid-link_quality/state',
                'homeassistant/sensor/main_uid/main_uid-signal_level/config',
                'homeassistant/sensor/main_uid/main_uid-signal_level/state',
            ],
        )
        for message in mqtt_client_mock.messages:
            topic = message['topic']
            payload = message['payload']
            self.assertIsInstance(payload, (int, float, str), message)
            if topic.endswith('/state'):
                if 'bit_rate' in topic:
                    self.assertEqual(payload, 29.2)
                elif 'frequency' in topic:
                    self.assertEqual(payload, 5.18)

        assert_snapshot(got=mqtt_client_mock.messages)
