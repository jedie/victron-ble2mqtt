import inspect
import logging
from enum import Enum

from bleak import BLEDevice
from victron_ble.devices import Device, DeviceData, detect_device_type
from victron_ble.exceptions import AdvertisementKeyMismatchError


logger = logging.getLogger(__name__)


def values2dict(obj: DeviceData) -> dict:
    data = {}
    for name, method in inspect.getmembers(obj, predicate=inspect.ismethod):
        if name.startswith("get_"):
            value = method()
            if isinstance(value, Enum):
                value = value.name.lower()
            if value is not None:
                data[name[4:]] = value
    return data


class GenericDevice:
    def __init__(self, victron_device: Device, ble_device: BLEDevice):
        self.victron_device = victron_device
        self.ble_device = ble_device

    def parse(self, *, raw_data) -> dict:
        device_data: DeviceData = self.victron_device.parse(raw_data)
        data_dict = values2dict(device_data)
        return data_dict


class DeviceHandler:
    def __init__(self, keys: list[str]):
        self.keys = keys
        self.devices = {}

    def get_generic_device(self, device: BLEDevice, raw_data: bytes) -> GenericDevice | None:
        data = dict(name=device.name, address=device.address, details=device.details)
        logger.debug('Received data: %s', data)
        try:
            return self.devices[device.address]
        except KeyError:
            if DeviceClass := detect_device_type(raw_data):
                logger.info('Device type: %s for %s', DeviceClass.__name__, data)
                for key in self.keys:
                    victron_device = DeviceClass(key)
                    try:
                        victron_device.parse(raw_data)
                    except AdvertisementKeyMismatchError:
                        continue
                    except ValueError as err:
                        logger.warning('Error parsing data: %s', err)
                    else:
                        logger.info('New device: %s', device.name)
                        self.devices[device.address] = generic_device = GenericDevice(
                            victron_device,
                            ble_device=device,
                        )
                        return generic_device
            else:
                logger.error('No keys for %s', data)
