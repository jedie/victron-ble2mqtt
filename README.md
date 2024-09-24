# victron_ble2mqtt

[![tests](https://github.com/jedie/victron-ble2mqtt/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/jedie/victron-ble2mqtt/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/jedie/victron-ble2mqtt/branch/main/graph/badge.svg)](https://app.codecov.io/github/jedie/victron-ble2mqtt)
[![victron_ble2mqtt @ PyPi](https://img.shields.io/pypi/v/victron_ble2mqtt?label=victron_ble2mqtt%20%40%20PyPi)](https://pypi.org/project/victron_ble2mqtt/)
[![Python Versions](https://img.shields.io/pypi/pyversions/victron_ble2mqtt)](https://github.com/jedie/victron-ble2mqtt/blob/main/pyproject.toml)
[![License GPL-3.0-or-later](https://img.shields.io/pypi/l/victron_ble2mqtt)](https://github.com/jedie/victron-ble2mqtt/blob/main/LICENSE)

Emit MQTT events from Victron Energy Smart Devices via [victron-ble](https://github.com/keshavdv/victron-ble)

Tested with:

 * Solar Charger: [SmartSolar MPPT 100/20](https://www.victronenergy.de/solar-charge-controllers/smartsolar-mppt-75-10-75-15-100-15-100-20)
 * [Smart Battery Shunt](https://www.victronenergy.de/battery-monitors/smart-battery-shunt)
 * [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) with [Raspberry Pi OS Lite](https://www.raspberrypi.com/software/operating-systems/)
 * [Mosquitto MQTT Broker](https://mosquitto.org/)
 * [Home Assistant MQTT integration](https://www.home-assistant.io/integrations/mqtt/)

Scrrenshot from Home Assistant:

![2024-09-24 victron-ble2mqtt v0.4.0 Home Assistant 1.png](https://raw.githubusercontent.com/jedie/jedie.github.io/master/screenshots/victron-ble2mqtt/2024-09-24%20victron-ble2mqtt%20v0.4.0%20Home%20Assistant%201.png "2024-09-24 victron-ble2mqtt v0.4.0 Home Assistant 1.png")

More screenshots here: https://github.com/jedie/jedie.github.io/blob/master/screenshots/victron-ble2mqtt/README.md

## Usage

### preperation

`victron_ble` used [Bleak](https://pypi.org/project/bleak/) and the Linux backend of Bleak communicates with BlueZ over DBus. So you have to install this, e.g.:
```bash
~$ sudo apt install bluez
```

### Bootstrap

Clone the sources and just call the CLI to create a Python Virtualenv, e.g.:

```bash
~$ git clone https://github.com/jedie/victron-ble2mqtt.git
~$ cd victron-ble2mqtt
~/victron-ble2mqtt$ ./cli.py --help
```


# app CLI

[comment]: <> (✂✂✂ auto generated app help start ✂✂✂)
```
Usage: ./cli.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --help      Show this message and exit.                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────╮
│ debug-read      Read data from devices and print them. Device keys are used from config file, if │
│                 not given.                                                                       │
│ discover        Discover Victron devices with Instant Readout                                    │
│ edit-settings   Edit the settings file. On first call: Create the default one.                   │
│ print-settings  Display (anonymized) MQTT server username and password                           │
│ publish-loop    Publish MQTT messages in endless loop (Entrypoint from systemd)                  │
│ systemd-debug   Print Systemd service template + context + rendered file content.                │
│ systemd-remove  Remove Systemd service file. (May need sudo)                                     │
│ systemd-setup   Write Systemd service file, enable it and (re-)start the service. (May need      │
│                 sudo)                                                                            │
│ systemd-status  Display status of systemd service. (May need sudo)                               │
│ systemd-stop    Stops the systemd service. (May need sudo)                                       │
│ version         Print version and exit                                                           │
│ wifi-info       Just display the WiFi info                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```
[comment]: <> (✂✂✂ auto generated app help end ✂✂✂)



# dev CLI

[comment]: <> (✂✂✂ auto generated dev help start ✂✂✂)
```
Usage: ./dev-cli.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --help      Show this message and exit.                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────╮
│ check-code-style            Check code style by calling darker + flake8                          │
│ coverage                    Run tests and show coverage report.                                  │
│ fix-code-style              Fix code style of all cli_base source code files via darker          │
│ install                     Run pip-sync and install 'cli_base' via pip as editable.             │
│ mypy                        Run Mypy (configured in pyproject.toml)                              │
│ pip-audit                   Run pip-audit check against current requirements files               │
│ publish                     Build and upload this project to PyPi                                │
│ test                        Run unittests                                                        │
│ tox                         Run tox                                                              │
│ update                      Update "requirements*.txt" dependencies files                        │
│ update-test-snapshot-files  Update all test snapshot files (by remove and recreate all snapshot  │
│                             files)                                                               │
│ version                     Print version and exit                                               │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```
[comment]: <> (✂✂✂ auto generated dev help end ✂✂✂)


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

### Device Keys

You need the device keys of all Victron Energy Smart Devices you want to monitor.

The easiest way to get the keys: Install the official Victron Smartphone App and copy&paste the keys:

* Click on your device
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

At least insert your MQTT settings and all devices keys.

### Test

Start publish MQTT endless look, just call `publish-loop` command, e.g.:
```bash
~/victron-ble2mqtt$ ./cli.py publish-loop -vv
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
After this the MQTT publising runs and will be started on boot.

Check the services:
```bash
~/victron-ble2mqtt$ ./cli.py systemd-status
```

## Backwards-incompatible changes

### 0.4.0

You must edit your settings:

* `device_address` (The Device MAC address) was removed
* `device_key` is replaced by `device_keys` a list of device keys

Just insert the keys of all Victron Energy Smart Devices you want to monitor.
