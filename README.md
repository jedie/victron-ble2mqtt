# victron_ble2mqtt

[![tests](https://github.com/jedie/victron-ble2mqtt/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/jedie/victron-ble2mqtt/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/jedie/victron_ble2mqtt/branch/main/graph/badge.svg)](https://app.codecov.io/github/jedie/victron_ble2mqtt)
[![victron_ble2mqtt @ PyPi](https://img.shields.io/pypi/v/victron_ble2mqtt?label=victron_ble2mqtt%20%40%20PyPi)](https://pypi.org/project/victron_ble2mqtt/)
[![Python Versions](https://img.shields.io/pypi/pyversions/victron_ble2mqtt)](https://github.com/jedie/victron-ble2mqtt/blob/main/pyproject.toml)
[![License GPL-3.0-or-later](https://img.shields.io/pypi/l/victron_ble2mqtt)](https://github.com/jedie/victron-ble2mqtt/blob/main/LICENSE)

Emit MQTT events from Victron Energy Solar Charger via [victron-ble](https://github.com/keshavdv/victron-ble)

**This is in early, not useable state!**

Tested with:

 * Solar Charger: [SmartSolar MPPT 100/20](https://www.victronenergy.de/solar-charge-controllers/smartsolar-mppt-75-10-75-15-100-15-100-20)
 * [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) with [Raspberry Pi OS Lite](https://www.raspberrypi.com/software/operating-systems/)
 * [Mosquitto MQTT Broker](https://mosquitto.org/)
 * [Home Assistant MQTT integration](https://www.home-assistant.io/integrations/mqtt/)

