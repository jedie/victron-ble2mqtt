import logging
import socket

from bleak import BLEDevice
from ha_services.mqtt4homeassistant.components.sensor import Sensor
from ha_services.mqtt4homeassistant.device import MainMqttDevice, MqttDevice
from paho.mqtt.client import Client
from victron_ble.devices import Device, BatteryMonitor, SolarCharger, DcDcConverter, SmartBatteryProtect, AcCharger

import victron_ble2mqtt
from victron_ble2mqtt.user_settings import UserSettings
from victron_ble2mqtt.victron_ble_utils import GenericDevice


logger = logging.getLogger(__name__)


class BaseHandler:
    VictronDeviceClass = None

    def __init__(
        self,
        *,
        ble_device: BLEDevice,
        main_mqtt_device: MainMqttDevice,
        victron_device: Device,
        mqtt_client: Client,
        user_settings: UserSettings,
    ):
        self.ble_device = ble_device
        self.main_mqtt_device = main_mqtt_device
        self.victron_device = victron_device
        self.mqtt_client = mqtt_client
        self.user_settings = user_settings

        self.device = None
        self.rssi_sensor = None
        self.sensors = {}

    def setup(self, *, data_dict):
        mac_address = self.ble_device.address
        uid = mac_address.lower().replace(':', '')
        self.device = MqttDevice(
            main_device=self.main_mqtt_device,
            name=self.ble_device.name,
            uid=uid,
            manufacturer='Victron Energy',
            model=data_dict['model_name'],  # e.g.: 'SmartSolar MPPT 100|20 48V' | 'SmartShunt 500A/50mV',
        )
        self.rssi_sensor = Sensor(
            device=self.device,
            name='RSSI',
            uid='rssi',
            state_class='measurement',
        )

    def publish(self, *, data_dict: dict, rssi: int | None) -> None:
        if self.device is None:
            self.setup(data_dict=data_dict)

        self.main_mqtt_device.poll_and_publish(self.mqtt_client)

        self.rssi_sensor.set_state(rssi)
        self.rssi_sensor.publish(self.mqtt_client)

        for key, value in data_dict.items():
            if key == 'model_name':
                continue

            if sensor := self.sensors.get(key):
                sensor.set_state(value)
                sensor.publish(self.mqtt_client)
            else:
                logger.warning(f'No sensor for key: {key}')


def calc_midpoint_shift(voltage: float, midpoint_voltage: float) -> float:
    """
    Calculate the midpoint shift in percent.

    >>> calc_midpoint_shift(100, 50)
    0.0
    >>> round(calc_midpoint_shift(26.7, 13.2),3)
    0.15
    >>> round(calc_midpoint_shift(100, 50.1),3)
    0.1
    >>> round(calc_midpoint_shift(100, 49.9),3)
    0.1
    """
    return abs((voltage / 2) - midpoint_voltage)


def calc_midpoint_shift_percent(voltage: float, midpoint_voltage: float) -> float:
    """
    Calculate the midpoint shift in percent.

    >>> calc_midpoint_shift_percent(100, 50)
    0.0
    >>> round(calc_midpoint_shift_percent(26.7, 13.2),3)
    0.89
    >>> calc_midpoint_shift_percent(100, 51)
    0.5
    >>> calc_midpoint_shift_percent(100, 49)
    0.5
    """
    try:
        return abs(voltage / ((midpoint_voltage * 2) - voltage) / 100)
    except ZeroDivisionError:
        return 0.0


