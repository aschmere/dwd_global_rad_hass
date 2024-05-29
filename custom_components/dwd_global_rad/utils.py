"""Utility functions for the Home Assistant global radiation measurement integration.

This module includes helper functions to handle time conversions required for the integration.

Functions:
    convert_to_local: Convert a timestamp to the local Home Assistant time zone.

Dependencies:
    - homeassistant.util.dt: Provides date and time utility functions for Home Assistant.
"""

from homeassistant.util.dt import as_local, utc_from_timestamp


def convert_to_local(timestamp):
    """Convert a timestamp to the local Home Assistant time zone."""
    # Convert timestamp to a UTC datetime object
    utc_dt = utc_from_timestamp(timestamp)
    # Return local datetime object
    return as_local(utc_dt)
