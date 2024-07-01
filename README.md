# DWD Global Radiation Home Assistant Integration
![GitHub release](https://img.shields.io/github/v/release/aschmere/dwd_global_rad_hass.svg)
![License](https://img.shields.io/github/license/aschmere/dwd_global_rad_hass.svg)
![Project State](https://img.shields.io/badge/project_state-beta-orange.svg)
![Maintained](https://img.shields.io/badge/maintained-yes-brightgreen.svg)

## Overview
The DWD Global Radiation Home Assistant Integration is a custom component that allows users to integrate global radiation data from the Deutscher Wetterdienst (DWD) into their Home Assistant setup. This integration provides real-time and forecast radiation data, enabling enhanced home automation based on weather conditions.

## Features
- **Measurements**: Access current global radiation measurements from DWD. Measurements are updated every 15 minutes.
- **Forecasts**: The data provides forecasts in 1-hour steps up to 17 hours into the future. Forecasts are updated hourly.
- **Configurable**: Easy setup and configuration through the Home Assistant UI.

## Installation
This integration requires the DWD Global Radiation API Server add-on to be installed. The add-on provides the necessary API services for the integration to work correctly, especially the functionality of the `netCDF4` Python package, which is essential for processing DWD data.

### Step 1: Register the Custom Repository with HACS
Before installing the integration, the repository must be registered as a custom repository in HACS. Follow these steps:

1. Open Home Assistant and go to HACS.
2. Click on the three dots in the top right corner and select "Custom repositories".
3. Add the URL `https://github.com/aschmere/dwd_global_rad_hass` to the "Add custom repository" field.
4. Choose the category as "Integration".
5. Click "Add".

### Step 2: Install the Integration via HACS
To install this repository using HACS, click the button below:

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=aschmere&repository=dwd_global_rad_hass)

### Step 3: Reboot Home Assistant
After installing the integration, reboot Home Assistant to apply the changes.

### Step 4: Add and Configure the Integration
Once Home Assistant has restarted, you can add and configure the `DWD Global Radiation` integration using the config flow. To do this, go to the Home Assistant UI and navigate to `Configuration` > `Integrations` > `Add Integration`, then search for `DWD Global Radiation Forecasts and Data`.

Alternatively, you can use the button below to start the configuration process directly:

[![Open your Home Assistant instance and start setting up this integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dwd_global_rad)



