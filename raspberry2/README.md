# Raspberry Pi 2 - IoT Data Aggregation and Visualization

This directory contains Python scripts for Raspberry Pi 2, which serves as the data aggregation and visualization component of the system. This Pi subscribes to MQTT topics (where data from all ESP32 nodes is published by the central Raspberry Pi 1 gateway), stores the data in InfluxDB, and provides visualization capabilities through Grafana. The system processes measurements from multiple ESP32-C3 modules (temperature, humidity, TVOC, CAQI, eCO2) and makes them available for monitoring and analysis.

## Structure
- `mqtt_to_influx.py` - This Python script subscribes to the MQTT broker where sensor data is sent by the Raspberry Pi 1(temperature, humidity, CAQI, TVOC, eCO2), parses and saves the data to an InfluxDB database. It authenticates using a username and password (prompted or loaded from .env).

Data format in InfluxDB:
Each data point is written using the InfluxDB line protocol, where:

The device ID is used as the measurement name.
The sensor type (temp, hum, tvoc, eCO2, caqi) is stored as a tag (type).
The sensor value is stored as a field (value).
The provided timestamp is used as the time.
- `read_from_db.py` - This Python script connects to the InfluxDB database, authenticates the user by asking for the database's password if it's not already found in the .env file, and allows the user to either export measurement data to text files or delete data from the database. The user can choose to operate on a specific measurement or all measurements, and can specify conditions for deletion (up to what time data will be erased). The script handles authentication, data querying, and deletion via HTTP requests to the InfluxDB server.
- `udp_receiver_test.py` - Test script for UDP communication (listens on port 8080)----
- `webserver/` - Web server utilities for data visualization:
  - `grafana/` - Configuration files for Grafana dashboards and data sources
  - `UI` - Simple test file for UI development
- `mqtt_mean_to_influx.py` - Subscribes to the MQTT topics where mean values are published by `udp_to_mqtt_mean.py` (e.g., `iot/team19/mean_value/temp`), and writes each mean value to InfluxDB. This script expects temp and hum as floats (2 decimals), and caqi, tvoc, eco2 as integers. Each value is stored as a separate measurement in InfluxDB, with the measurement name `mean_value` and the sensor type as a tag.

---

## Usage (Mean Value Pipeline)
1. Start the mean UDP to MQTT aggregator on Raspberry Pi 1:
   ```sh
   python3 ../raspberry1/udp_to_mqtt_mean.py
   ```
2. Start the mean MQTT to InfluxDB bridge on Raspberry Pi 2:
   ```sh
   python mqtt_mean_to_influx.py
   ```
   This will subscribe to all mean value topics and save incoming mean values to InfluxDB.

---

## Data Format (Mean Value)
- MQTT topics: `iot/team19/mean_value/<key>` (e.g., `temp`, `hum`, `caqi`, ...)
- Payload: mean value as float (for temp, hum) or int (for others)
- InfluxDB: measurement name `mean_value`, tag `type=<key>`, field `value=<mean>`

## Requirements
- Python 3.x
- Python packages:
  - `paho-mqtt` - For MQTT client functionality
  - `requests` - For HTTP communication with InfluxDB
- Optional: Grafana (for data visualization dashboards)

## Configuration
Both `mqtt_to_influx.py` and `read_from_db.py` will:
1. Look for credentials in a `.env` file in the parent directory
2. Prompt for credentials if not found, and save them to the `.env` file

## Usage
1. Start the MQTT to InfluxDB bridge:
   ```sh
   python mqtt_to_influx.py
   ```
   This will subscribe to the configured MQTT topics and save incoming data to InfluxDB.

2. To query data from the database:
   ```sh
   python read_from_db.py
   ```
   You will be prompted for the InfluxDB password if not already stored in the .env file.

3. To install Grafana for data visualization:
   ```sh
   cd webserver/grafana
   sudo bash install.sh
   ```
   Then access Grafana at http://<your_rpi_ip>:3000

## License
MIT