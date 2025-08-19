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

[comment]: <> (✂✂✂ auto generated main help start ✂✂✂)
```
usage: ./cli.py [-h]
                {debug-read,discover,edit-settings,print-settings,publish-loop,systemd-debug,systemd-logs,systemd-remo
ve,systemd-setup,systemd-status,systemd-stop,update-readme-history,version}



╭─ options ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ -h, --help        show this help message and exit                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ subcommands ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ {debug-read,discover,edit-settings,print-settings,publish-loop,systemd-debug,systemd-logs,systemd-remove,systemd-s │
│ etup,systemd-status,systemd-stop,update-readme-history,version}                                                    │
│     debug-read    Read data from devices and print them. Device keys are used from config file, if not given.      │
│     discover      Discover Victron devices with Instant Readout                                                    │
│     edit-settings                                                                                                  │
│                   Edit the settings file. On first call: Create the default one.                                   │
│     print-settings                                                                                                 │
│                   Display (anonymized) MQTT server username and password                                           │
│     publish-loop  Publish MQTT messages in endless loop (Entrypoint from systemd)                                  │
│     systemd-debug                                                                                                  │
│                   Print Systemd service template + context + rendered file content.                                │
│     systemd-logs  Display the systemd logs for this service. (May need sudo)                                       │
│     systemd-remove                                                                                                 │
│                   Remove Systemd service file. (May need sudo)                                                     │
│     systemd-setup                                                                                                  │
│                   Write Systemd service file, enable it and (re-)start the service. (May need sudo)                │
│     systemd-status                                                                                                 │
│                   Display status of systemd service. (May need sudo)                                               │
│     systemd-stop  Stops the systemd service. (May need sudo)                                                       │
│     update-readme-history                                                                                          │
│                   Update project history base on git commits/tags in README.md Will be exited with 1 if the        │
│                   README.md was updated otherwise with 0.                                                          │
│                                                                                                                    │
│                   Also, callable via e.g.:                                                                         │
│                       python -m cli_base update-readme-history -v                                                  │
│     version       Print version and exit                                                                           │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
[comment]: <> (✂✂✂ auto generated main help end ✂✂✂)



# dev CLI

[comment]: <> (✂✂✂ auto generated dev help start ✂✂✂)
```
usage: ./dev-cli.py [-h]
                    {check-code-style,coverage,fix-code-style,install,mypy,nox,pip-audit,publish,test,update,update-te
st-snapshot-files,version}



╭─ options ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ -h, --help        show this help message and exit                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ subcommands ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ {check-code-style,coverage,fix-code-style,install,mypy,nox,pip-audit,publish,test,update,update-test-snapshot-file │
│ s,version}                                                                                                         │
│     check-code-style                                                                                               │
│                   Check code style by calling darker + flake8                                                      │
│     coverage      Run tests and show coverage report.                                                              │
│     fix-code-style                                                                                                 │
│                   Fix code style of all victron_ble2mqtt source code files via darker                              │
│     install       Install requirements and 'victron_ble2mqtt' via pip as editable.                                 │
│     mypy          Run Mypy (configured in pyproject.toml)                                                          │
│     nox           Run nox                                                                                          │
│     pip-audit     Run pip-audit check against current requirements files                                           │
│     publish       Build and upload this project to PyPi                                                            │
│     test          Run unittests                                                                                    │
│     update        Update "requirements*.txt" dependencies files                                                    │
│     update-test-snapshot-files                                                                                     │
│                   Update all test snapshot files (by remove and recreate all snapshot files)                       │
│     version       Print version and exit                                                                           │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
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


# History

[comment]: <> (✂✂✂ auto generated history start ✂✂✂)

* [v0.7.0](https://github.com/jedie/victron-ble2mqtt/compare/v0.6.0...v0.7.0)
  * 2025-08-19 - NEW: "./cli.py systemd-logs"
  * 2025-08-19 - Add new setting: `publish_throttle_seconds` for #31
  * 2025-08-19 - Update requirements
  * 2025-06-17 - Limit sensor values
* [v0.6.0](https://github.com/jedie/victron-ble2mqtt/compare/v0.5.1...v0.6.0)
  * 2025-04-08 - Remove own Wifi info stuff
* [v0.5.1](https://github.com/jedie/victron-ble2mqtt/compare/v0.5.0...v0.5.1)
  * 2025-04-08 - pip-tools -> uv
* [v0.5.0](https://github.com/jedie/victron-ble2mqtt/compare/v0.4.1...v0.5.0)
  * 2024-09-25 - NEW: Midpoint Shift (absolut + percent) in BatteryMonitor

<details><summary>Expand older history entries ...</summary>

* [v0.4.1](https://github.com/jedie/victron-ble2mqtt/compare/v0.4.0...v0.4.1)
  * 2024-09-24 - Bugfix delay data: Never, never use time.sleep() in a async context
* [v0.4.0](https://github.com/jedie/victron-ble2mqtt/compare/v0.3.0...v0.4.0)
  * 2024-09-24 - Update README.md
  * 2024-09-22 - Use device keys and refactor MQTT sensors: Support BatteryMonitor
  * 2024-09-22 - Bugfix Pi installation
  * 2024-09-22 - Move pip-compile switches into pyproject.toml
  * 2024-09-22 - Update requirements
* [v0.3.0](https://github.com/jedie/victron-ble2mqtt/compare/v0.1.0...v0.3.0)
  * 2024-09-20 - bugfix publish
  * 2024-09-20 - Add help pages into README
  * 2024-04-16 - Update to new ha-services version and update project setup
  * 2024-03-23 - Update README.md
  * 2024-03-10 - Disable verbose print as default
  * 2024-03-10 - Expose WiFi quality values to MQTT
* [v0.1.0](https://github.com/jedie/victron-ble2mqtt/compare/2bff08d...v0.1.0)
  * 2024-03-09 - Remove 3.9 from test matrix
  * 2024-03-09 - requires-python = ">=3.10"
  * 2024-03-09 - Update README.md
  * 2024-03-09 - Add Hostname + sys load to MQTT
  * 2024-03-09 - Add info about systemd to README
  * 2024-03-09 - Remove deprecation warning about RSSI
  * 2024-03-09 - Bugfix systemd "exec_start" value
  * 2024-03-09 - Add systemd commands
  * 2024-03-09 - Publish value to MQTT
  * 2024-03-09 - Add user settings and "debug-read" CLI command
  * 2024-03-09 - Add "discover" to app CLI
  * 2024-03-08 - More info in README
  * 2024-03-08 - Add "victron-ble" and "ha-services"
  * 2024-03-08 - Init from https://github.com/jedie/cookiecutter_templates

</details>


[comment]: <> (✂✂✂ auto generated history end ✂✂✂)
