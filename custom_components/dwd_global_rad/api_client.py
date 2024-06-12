import logging

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

    @property
    async def locations(self):
        if self._locations is None:
            await self.fetch_locations()
        return self._locations

    async def fetch_locations(self):
        url = f"{self.base_url}/locations"
        async with self.session.get(url) as response:
            if response.status == 200:
                self._locations = await response.json()
            else:
                self._locations = []
        return self._locations

    async def get_location_by_name(self, name: str):
        url = f"{self.base_url}/locations/{name}"
        async with self.session.get(url) as response:
            data = await response.json()
            if response.status != 200 or "error" in data:
                return None
            return data

    async def add_location(self, name: str, latitude: float, longitude: float):
        url = f"{self.base_url}/locations"
        data = {"name": name, "latitude": latitude, "longitude": longitude}
        async with self.session.post(url, json=data) as response:
            return await response.json()

    async def fetch_forecasts(self):
        url = f"{self.base_url}/forecasts"
        async with self.session.get(url) as response:
            return await response.json()

    async def fetch_measurements(self, hours: int = 3):
        url = f"{self.base_url}/measurements?hours={hours}"
        async with self.session.get(url) as response:
            return await response.json()

    async def close(self):
        await self.session.close()
