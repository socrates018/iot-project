# MQTT Publisher

This script generates random temperature and humidity values and publishes them to MQTT topics. Useful for simulating IoT sensor data.

## Setup
1. Install dependencies:
   ```bash
   pip install paho-mqtt
   ```

## Usage
Run the script:
```bash
python project.py
```

## Notes
- Edit connection settings in `project.py` if needed.
- Publishes to topics like `iot/<hostname>/airTemperature` and `iot/<hostname>/airHumidity` every 5 seconds by default.
