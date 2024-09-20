import logging

import rich_click as click
from cli_base.cli_tools.verbosity import OPTION_KWARGS_VERBOSE, setup_logging
from rich import print  # noqa

from victron_ble2mqtt.cli_app import cli
from victron_ble2mqtt.wifi_info import get_wifi_infos


logger = logging.getLogger(__name__)


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def wifi_info(verbosity: int):
    """
    Just display the WiFi info
    """
    setup_logging(verbosity=verbosity)

    wifi_infos = get_wifi_infos(verbosity=verbosity)
    print(wifi_infos)
