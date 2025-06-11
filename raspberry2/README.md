# Raspberry Pi 2 - IoT Data Storage and Visualization

This directory contains Python scripts for Raspberry Pi 2, which serves as the data storage and visualization component of the system. This Pi subscribes to MQTT topics (where data from all ESP32 nodes is published by the central Raspberry Pi 1 gateway), stores the data in InfluxDB, and provides visualization capabilities through Grafana.

The system can operate in two modes corresponding to the mode Raspberry Pi 1 is running:
1. **Individual device mode**: Receiving individual measurements from multiple ESP32-C3 modules (temperature, humidity, TVOC, CAQI, eCO2) and storing each device's data separately.
2. **Mean values mode**: Receiving mean values calculated by Raspberry Pi 1 across all devices and storing these values.

Both individual device data and mean values are available for monitoring and analysis in Grafana.

## Structure
- `mqtt_to_influx.py` - This Python script subscribes to the MQTT topics where individual device data is sent by the Raspberry Pi 1 (`iot/team19/<device_id>`), parses and saves the data to an InfluxDB database. It authenticates using a username and password (prompted or loaded from .env).
- `mqtt_mean_to_influx.py` - This Python script subscribes to the MQTT topics where mean values are published by Raspberry Pi 1 (`iot/team19/mean_value/<key>`), and writes each value to InfluxDB as a measurement named `mean_value` with the sensor type as a tag.
- `manage_db.py` - This Python script connects to the InfluxDB database, authenticates the user by asking for the database's password if it's not already found in the .env file, and allows the user to either export measurement data to text files or delete data from the database. The user can choose to operate on a specific measurement or all measurements, and can specify conditions for deletion (up to what time data will be erased).
- `udp_receiver_test.py` - Test script for UDP communication (listens on port 8080)
- `webserver/` - Web server utilities for data visualization:
  - `grafana/` - Configuration files for Grafana dashboards and data sources
  - `UI` - Simple test file for UI development

---

## Data Format (Mean Values)
- MQTT topics: `iot/team19/mean_value/<key>` (e.g., `temp`, `hum`, `caqi`, ...)
- Payload: value as float (for temp, hum) or int (for others)
- InfluxDB: measurement name `mean_value`, tag `type=<key>`, field `value=<mean>`

## Configuration
Both `mqtt_to_influx.py` and `manage_db.py` will:
1. Look for credentials in a `.env` file in the parent directory
2. Prompt for credentials if not found, and save them to the `.env` file

## License
MIT