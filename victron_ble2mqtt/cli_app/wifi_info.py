import logging

from cli_base.cli_tools.verbosity import setup_logging
from cli_base.tyro_commands import TyroVerbosityArgType
from rich import print  # noqa

from victron_ble2mqtt.cli_app import app
from victron_ble2mqtt.wifi_info import get_wifi_infos


logger = logging.getLogger(__name__)


@app.command
def wifi_info(verbosity: TyroVerbosityArgType):
    """
    Just display the WiFi info
    """
    setup_logging(verbosity=verbosity)

    wifi_infos = get_wifi_infos(verbosity=verbosity)
    print(wifi_infos)