class BatteryMonitorHandler(BaseHandler):
    VictronDeviceClass = BatteryMonitor
    # example_data = {
    #     'aux_mode': 'midpoint_voltage',
    #     'consumed_ah': 0.0,  # device class "electricity" Ah not supported by HASS - convert to "energy" Wh
    #     'current': 1.343,  # not existing in 'Smart Battery Sense'
    #     'midpoint_voltage': 13.03,
    #     'model_name': 'SmartShunt 500A/50mV',
    #     'remaining_mins': 65535,
    #     'soc': 100.0,
    #     'voltage': 26.22,
    #     'rssi': -70,
    # }

    def setup(self, *, data_dict):
        super().setup(data_dict=data_dict)

        self.sensors = {
            'aux_mode': Sensor(
                device=self.device,
                name='Auxiliary Mode',
                uid='aux_mode',
            ),
            # 'consumed_ah': Sensor(
            #    device=self.device,
            #    name='Consumed Ah',
            #    uid='consumed_ah',
            #    device_class='electricity',
            #    state_class='measurement',
            #    unit_of_measurement='Ah',
            #    suggested_display_precision=1,
            #),
            'current': Sensor(
                device=self.device,
                name='Current',
                uid='current',
                device_class='current',
                state_class='measurement',
                unit_of_measurement='A',
                suggested_display_precision=3,
            ),
            'midpoint_voltage': Sensor(
                device=self.device,
                name='Midpoint Voltage',
                uid='midpoint_voltage',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=2,
            ),
            'remaining_mins': Sensor(
                device=self.device,
                name='Remaining Minutes',
                uid='remaining_mins',
                state_class='measurement',
                unit_of_measurement='min',
            ),
            'soc': Sensor(
                device=self.device,
                name='State of Charge',
                uid='soc',
                device_class='battery',
                state_class='measurement',
                unit_of_measurement='%',
                suggested_display_precision=1,
            ),
            'voltage': Sensor(
                device=self.device,
                name='Voltage',
                uid='voltage',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=2,
            ),
            'temperature': Sensor(
                device=self.device,
                name='Temperature',
                uid='temperature',
                device_class='temperature',
                state_class='measurement',
                unit_of_measurement='°C',
                suggested_display_precision=1,
            ),
        }
        ####################################################################################
        # Extra sensors

        if data_dict.get('current'):
            self.power_sensor = Sensor(
                device=self.device,
                name='Power',
                uid='power',
                device_class='power',
                state_class='measurement',
                unit_of_measurement='W',
                suggested_display_precision=2,
            )

        if data_dict.get('consumed_ah'):
            self.consumed_wh = Sensor(
                device=self.device,
                name='Consumed Energy',
                uid='consumed_wh',
                device_class='energy',
                state_class='measurement',
                unit_of_measurement='Wh',
                suggested_display_precision=0,
            )

        if data_dict.get('aux_mode', None) == 'midpoint_voltage':
            self.midpoint_shift = Sensor(
                device=self.device,
                name='Midpoint Shift',
                uid='midpoint_shift',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=2,
            )
            self.midpoint_shift_percent = Sensor(
                device=self.device,
                name='Midpoint Shift',
                uid='midpoint_shift_percent',
                state_class='measurement',
                unit_of_measurement='%',
                suggested_display_precision=2,
            )

    def publish(self, *, data_dict: dict, rssi: int | None) -> None:
        super().publish(data_dict=data_dict, rssi=rssi)

        # Extra sensors

        if data_dict.get('consumed_ah'):
            self.consumed_wh.set_state(data_dict['voltage'] * data_dict['consumed_ah'])
            self.consumed_wh.publish(self.mqtt_client)

        if data_dict.get('current'):
            self.power_sensor.set_state(data_dict['voltage'] * data_dict['current'])
            self.power_sensor.publish(self.mqtt_client)

        if data_dict.get('aux_mode', None) == 'midpoint_voltage':
            midpoint_shift = calc_midpoint_shift(data_dict['voltage'], data_dict['midpoint_voltage'])
            self.midpoint_shift.set_state(midpoint_shift)
            self.midpoint_shift.publish(self.mqtt_client)

            midpoint_shift_percent = calc_midpoint_shift_percent(data_dict['voltage'], data_dict['midpoint_voltage'])
            self.midpoint_shift_percent.set_state(midpoint_shift_percent)
            self.midpoint_shift_percent.publish(self.mqtt_client)


