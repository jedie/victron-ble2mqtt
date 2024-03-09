import dataclasses

from cli_base.systemd.data_classes import BaseSystemdServiceInfo, BaseSystemdServiceTemplateContext


@dataclasses.dataclass
class SystemdServiceTemplateContext(BaseSystemdServiceTemplateContext):
    """
    Context values for the systemd service file content.
    """

    verbose_service_name: str = 'victron-ble2mqtt'


@dataclasses.dataclass
class SystemdServiceInfo(BaseSystemdServiceInfo):
    """
    Information for systemd helper functions.
    """

    template_context: SystemdServiceTemplateContext = dataclasses.field(default_factory=SystemdServiceTemplateContext)


@dataclasses.dataclass
class UserSettings:
    """
    Victron-BLE -> MQTT - settings

    Note: Insert at least device address + key

    See README for more information.
    """
    systemd: dataclasses = dataclasses.field(default_factory=SystemdServiceInfo)

    device_address: str = '<device MAC address>'
    device_key: str = '<insert your device key here>'
