"""Set up the global radiation measurement sensor integration for Home Assistant.

Defines the sensor types and handles the setup of sensors from a config entry. The module includes
the implementation of the `GlobalRadiationMeasurementSensor` class, which represents a sensor for
measuring global radiation and handles the update of its state and attributes based on location data.

Classes:
    GlobalRadiationMeasurementSensor: Represents a global radiation measurement sensor.

Functions:
    async_setup_entry: Sets up sensors from a config entry.

Constants:
    GLOBALRAD_MEASUREMENT_SENSOR_TYPES: Descriptions of the global radiation measurement sensors.

Dependencies:
    - homeassistant.components.sensor: Provides sensor-related classes and constants.
    - homeassistant.config_entries: Handles configuration entries for Home Assistant integrations.
    - homeassistant.const: Provides Home Assistant constants.
    - homeassistant.core: Core functionality of Home Assistant.
    - homeassistant.helpers.entity_platform: Entity platform helper functions.
    - .abstract_sensor: Abstract base class for global radiation sensors.
    - .const: Module constants.
    - .utils: Utility functions for data conversion.
"""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfIrradiance
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import UpdateFailed

from .abstract_sensor import AbstractGlobalRadiationSensor
from .const import ATTR_API_GLOBAL_RADIATION_MEASUREMENT, DOMAIN
from .utils import convert_to_local

_LOGGER = logging.getLogger(__name__)

GLOBALRAD_MEASUREMENT_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=ATTR_API_GLOBAL_RADIATION_MEASUREMENT,
        name="DWD Global Radiation Measurement",
        native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    name = entry.data["name"]
    location_coordinator = hass.data[DOMAIN][entry.entry_id]["location_coordinator"]

    entities: list[AbstractGlobalRadiationSensor] = [
        GlobalRadiationMeasurementSensor(location_coordinator, name, description)
        for description in GLOBALRAD_MEASUREMENT_SENSOR_TYPES
    ]

    async_add_entities(entities, update_before_add=True)


class GlobalRadiationMeasurementSensor(AbstractGlobalRadiationSensor):
    """Representation of a global radiation measurement sensor."""

    def update_state(self, location_data):
        """Update the state and attributes based on location data."""
        if location_data:
            self._attr_native_value = location_data["measurements"][
                "measurement_values"
            ][0]["sis"]
            # Prepare forecasts data for presentation
            forecasts = location_data["forecasts"]
            forecast_entries = [
                {
                    "datetime": convert_to_local(entry["timestamp"]),
                    **{
                        key: round(value) if key == "sis" else value
                        for key, value in entry.items()
                        if key != "timestamp"
                    },
                }
                for entry in forecasts["entries"]
            ]
            forecast_presentation = {
                "issuance_time": convert_to_local(forecasts["issuance_time"]),
                "grid_latitude": forecasts["grid_latitude"],
                "grid_longitude": forecasts["grid_longitude"],
                "distance_in_km": forecasts["distance"],
                "units": forecasts["metadata"].get("units"),
                "entries": forecast_entries,
                "metadata": {
                    key: value
                    for key, value in forecasts["metadata"].items()
                    if key != "units"
                },
            }

            # Prepare measurements data for presentation
            measurements = location_data["measurements"]
            measurement_values = [
                {
                    "datetime": convert_to_local(entry["timestamp"]),
                    **{
                        key: value for key, value in entry.items() if key != "timestamp"
                    },
                }
                for entry in measurements["measurement_values"]
            ]
            measurement_presentation = {
                "grid_latitude": measurements["grid_latitude"],
                "grid_longitude": measurements["grid_longitude"],
                "distance_in_km": measurements["distance"],
                "measurement_values": measurement_values,
            }

            # Update attributes without altering the internal structure
            self._attributes = {
                "forecasts": forecast_presentation,
                "measurements": measurement_presentation,
            }
        else:
            self._attr_native_value = None  # Mark the sensor as unavailable
            self._attributes = {}
            self._attr_available = False

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            await super().async_update()
            location_data = await self.coordinator.get_location_data()
            self.update_state(location_data)
        except UpdateFailed as err:
            if "Server disconnected" in str(err):
                _LOGGER.error(
                    "Server disconnected while fetching location data: %s", err
                )
            else:
                _LOGGER.error("Unexpected error fetching location data: %s", err)
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            self.async_write_ha_state()

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success
