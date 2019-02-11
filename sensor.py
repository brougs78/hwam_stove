"""
Support for HWAM Stove sensors.

For more details about this platform, please refer to the documentation at
http://home-assistant.io/components/sensor.hwam_stove/
"""
import logging

from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.const import DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity, async_generate_entity_id

from custom_components.hwam_stove import DATA_HWAM_STOVE, DATA_PYSTOVE

DEPENDENCIES = ['hwam_stove']

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the HWAM Stove sensors."""
    if discovery_info is None:
        return
    pystove = hass.data[DATA_HWAM_STOVE][DATA_PYSTOVE]
    sensor_info = {
        # {name: [device_class, unit, friendly_name format]}
        pystove.DATA_STOVE_TEMPERATURE: [
            DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS, "Stove Temperature {}"],
        pystove.DATA_ROOM_TEMPERATURE: [
            DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS, "Room Temperature {}"],
    }
    stove_device = discovery_info[0]
    sensor_list = discovery_info[1]
    sensors = []
    for var in sensor_list:
        device_class = sensor_info[var][0]
        unit = sensor_info[var][1]
        name_format = sensor_info[var][2]
        entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, name_format.format(stove_device.name),
            hass=hass)
        sensors.append(
            HwamStoveSensor(entity_id, stove_device, var, device_class, unit,
                            name_format))
    async_add_entities(sensors)


class HwamStoveSensor(Entity):
    """Representation of a HWAM Stove sensor."""

    def __init__(self, entity_id, stove_device, var, device_class, unit,
                 name_format):
        """Initialize the sensor."""
        self._stove_device = stove_device
        self.entity_id = entity_id
        self._var = var
        self._value = None
        self._device_class = device_class
        self._unit = unit
        self._name_format = name_format
        self._friendly_name = name_format.format(stove_device.name)

    async def async_added_to_hass(self):
        """Subscribe to updates from the component."""
        _LOGGER.debug("Added HWAM Stove sensor %s", self.entity_id)
        async_dispatcher_connect(self.hass, self._stove_device.signal,
                                 self.receive_report)

    async def receive_report(self, status):
        """Handle status updates from the component."""
        self._friendly_name = self._name_format.format(
            self._stove_device.stove.name)
        value = status.get(self._var)
        if isinstance(value, float):
            value = '{:2.1f}'.format(value)
        self._value = value
        self.async_schedule_update_ha_state()

    @property
    def name(self):
        """Return the friendly name of the sensor."""
        return self._friendly_name

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    @property
    def state(self):
        """Return the state of the device."""
        return self._value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def should_poll(self):
        """Return False because entity pushes its state."""
        return False
