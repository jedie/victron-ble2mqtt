"""
    Allow victron_ble2mqtt to be executable
    through `python -m victron_ble2mqtt.cli_dev`.
"""

from victron_ble2mqtt.cli_dev import main


if __name__ == '__main__':
    main()
