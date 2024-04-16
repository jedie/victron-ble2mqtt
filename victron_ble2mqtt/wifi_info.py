#
# TODO: Move to ha-services !
#
import dataclasses
import logging
import re

from cli_base.cli_tools.subprocess_utils import verbose_check_output
from ha_services.mqtt4homeassistant.components.sensor import Sensor
from ha_services.mqtt4homeassistant.device import MainMqttDevice
from paho.mqtt.client import Client


logger = logging.getLogger(__name__)


RE_PATTERNS = (
    r'\s+ESSID:"(?P<ESSID>.+)"\s+',
    r'\s+Frequency:(?P<frequency>[\d\.]+?)\s+(?P<frequency_unit>[a-zA-Z]+)\s+',
    r'\s+Bit Rate=(?P<bit_rate>[\d\.]+?)\s+(?P<bit_rate_unit>[a-zA-Z/]+)\s+',
    r'\s+Link Quality=(?P<link_quality>[\d\/]+?)\s+',
    r'\s+Signal level=(?P<signal_level>[-\d\.]+?)\s+(?P<signal_level_unit>[a-zA-Z/]+)\s+',
)


def _get_iwconfig_values(*, verbosity: int = 1) -> dict:
    output = verbose_check_output('iwconfig', verbose=verbosity > 1)

    logger.debug('RAW iwconfig output: %s', output)

    iwconfig_values = {}

    blocks = output.split('\n\n')
    for block in blocks:
        if 'no wireless extensions' in block:
            continue
        if 'ESSID' not in block:
            continue

        device_name = block.partition(' ')[0]

        values = {}
        for re_pattern in RE_PATTERNS:
            match = re.search(re_pattern, block, flags=re.IGNORECASE | re.MULTILINE)
            if match:
                groupdict = match.groupdict()
                values.update(groupdict)

        iwconfig_values[device_name] = values

    return iwconfig_values


@dataclasses.dataclass
class WifiInfoValue:
    slug: str
    name: str
    value: str | float | int
    unit: str | None


@dataclasses.dataclass
class WifiInfo:
    device_name: str
    values: list[WifiInfoValue]


def _convert_iwconfig_values(iwconfig_values: dict) -> list[WifiInfo]:
    wifi_infos = []
    for device_name, values in iwconfig_values.items():
        device_values = []
        for slug, value in sorted(values.items()):
            if slug.endswith('_unit'):
                continue

            if value.isdigit():  # e.g. '123' -> 123
                value = int(value)
            elif re.match(r'\d+\.\d+', value):  # e.g. '1.23' -> 1.23
                value = float(value)
            elif re.match(r'-\d+', value):  # e.g. '-12' -> -12
                value = int(value)

            device_values.append(
                WifiInfoValue(
                    slug=slug,
                    name=slug.replace('_', ' ').capitalize(),  # e.g. 'bit_rate' -> 'Bit rate'
                    value=value,
                    unit=values.get(f'{slug}_unit'),
                )
            )

        wifi_infos.append(
            WifiInfo(
                device_name=device_name,
                values=device_values,
            )
        )

    return wifi_infos


def get_wifi_infos(*, verbosity: int = 1) -> list[WifiInfo]:
    raw_values = _get_iwconfig_values(verbosity=verbosity)
    logger.debug('Raw iwconfig values: %r', raw_values)

    wifi_infos = _convert_iwconfig_values(raw_values)
    logger.info('iwconfig values: %r', wifi_infos)
    return wifi_infos


class WifiInfo2Mqtt:
    def __init__(self, *, device: MainMqttDevice, verbosity: int):
        self.device = device
        self.verbosity = verbosity

        self.wifi_device_name = Sensor(
            device=self.device,
            name='Wifi Device Name',
            uid='wifi_device_name',
        )
        self.sensors = {}

    def poll_and_publish(self, client: Client) -> None:
        wifi_infos = get_wifi_infos(verbosity=self.verbosity)

        device_count = len(wifi_infos)
        if device_count == 0:
            logger.warning('No WiFi devices found')
            return

        if device_count > 1:
            logger.warning('Multiple WiFi devices found, only the first one will be used')

        wifi_info: WifiInfo = wifi_infos[0]

        self.wifi_device_name.set_state(wifi_info.device_name)
        self.wifi_device_name.publish(client)

        for wifi_info_value in wifi_info.values:

            value = wifi_info_value.value  # e.g.: 'foobar', 29.2, ...
            if isinstance(value, (int, float)):
                state_class = 'measurement'
            else:
                state_class = None

            slug = wifi_info_value.slug  # e.g.: 'ESSID', 'bit_rate', ...
            sensor = self.sensors.get(slug)
            if not sensor:
                sensor = self.sensors[slug] = Sensor(
                    device=self.device,
                    name=wifi_info_value.name,  # e.g.: 'ESSID', 'bit rate', ...
                    uid=slug,
                    state_class=state_class,
                    unit_of_measurement=wifi_info_value.unit,  # e.g.: None, 'Mb/s', ...
                )

            sensor.set_state(value)
            sensor.publish(client)
