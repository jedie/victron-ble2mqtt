"""
    Allow victron_ble2mqtt to be executable
    through `python -m victron_ble2mqtt`.
"""


from victron_ble2mqtt.cli import cli_app


def main():
    cli_app.main()


if __name__ == '__main__':
    main()
