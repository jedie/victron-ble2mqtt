import dataclasses


@dataclasses.dataclass
class HaValueInfo:
    name: str
    device_class: str | None  # e.g.: "voltage" / "current" / "energy" etc.
    state_class: str | None  # e.g.: "measurement" / "total" / "total_increasing" etc.
    unit: str | None  # e.g.: "V" / "A" / "kWh" etc.


VICTRON_VALUES = {
    'battery_charging_current': HaValueInfo(
        name='Battery Charging',
        device_class='current',
        state_class='measurement',
        unit='A',
    ),
    'battery_voltage': HaValueInfo(
        name='Battery',
        device_class='voltage',
        state_class='measurement',
        unit='V',
    ),
    'charge_state': HaValueInfo(
        name='Charge State',
        device_class=None,
        state_class=None,
        unit=None,
    ),
    'external_device_load': HaValueInfo(
        name='Load',
        device_class='current',
        state_class='measurement',
        unit='A',
    ),
    'model_name': HaValueInfo(
        name='Model Name',
        device_class=None,
        state_class=None,
        unit=None,
    ),
    'solar_power': HaValueInfo(
        name='Solar',
        device_class='power',
        state_class='measurement',
        unit='W',
    ),
    'yield_today': HaValueInfo(
        name='Yield Today',
        device_class='energy',
        state_class='measurement',
        unit='Wh',
    ),
}