class SolarChargerHandler(BaseHandler):
    VictronDeviceClass = SolarCharger
    # example_data = {
    #     'battery_charging_current': 0.8,
    #     'battery_voltage': 25.91,
    #     'charge_state': 'bulk',
    #     'charger_error': 'no_error',
    #     'external_device_load': 0.0,  # existence depending on victron device
    #     'model_name': 'SmartSolar MPPT 100|20 48V',
    #     'solar_power': 22,
    #     'yield_today': 330,
    #     'rssi': -80,
    # }

    def setup(self, *, data_dict):
        super().setup(data_dict=data_dict)

        self.sensors = {
            'battery_charging_current': Sensor(
                device=self.device,
                name='Battery Charging',
                uid='battery_charging_current',
                device_class='current',
                state_class='measurement',
                unit_of_measurement='A',
                suggested_display_precision=1,
            ),
            'battery_voltage': Sensor(
                device=self.device,
                name='Battery',
                uid='battery_voltage',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=2,
            ),
            'charge_state': Sensor(
                device=self.device,
                uid='charge_state',
                name='Charge State',
            ),
            'charger_error': Sensor(
                device=self.device,
                uid='charger_error',
                name='Charger Error',
            ),
            'solar_power': Sensor(
                device=self.device,
                name='Solar',
                uid='solar_power',
                device_class='energy',
                state_class='measurement',
                unit_of_measurement='W',
                suggested_display_precision=0,
            ),
            'yield_today': Sensor(
                device=self.device,
                name='Yield Today',
                uid='yield_today',
                device_class='energy',
                state_class='measurement',
                unit_of_measurement='Wh',
                suggested_display_precision=0,
            ),
        }

        ####################################################################################
        # Extra sensors

        if data_dict.get('external_device_load'):
            self.external_device_load = Sensor(
                device=self.device,
                name='Load',
                uid='load',
                device_class='current',
                state_class='measurement',
                unit_of_measurement='A',
                suggested_display_precision=1,
            )
        self.charging_power = Sensor(
            device=self.device,
            name='Charging Power',
            uid='charging_power',
            device_class='power',
            state_class='measurement',
            unit_of_measurement='W',
            suggested_display_precision=1,
        )
        self.load_power = Sensor(
            device=self.device,
            name='Load Power',
            uid='load_power',
            device_class='power',
            state_class='measurement',
            unit_of_measurement='W',
            suggested_display_precision=1,
        )

    def publish(self, *, data_dict: dict, rssi: int | None) -> None:
        super().publish(data_dict=data_dict, rssi=rssi)

        # Extra sensors

        self.charging_power.set_state(data_dict['battery_voltage'] * data_dict['battery_charging_current'])
        self.charging_power.publish(self.mqtt_client)

        if data_dict.get('external_device_load'):
            self.load_power.set_state(data_dict['battery_voltage'] * data_dict['external_device_load'])
            self.load_power.publish(self.mqtt_client)


class DcDcConverterHandler(BaseHandler):
    VictronDeviceClass = DcDcConverter
    # example_data = {
    #     'charge_state': 'off', 
    #     'charger_error': 'no_error',
    #     'input_voltage': 11.36,
    #     'model_name': 'Orion Smart 12V|12V-30A Non-isolated DC-DC Charger',
    #     'off_reason': 'engine_shutdown_and_input_voltage_lockout',
    #     'output_voltage': 0
    # }

    def setup(self, *, data_dict):
        super().setup(data_dict=data_dict)

        self.sensors = {
            'charge_state': Sensor(
                device=self.device,
                name='Charge State',
                uid='charge_state',
            ),
            'charger_error': Sensor(
                device=self.device,
                name='Charge Error',
                uid='charger_error',
            ),
            'input_voltage': Sensor(
                device=self.device,
                name='Input Voltage',
                uid='input_voltage',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=1,
            ),
            'output_voltage': Sensor(
                device=self.device,
                name='Output Voltage',
                uid='output_voltage',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=1,
            ),
            'off_reason': Sensor(
                device=self.device,
                name='Off Reason',
                uid='off_reason',
            ),
        }

    def publish(self, *, data_dict: dict, rssi: int | None) -> None:
        super().publish(data_dict=data_dict, rssi=rssi)


