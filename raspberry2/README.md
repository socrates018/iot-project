# raspberry2

This directory contains Python scripts for Raspberry Pi, focusing on MQTT to InfluxDB integration and database reading utilities.

## Structure
- `mqtt_to_influx.py` - Publishes MQTT data to InfluxDB
- `read_from_db.py` - Reads and exports data from the InfluxDB database. Prompts for password and measurement/topic to export.
- `webserver/` - (Optional) Web server utilities for data visualization or API endpoints.

## Requirements
- Python 3.x
- `requests` and `influxdb` client libraries (see script headers for details)

## Usage
1. Edit the scripts as needed for your environment.
2. Run with Python 3:
   ```sh
   python mqtt_to_influx.py
   python read_from_db.py
   ```
3. For `read_from_db.py`, you will be prompted for the InfluxDB password and which measurement/topic to export.

## License
MIT