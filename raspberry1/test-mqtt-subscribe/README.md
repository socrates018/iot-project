# MQTT Subscriber

This script listens to MQTT topics and saves incoming messages to an InfluxDB database. It is useful for collecting IoT sensor data.

## Setup
1. Install dependencies:
   ```bash
   pip install paho-mqtt requests python-dotenv
   ```
2. Create a `.env` file with:
   ```
   MQTT_PASSWORD=your_mqtt_password
   ```

## Usage
Run the script:
```bash
python subscriber.py
```

## Notes
- Edit connection settings in `subscriber.py` if needed.
- Requires network access to the MQTT broker and InfluxDB.
