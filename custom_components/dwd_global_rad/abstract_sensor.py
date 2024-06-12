"""Abstract sensor module for DWD Global Radiation integration in Home Assistant.

This module defines an abstract base class for global radiation sensors, providing
common functionality and attributes for derived sensor classes.

Classes:
    AbstractGlobalRadiationSensor -- Abstract base class for global radiation sensors.

Usage:
    This module should be used as a base for creating specific global radiation sensor
    classes. Derived classes must implement the `update_state` method to handle updates
    from the coordinator.

Constants:
    ATTR_ATTRIBUTION -- Attribution string for the sensor data.
    DOMAIN -- Domain for the integration.
    MANUFACTURER -- Manufacturer string for the device info.

Classes:
    AbstractGlobalRadiationSensor -- Provides a common interface and functionality
                                     for global radiation sensors.

Methods:
    __init__ -- Initialize the sensor with coordinator, name, and description.
    name -- Return the name of the sensor.
    extra_state_attributes -- Return the state attributes.
    available -- Return True if the entity is available.
    async_added_to_hass -- Connect to dispatcher listening for entity data notifications.
    _handle_coordinator_update -- Handle updated data from the coordinator.
    async_update -- Get the latest data and update the states.
    update_state -- Abstract method to update the state and attributes based on location data.

"""

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_ATTRIBUTION, DOMAIN, MANUFACTURER
from .coordinator import LocationDataUpdateCoordinator


class AbstractGlobalRadiationSensor(CoordinatorEntity, SensorEntity):
    """Abstract class for a global radiation sensor."""

    _attr_should_poll = False
    _attr_attribution = ATTR_ATTRIBUTION

    def __init__(
        self,
        coordinator: LocationDataUpdateCoordinator,
        name: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        unique_device_id = f"{name} - DWD Global Radiation"
        self._attr_name = f"{name} {description.key}"
        self._attr_unique_id = f"{name.lower().replace(' ', '_')}_{description.key.lower().replace(' ', '_')}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            # identifiers={(DOMAIN, f"{split_unique_id[0]}-{split_unique_id[1]}")},
            identifiers={(DOMAIN, unique_device_id)},
            manufacturer=MANUFACTURER,
            name=unique_device_id,
        )
        self._attr_native_value = None
        self._attributes: dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._attr_name or "Unknown"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return self._attributes

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        await super().async_added_to_hass()
        # Register the update listener
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if isinstance(self.coordinator, LocationDataUpdateCoordinator):
            self.hass.async_create_task(self._async_handle_coordinator_update())

    async def _async_handle_coordinator_update(self):
        """Handle updated data from the coordinator asynchronously."""
        location_data = await self.coordinator.get_location_data()
        self.update_state(location_data)
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Get the latest data and update the states."""
        await self.coordinator.async_request_refresh()

    def update_state(self, location_data):
        """Update the state and attributes based on location data."""
        raise NotImplementedError("Must be implemented by subclasses")
