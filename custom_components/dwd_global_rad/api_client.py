import logging
import traceback

import aiohttp

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class DWDGlobalRadAPIClient:
    def __init__(self, hass: HomeAssistant, hostname: str, port_number: int):
        self.hass = hass
        self.hostname = hostname
        self.port_number = port_number
        self.session = aiohttp.ClientSession()
        self._locations = None
        self.base_url = f"http://{self.hostname}:{self.port_number}"
        self.debug_mode = _LOGGER.isEnabledFor(logging.DEBUG)
        self.tracing_enabled = False  # Separate flag for tracing

    @property
    async def locations(self):
        self._log_debug_info("Fetching locations property")
        if self._locations is None:
            await self.fetch_locations()
        return self._locations

    async def fetch_locations(self):
        self._log_debug_info("Fetching locations")
        url = f"{self.base_url}/locations"
        async with self.session.get(url) as response:
            if response.status == 200:
                self._locations = await response.json()
            else:
                self._locations = []
        return self._locations

    async def get_location_by_name(self, name: str):
        self._log_debug_info(f"Fetching location by name: {name}")
        url = f"{self.base_url}/locations/{name}"
        async with self.session.get(url) as response:
            data = await response.json()
            if response.status != 200 or "error" in data:
                return None
            return data

    async def add_location(self, name: str, latitude: float, longitude: float):
        self._log_debug_info(f"Adding location: {name}")
        url = f"{self.base_url}/locations"
        data = {"name": name, "latitude": latitude, "longitude": longitude}
        async with self.session.post(url, json=data) as response:
            return await response.json()

    async def fetch_forecasts(self):
        self._log_debug_info("Fetching forecasts")
        url = f"{self.base_url}/forecasts"
        async with self.session.get(url) as response:
            return await response.json()

    async def fetch_measurements(self, hours: int = 3):
        self._log_debug_info(f"Fetching measurements for {hours} hours")
        url = f"{self.base_url}/measurements?hours={hours}"
        async with self.session.get(url) as response:
            return await response.json()

    async def remove_location(self, name: str):
        self._log_debug_info(f"Removing location: {name}")
        url = f"{self.base_url}/locations/{name}"
        async with self.session.delete(url) as response:
            return await response.json()

    async def get_forecast_animated_gif(self):
        self._log_debug_info("Fetching forecast animated GIF")
        url = f"{self.base_url}/process"
        async with self.session.post(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                return None

    async def get_status(self):
        self._log_debug_info("Checking API server status")
        url = f"{self.base_url}/status"
        async with self.session.get(url) as response:
            if response.status == 204:
                return True
            else:
                return False
    
    async def get_forecast_for_future_hour(self, location_name: str, number_of_hours: int):
        self._log_debug_info(f"Fetching forecast for location: {location_name}, hours: {number_of_hours}")
        url = f"{self.base_url}/locations/{location_name}/forecast/{number_of_hours}h"
        async with self.session.get(url) as response:
            return await response.json()

    async def close(self):
        self._log_debug_info("Closing session")
        await self.session.close()

    def _log_debug_info(self, message: str):
        _LOGGER.debug(message)
        if self.debug_mode and self.tracing_enabled:
            _LOGGER.debug("Call stack:")
            stack = traceback.format_stack()
            for line in stack:
                _LOGGER.debug(line.strip())
