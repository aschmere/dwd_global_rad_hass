import json

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import now as dt_now

# Import the DOMAIN constant from the __init__.py file in the same directory
from . import DOMAIN


class DWDGlobalRadRESTApi(HomeAssistantView):
    url = "/api/dwd_global_rad/forecasts/{location_name}/{hours}h"
    name = "api:dwd_global_rad_forecasts"  # Unique name for this view
    requires_auth = True

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    async def get(self, request, location_name, hours):
        """Handle GET requests."""
        # Validate and process the inputs
        if not hours.isdigit() or not (1 <= int(hours) <= 99):
            return self.json({"error": "Invalid hours format"}, status_code=400)

        hours = int(hours)
        api_client = self.hass.data[DOMAIN].get("api_client")

        if api_client is None:
            return self.json({"error": "API client not initialized"}, status_code=500)

        try:
            # location_name is automatically URL-decoded by HomeAssistantView

            forecast = await api_client.get_forecast_for_future_hour(
                location_name, hours
            )
        except KeyError:
            return self.json({"error": "Location not found"}, status_code=404)
        except ValueError as e:
            return self.json({"error": f"Value error: {e}"}, status_code=400)
        except (
            api_client.ApiError
        ) as e:  # Assuming api_client.ApiError is a specific exception
            return self.json({"error": f"API error: {e}"}, status_code=500)
        except (TypeError, AttributeError) as e:
            # Catching specific common exceptions that might still occur
            return self.json({"error": f"Unexpected error: {e}"}, status_code=500)

        return self.json(
            {"location_name": location_name, "hours": hours, "forecast": forecast}
        )