class SmartBatteryProtectHandler(BaseHandler):
    VictronDeviceClass = SmartBatteryProtect
    # example_data = {
    #     'alarm_reason': 'no_alarm',
    #     'device_state': 'active',
    #     'error_code': 'no_error',
    #     'input_voltage': 13.28,
    #     'model_name': 'Smart BatteryProtect 12/24V-100A',
    #     'off_reason': 'no_reason',
    #     'output_state': 'on',
    #     'output_voltage': 13.28,
    #     'warning_reason': 'no_alarm'
    # }

    def setup(self, *, data_dict):
        super().setup(data_dict=data_dict)

        self.sensors = {
            'alarm_reason': Sensor(
                device=self.device,
                name='Alarm Reason',
                uid='alarm_reason',
            ),
            'device_state': Sensor(
                device=self.device,
                name='Device State',
                uid='device_state',
            ),
            'error_code': Sensor(
                device=self.device,
                name='Error Code',
                uid='error_code',
            ),
            'input_voltage': Sensor(
                device=self.device,
                name='Input Voltage',
                uid='input_voltage',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=2,
            ),
            'off_reason': Sensor(
                device=self.device,
                name='Off Reason',
                uid='off_reason',
            ),
            'output_state': Sensor(
                device=self.device,
                name='Output State',
                uid='output_state',
            ),
            'output_voltage': Sensor(
                device=self.device,
                name='Output Voltage',
                uid='output_voltage',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=2,
            ),
            'warning_reason': Sensor(
                device=self.device,
                name='Warning Reason',
                uid='warning_reason',
            ),
        }

    def publish(self, *, data_dict: dict, rssi: int | None) -> None:
        super().publish(data_dict=data_dict, rssi=rssi)


class AcChargerHandler(BaseHandler):
    VictronDeviceClass = AcCharger
    # example_data = {
    #     'ac_current': -0.1,
    #     'output_current1': 1.0,
    #     'output_current2': -0.1,
    #     'output_current3': -0.1,
    #     'output_voltage1': 13.51,
    #     'output_voltage2': -0.01,
    #     'output_voltage3': -0.01,
    #     'charge_state': 'float',
    #     'charger_error': 'no_error',
    #     'model_name': 'Phoenix Smart IP43 Charger 12|30 (1+1)',
    #     'temperature': 8
    # }

    def setup(self, *, data_dict):
        super().setup(data_dict=data_dict)

        self.sensors = {
            'charge_state': Sensor(
                device=self.device,
                name='Charge State',
                uid='charge_state',
            ),
            'charger_error': Sensor(
                device=self.device,
                name='Charger Error',
                uid='charger_error',
            ),
            'ac_current': Sensor(
                device=self.device,
                name='AC Current',
                uid='ac_current',
                device_class='current',
                state_class='measurement',
                unit_of_measurement='A',
                suggested_display_precision=2,
            ),
            'output_current1': Sensor(
                device=self.device,
                name='Output Current 1',
                uid='output_current1',
                device_class='current',
                state_class='measurement',
                unit_of_measurement='A',
                suggested_display_precision=2,
            ),
            'output_current2': Sensor(
                device=self.device,
                name='Output Current 2',
                uid='output_current2',
                device_class='current',
                state_class='measurement',
                unit_of_measurement='A',
                suggested_display_precision=2,
            ),
            'output_current3': Sensor(
                device=self.device,
                name='Output Current 3',
                uid='output_current3',
                device_class='current',
                state_class='measurement',
                unit_of_measurement='A',
                suggested_display_precision=2,
            ),
            'output_voltage1': Sensor(
                device=self.device,
                name='Output Voltage 1',
                uid='output_voltage1',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=2,
            ),
            'output_voltage2': Sensor(
                device=self.device,
                name='Output Voltage 2',
                uid='output_voltage2',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=2,
            ),
            'output_voltage3': Sensor(
                device=self.device,
                name='Output Voltage 3',
                uid='output_voltage3',
                device_class='voltage',
                state_class='measurement',
                unit_of_measurement='V',
                suggested_display_precision=2,
            ),
            'temperature': Sensor(
                device=self.device,
                name='Temperature',
                uid='temperature',
                device_class='temperature',
                state_class='measurement',
                unit_of_measurement='°C',
                suggested_display_precision=1,
            ),
        }

        ####################################################################################
        # Extra sensors

        self.output_power1 = Sensor(
            device=self.device,
            name='Output Power 1',
            uid='output_power1',
            device_class='power',
            state_class='measurement',
            unit_of_measurement='W',
            suggested_display_precision=1,
        )
        self.output_power2 = Sensor(
            device=self.device,
            name='Output Power 2',
            uid='output_power2',
            device_class='power',
            state_class='measurement',
            unit_of_measurement='W',
            suggested_display_precision=1,
        )
        self.output_power3 = Sensor(
            device=self.device,
            name='Output Power 3',
            uid='output_power3',
            device_class='power',
            state_class='measurement',
            unit_of_measurement='W',
            suggested_display_precision=1,
        )


    def publish(self, *, data_dict: dict, rssi: int | None) -> None:
        super().publish(data_dict=data_dict, rssi=rssi)

        # Extra sensors
        self.output_power1.set_state(data_dict['output_voltage1'] * data_dict['output_current1'])
        self.output_power1.publish(self.mqtt_client)

        self.output_power2.set_state(data_dict['output_voltage2'] * data_dict['output_current2'])
        self.output_power2.publish(self.mqtt_client)

        self.output_power3.set_state(data_dict['output_voltage3'] * data_dict['output_current3'])
        self.output_power3.publish(self.mqtt_client)


