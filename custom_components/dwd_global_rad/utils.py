"""Utility functions for the Home Assistant global radiation measurement integration.

This module includes helper functions to handle time conversions required for the integration.

Functions:
    convert_to_local: Convert a timestamp to the local Home Assistant time zone.

Dependencies:
    - homeassistant.util.dt: Provides date and time utility functions for Home Assistant.
"""

import logging

from homeassistant.util.dt import as_local, utc_from_timestamp


def convert_to_local(timestamp):
    """Convert a timestamp to the local Home Assistant time zone."""
    # Convert timestamp to a UTC datetime object
    utc_dt = utc_from_timestamp(timestamp)
    # Return local datetime object
    return as_local(utc_dt)


def setup_logger(name, level=logging.DEBUG, log_file=None):
    """Set up logger with the specified name and level."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add formatter to ch
    ch.setFormatter(formatter)

    # Add ch to logger
    logger.addHandler(ch)

    # Optional: Add file handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
