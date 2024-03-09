# victron_ble2mqtt

[![tests](https://github.com/jedie/victron-ble2mqtt/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/jedie/victron-ble2mqtt/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/jedie/victron_ble2mqtt/branch/main/graph/badge.svg)](https://app.codecov.io/github/jedie/victron_ble2mqtt)
[![victron_ble2mqtt @ PyPi](https://img.shields.io/pypi/v/victron_ble2mqtt?label=victron_ble2mqtt%20%40%20PyPi)](https://pypi.org/project/victron_ble2mqtt/)
[![Python Versions](https://img.shields.io/pypi/pyversions/victron_ble2mqtt)](https://github.com/jedie/victron-ble2mqtt/blob/main/pyproject.toml)
[![License GPL-3.0-or-later](https://img.shields.io/pypi/l/victron_ble2mqtt)](https://github.com/jedie/victron-ble2mqtt/blob/main/LICENSE)

Emit MQTT events from Victron Energy Solar Charger via [victron-ble](https://github.com/keshavdv/victron-ble)

Tested with:

 * Solar Charger: [SmartSolar MPPT 100/20](https://www.victronenergy.de/solar-charge-controllers/smartsolar-mppt-75-10-75-15-100-15-100-20)
 * [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) with [Raspberry Pi OS Lite](https://www.raspberrypi.com/software/operating-systems/)
 * [Mosquitto MQTT Broker](https://mosquitto.org/)
 * [Home Assistant MQTT integration](https://www.home-assistant.io/integrations/mqtt/)

## Usage

### Bootstrap

Clone the sources and just call the CLI to create a Python Virtualenv, e.g.:

```bash
~$ git clone https://github.com/jedie/victron-ble2mqtt.git
~$ cd victron-ble2mqtt
~/victron-ble2mqtt$ ./cli.py --help
```

### Setup Device

Detect your device first, e.g.:
```bash
~/victron-ble2mqtt$ ./cli.py discover
...
{
    'name': 'SmartSolar HQ2248AM79D',
    'address': 'E7:37:97:XX:XX:XX',
    'details': {
        'path': '/org/bluez/hci0/dev_E7_37_97_XX_XX_XX',
        'props': {
            'Address': 'E7:37:97:XX:XX:XX',
            'AddressType': 'random',
            'Name': 'SmartSolar HQ2248AM79D',
            'Alias': 'SmartSolar HQ2248AM79D',
            'Paired': False,
            'Trusted': False,
            'Blocked': False,
            'LegacyPairing': False,
            'RSSI': -89,
            'Connected': False,
            'UUIDs': [],
            'Adapter': '/org/bluez/hci0',
            'ManufacturerData': {737: bytearray(b'...')},
            'ServicesResolved': False
        }
    }
}
...
(Hit Ctrl-C to abort)
```

### Device Key

You need the Device MAC address and the key.

The easiest way to get the device key: Install the official Victron Smartphone and and copy&paste the key:

* Click on your SmartSolar device
* Go to detail page about the `SmartSolar Bluetooth Interface`
* Click on `SHOW` at `Instant readout via Bluetooth` / `Encryption data`
* Copy the Connectionkey by click on the key

(I send the key via Signal as "my note" and use the Desktop Signal app to receive the key on my Computer)

See also: https://community.victronenergy.com/questions/187303/victron-bluetooth-advertising-protocol.html

### setting

Just call `edit-settings` command, e.g.:
```bash
~/victron-ble2mqtt$ ./cli.py edit-settings
```

At least insert your MQTT settings and the device MAC and key.

### Test

Start publish MQTT endless look, just call `publish-loop` command, e.g.:
```bash
~/victron-ble2mqtt$ ./cli.py publish-loop
```

### setup systemd services

Check systemd setup:
```bash
~/victron-ble2mqtt$ ./cli.py systemd-debug
```

Setup services:
```bash
~/victron-ble2mqtt$ ./cli.py systemd-setup
```

Check the services:
```bash
~/victron-ble2mqtt$ ./cli.py systemd-status
```