class FallbackHandler(BaseHandler):
    VictronDeviceClass = None

    def setup(self, *, data_dict):
        super().setup(data_dict=data_dict)

        for key in data_dict.keys():
            if key == 'model_name':
                continue

            logger.warning('Setup fallback sensor for: %s', key)

            self.sensors[key] = Sensor(
                device=self.device,
                name=key.capitalize(),
                uid=key,
            )


VICRON_DEVICE_HANDLERS = (
    BatteryMonitorHandler,
    SmartBatteryProtectHandler,
    AcChargerHandler,
    SolarChargerHandler,
    DcDcConverterHandler,
)


def get_handler(*, victron_device: Device) -> type[BaseHandler]:
    for HandlerClass in VICRON_DEVICE_HANDLERS:
        if isinstance(victron_device, HandlerClass.VictronDeviceClass):
            logger.info('Handler for %s: %s', victron_device, HandlerClass.__name__)
            return HandlerClass

    logger.warning('Use fallback handler for %s', victron_device)
    return FallbackHandler


class VictronMqttDeviceHandler:
    def __init__(self, *, user_settings: UserSettings):
        self.user_settings = user_settings
        self.main_mqtt_device = MainMqttDevice(
            name=f'victron-ble2mqtt@{socket.gethostname()}',
            uid=user_settings.mqtt.main_uid,
            manufacturer='victron-ble2mqtt',
            sw_version=victron_ble2mqtt.__version__,
            config_throttle_sec=user_settings.mqtt.publish_config_throttle_seconds,
        )
        self.handler_map = {}

    def publish(
        self,
        *,
        ble_device: BLEDevice,
        raw_data: bytes,
        generic_device: GenericDevice,
        rssi: int | None,
        mqtt_client: Client,
    ) -> None:
        logger.debug('MQTT data from %s', ble_device.name)

        mac_address = ble_device.address
        try:
            handler = self.handler_map[mac_address]
        except KeyError:
            HandlerClass = get_handler(victron_device=generic_device.victron_device)
            handler = self.handler_map[mac_address] = HandlerClass(
                ble_device=ble_device,
                main_mqtt_device=self.main_mqtt_device,
                victron_device=generic_device.victron_device,
                mqtt_client=mqtt_client,
                user_settings=self.user_settings,
            )

        handler.publish(
            data_dict=generic_device.parse(raw_data=raw_data),
            rssi=rssi,
        )
