import inspect
import logging
from unittest import TestCase
from unittest.mock import patch

from ha_services.mqtt4homeassistant.data_classes import HaValue

from victron_ble2mqtt.wifi_info import (
    WifiInfo,
    WifiInfoValue,
    _convert_iwconfig_values,
    _get_iwconfig_values,
    get_wifi_info_ha_values,
    get_wifi_infos,
)


class WifiInfoTestCase(TestCase):
    def test_get_iwconfig_values(self):
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

    def test_convert_iwconfig_values(self):
        self.assertEqual(
            _convert_iwconfig_values(
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
                }
            ),
            [
                WifiInfo(
                    device_name='wlo1',
                    values=[
                        WifiInfoValue(name='ESSID', value='foobar', unit=None),
                        WifiInfoValue(name='bit rate', value=29.2, unit='Mb/s'),
                        WifiInfoValue(name='frequency', value=5.18, unit='GHz'),
                        WifiInfoValue(name='link quality', value='45/70', unit=None),
                        WifiInfoValue(name='signal level', value=-65, unit='dBm'),
                    ],
                )
            ],
        )

    def test_get_wifi_info(self):
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
            self.assertLogs('victron_ble2mqtt'),
        ):
            wifi_infos = get_wifi_infos(verbosity=0)
        self.assertEqual(
            wifi_infos,
            [
                WifiInfo(
                    device_name='wlo1',
                    values=[
                        WifiInfoValue(name='ESSID', value='foobar', unit=None),
                        WifiInfoValue(name='bit rate', value=29.2, unit='Mb/s'),
                        WifiInfoValue(name='frequency', value=5.18, unit='GHz'),
                        WifiInfoValue(name='link quality', value='45/70', unit=None),
                        WifiInfoValue(name='signal level', value=-65, unit='dBm'),
                    ],
                )
            ],
        )

    def test_get_wifi_info_ha_values(self):
        mocked_wifi_info = [
            WifiInfo(
                device_name='wlo1',
                values=[
                    WifiInfoValue(name='ESSID', value='foobar', unit=None),
                    WifiInfoValue(name='bit rate', value=29.2, unit='Mb/s'),
                    WifiInfoValue(name='frequency', value=5.18, unit='GHz'),
                    WifiInfoValue(name='link quality', value='45/70', unit=None),
                    WifiInfoValue(name='signal level', value=-65, unit='dBm'),
                ],
            )
        ]
        with patch('victron_ble2mqtt.wifi_info.get_wifi_infos', return_value=mocked_wifi_info):
            ha_values = get_wifi_info_ha_values(verbosity=0)
        self.assertEqual(
            ha_values,
            [
                HaValue(name='Device Name', value='wlo1', device_class=None, state_class=None, unit=None),
                HaValue(name='ESSID', value='foobar', device_class=None, state_class=None, unit=None),
                HaValue(name='bit rate', value=29.2, device_class=None, state_class='measurement', unit='Mb/s'),
                HaValue(name='frequency', value=5.18, device_class=None, state_class='measurement', unit='GHz'),
                HaValue(name='link quality', value='45/70', device_class=None, state_class=None, unit=None),
                HaValue(name='signal level', value=-65, device_class=None, state_class='measurement', unit='dBm'),
            ],
        )
