# raspberry1

This directory contains Python projects and examples for Raspberry Pi, focusing on MQTT, simple apps, and project templates.

## Structure
- `class_examples/` - Educational Python scripts and exercises
- `simple-app/` - Example simple application
- `project/` - Project template or main project code
- `test-mqtt-publish/` - MQTT publish example
- `test-mqtt-subscribe/` - MQTT subscribe example

# UDP to MQTT Gateway for ESP32 Sensor Nodes

This directory contains scripts and configuration for bridging sensor data from multiple ESP32 devices (sent via UDP) to an MQTT broker, and onward to an InfluxDB database for storage and visualization. The setup is designed for use on a Raspberry Pi or similar Linux system.

## Overview

- **ESP32 devices** send sensor data as JSON via UDP to a gateway (Raspberry Pi).
- The **gateway** collects the latest reading from each ESP32 and publishes all readings together as a single MQTT message every few seconds.
- A separate script on another machine (or the same one) subscribes to the MQTT topic and writes the data to InfluxDB.

This approach is scalable, efficient, and easy to integrate with data pipelines (e.g., InfluxDB, Grafana).

---

## File Descriptions

### udp_to_mqtt.py
- **Purpose:** Listens for UDP packets from ESP32 sensor nodes, collects the latest reading from each device, and publishes all readings as a single JSON array to an MQTT topic at regular intervals.
- **How it works:**
  - Listens on UDP port 8080 (configurable).
  - Expects each UDP packet to be a JSON string with an `id` field (unique per ESP32, e.g., last 3 bytes of MAC address) and sensor values (`temp`, `hum`, `caqi`, `tvoc`, `eco2`, `timestamp`).
  - Stores the latest reading for each device in a dictionary.
  - Every 2 seconds (configurable), publishes a single MQTT message to the topic `iot/team19` containing a JSON array of all latest readings.
- **Configuration:** All settings (UDP port, MQTT broker, topic, publish interval, etc.) are at the top of the script.
- **Usage:**
  ```sh
  python3 udp_to_mqtt.py
  ```
  You will be prompted for the MQTT password.

### config.json
- **Purpose:** (If present) Can be used to store configuration parameters for the gateway or other scripts. Not used by default in `udp_to_mqtt.py`.

### udp_listener_example.py
- **Purpose:** Example script for listening to UDP packets. Useful for debugging or testing ESP32 UDP output without MQTT or InfluxDB.
- **Usage:**
  ```sh
  python3 udp_listener_example.py
  ```

### class_examples/
- **Purpose:** Contains example Python scripts for educational or testing purposes. Not directly related to the UDP-to-MQTT gateway.
- **Notable files:**
  - `Exercise1.py`: Example exercise script.
  - `simple-app/`, `project/`, `test-mqtt-publish/`, `test-mqtt-subscribe/`: Example projects and MQTT test scripts.

---

## Data Flow Example

1. **ESP32** sends UDP packet:
   ```json
   {"id": "AABBCC", "temp": 23.4, "hum": 56.7, "caqi": 2, "tvoc": 123, "eco2": 456, "timestamp": "2025-05-28T12:34:56Z"}
   ```
2. **udp_to_mqtt.py** receives the packet, updates the latest reading for `AABBCC`.
3. Every 2 seconds, **udp_to_mqtt.py** publishes:
   ```json
   [
     {"id": "AABBCC", "temp": 23.4, ...},
     {"id": "DDEEFF", "temp": 24.1, ...},
     ...
   ]
   ```
   to MQTT topic `iot/team19`.
4. **Downstream scripts** (e.g., `mqtt_to_influx.py` on raspberry2) subscribe to `iot/team19` and write the data to InfluxDB.

---

## Integration with InfluxDB

See the `raspberry2/` directory for scripts like `mqtt_to_influx.py` and `mqtt_to_influx_updated.py`, which subscribe to the MQTT topic and write sensor data to an InfluxDB database for storage and visualization (e.g., with Grafana).

---

## Requirements
- Python 3.x
- `paho-mqtt` Python package (install with `pip install paho-mqtt`)

---

## Troubleshooting
- Make sure your firewall allows UDP traffic on the specified port (default: 8080).
- Ensure the MQTT broker address and credentials are correct.
- If you see import errors for `paho.mqtt.client`, install the package with `pip install paho-mqtt`.

---

## Contact
For questions or issues, contact the project maintainer or open an issue in the repository.

## License
MIT