import logging
import time

import aiohttp

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the camera platform from a config entry."""
    async_add_entities([DWDGlobalRadCamera(hass, config_entry)])


class DWDGlobalRadCamera(Camera):
    """Representation of a DWD Global Radiation Forecast Camera."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the camera."""
        super().__init__()
        self._name = config_entry.data.get(
            "name", "DWD Global Radiation Forecast Camera"
        )
        self._unique_id = config_entry.data.get("unique_id")
        self.api_client = hass.data[DOMAIN]["api_client"]
        self.forecast_coordinator = hass.data[DOMAIN]["forecast_coordinator"]
        self._last_image = None
        self._attr_is_streaming = False
        self._config_entry = config_entry
        self._last_update_time = 0

        # Subscribe to forecast coordinator updates
        self.forecast_coordinator.async_add_listener(self._schedule_update)

    @property
    def name(self):
        """Return the name of the camera."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the camera."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this camera."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=self._name,
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_camera_image(self, width=None, height=None):
        """Return bytes of camera image."""
        _LOGGER.debug(
            "Returning camera image with width=%s and height=%s", width, height
        )
        return self._last_image

    @callback
    def _schedule_update(self):
        """Schedule an update for the camera image."""
        _LOGGER.debug("Scheduling update for forecast animation GIF.")
        self.hass.async_create_task(self.async_update())

    async def async_update(self):
        """Fetch new state data for the camera."""
        current_time = time.time()
        # Only update if the last update was more than 30 minutes ago
        if current_time - self._last_update_time < 1800:  # 30 minutes = 1800 seconds
            _LOGGER.debug("Skipping update, last update was less than 30 minutes ago.")
            return
        self._last_update_time = current_time
        _LOGGER.debug("Fetching new forecast animation GIF")
        try:
            image = await self.api_client.get_forecast_animated_gif()
            if image:
                self._last_image = image
                self._attr_is_streaming = True
            else:
                self._attr_is_streaming = False
        except aiohttp.ServerDisconnectedError as err:
            _LOGGER.error(
                "Server disconnected while fetching forecast animation GIF: %s",
                str(err),
            )
            self._attr_is_streaming = False
        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Client error while fetching forecast animation GIF: %s", str(err)
            )
            self._attr_is_streaming = False
        except Exception as err:
            _LOGGER.error(
                "Unexpected error while fetching forecast animation GIF: %s", str(err)
            )
            self._attr_is_streaming = False

        self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state."""
        return False
