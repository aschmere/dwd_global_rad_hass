# DWD Global Radiation Home Assistant Integration
![GitHub release](https://img.shields.io/github/v/release/aschmere/dwd_global_rad_hass.svg)
![License](https://img.shields.io/github/license/aschmere/dwd_global_rad_hass.svg)
![Project State](https://img.shields.io/badge/project_state-beta-orange.svg)
![Maintained](https://img.shields.io/badge/maintained-yes-brightgreen.svg)
## Overview
The DWD Global Radiation Home Assistant Integration is a custom component that allows users to integrate global radiation data from the Deutscher Wetterdienst (DWD) into their Home Assistant setup. This integration provides real-time and historical radiation data, enabling enhanced home automation based on weather conditions.

## Features
- **Real-Time Data**: Access current global radiation data from DWD.
- **Historical Data**: Retrieve historical radiation data for analysis and trends.
- **Configurable**: Easy setup and configuration through the Home Assistant UI.

## Documentation Status
Please note that this documentation is currently in a very early draft state and is actively being worked on. More detailed instructions and examples will be added soon.

## Installation

### Important Note on NetCDF Compatibility
NetCDF is a core part of this integration and needs to be installed for the integration to function. However, there is a known incompatibility with the Home Assistant image. For details on this issue, please refer to this [Home Assistant feature request](https://community.home-assistant.io/t/add-compatibility-with-netcdf4-python-package-to-home-assistance-core/734741).

### NetCDF Installation Workaround

#### Background
Home Assistant currently does not support the automatic installation of the Python NetCDF package as a requirement for an Integration. Home Assistant usually tries to install required packages of an Integration as specified in the integration's `manifest.json` file, but in the case of the NetCDF package, it fails currently (status: Home Assistant Core 2024.05.x and Home Assistant OS 12.3 and older). Although the following procedure was tested, u**se at your own risk, as installing your own python packages in the Home Assistant docker container is not considered as a typical end user scenario.

#### Prerequisite
Before applying this workaround, ensure you have an SSH add-on installed with the capability to disable "Protection Mode." One such add-on is available at [SSH & Web Terminal](https://github.com/hassio-addons/addon-ssh).

#### Step-by-Step Guide to Install netCDF4 and cftime in Home Assistant Docker Container

1. **Access your Home Assistant instance via SSH and disabled "Protection Mode".**
2. **Access the Home Assistant Container**:
   Use the following command to access the Home Assistant Docker container:
   ```sh
   docker exec -it homeassistant /bin/bash
   ```
3. **Update Package List and Install Dependencies**:
    Update the package list and install the necessary development tools and libraries:

    ```sh
    apk update
    apk add --no-cache netcdf-dev hdf5 hdf5-dev gcc g++ python3-dev musl-dev libffi-dev
    ```
4. **Set Environment Variables:**
    ```sh
    export CFLAGS="-I/usr/include"
    export LDFLAGS="-L/usr/lib"
    export CPPFLAGS="-I/usr/include"
    export HDF5_DIR="/usr"
    export NETCDF4_DIR="/usr"
    ```
5. **Install wheel and Cython:**
    ```sh
    pip install wheel cython
    ```
6. **Install netCDF4 and cftime:**
    ```sh
    pip install netCDF4 cftime --no-build-isolation
    ```
7. **Verify Installation:**
    ```sh
    pip list | grep netCDF4
    pip list | grep cftime
    ```
### Installation of the DWD Global Radiation Home Assistant Integration
#### Step 1: Install the Integration via HACS
To install this repository using HACS, click the button below:

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=aschmere&repository=dwd_global_rad_hass)
#### Step 2: Reboot Home Assistant
After installing the integration, reboot Home Assistant to apply the changes.
#### Step 3: Add and Configure the Integration
Once Home Assistant has restarted, you can add and configure the `DWD Global Radiation` integration using the config flow. To do this, go to the Home Assistant UI and navigate to `Configuration` > `Integrations` > `Add Integration`, then search for `DWD Global Radiation Forecasts and Data`.

Alternatively, you can use the button below to start the configuration process directly:

[![Open your Home Assistant instance and start setting up this integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dwd_global_rad)

