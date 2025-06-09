# Raspberry Pi 1 - Central UDP to MQTT Gateway

This directory contains Python scripts for the central gateway that collects sensor data from all ESP32 nodes and forwards it to an MQTT broker.

## Structure
- `udp_to_mqtt.py` - Main gateway script that receives UDP packets from ESP32s and publishes to MQTT
- `test-mqtt-publish/` - MQTT publish example for testing
- `udp_sender_test.py` - Test script for sending UDP packets
- `test_tcp.py` - TCP & UDP communication test script
- `udp_to_mqtt_mean.py` - Aggregates all received UDP sensor data (from all ESP32s) over a configurable interval, computes the mean for each measurement (temp, hum as float with 2 decimals, others as int), and publishes each mean value to its own MQTT topic (e.g., `iot/team19/mean_value/temp`).

# UDP to MQTT Gateway for ESP32 Sensor Nodes

This directory contains scripts and configurations for bridging sensor data from multiple ESP32 devices (sent via UDP) to an MQTT broker, and onward to an InfluxDB database for storage. The setup is designed for use on a Raspberry Pi or similar Linux system.

## Overview

- **ESP32 devices** send sensor data as JSON via UDP to a gateway (Raspberry Pi).
- The **gateway** collects the latest reading from each ESP32 and publishes all readings together as a single MQTT message every few seconds.
- A separate script on another machine (or the same one) subscribes to the MQTT topic and writes the data to InfluxDB.

This approach is scalable, efficient, and integrated with our InfluxDB and Grafana data visualization pipeline.

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

### udp_to_mqtt_mean.py
- **Purpose:** Receives UDP packets from ESP32 sensor nodes, aggregates the sensor data over a configurable interval, computes the mean for each measurement, and publishes each mean value to its own MQTT topic.
- **How it works:**
  - Listens on UDP port 8080 (configurable).
  - Expects each UDP packet to be a JSON string with an `id` field and sensor values (`temp`, `hum`, `caqi`, `tvoc`, `eco2`).
  - Aggregates values for each measurement from all received packets.
  - Every 20 seconds (configurable), publishes the mean value of each measurement to its respective MQTT topic (e.g., `iot/team19/mean_value/temp`).
- **Configuration:** All settings (UDP port, MQTT broker, topic, publish interval, etc.) are at the top of the script.
- **Usage:**
  ```sh
  python3 udp_to_mqtt_mean.py
  ```
  You will be prompted for the MQTT password.

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
4. **Downstream scripts** (`mqtt_to_influx.py` on raspberry2) subscribe to `iot/team19` and write the data to our InfluxDB database.

---

## Data Flow Example (Mean Aggregation)

1. **ESP32** sends UDP packet:
   ```json
   {"id": "AABBCC", "temp": 23.4, "hum": 56.7, "caqi": 2, "tvoc": 123, "eco2": 456}
   ```
2. **udp_to_mqtt_mean.py** receives packets from all devices, aggregates values for each measurement, and every 20 seconds publishes:
   - `iot/team19/mean_value/temp`: `23.45` (float, 2 decimals)
   - `iot/team19/mean_value/hum`: `56.70` (float, 2 decimals)
   - `iot/team19/mean_value/caqi`: `2` (int)
   - ...

---

## Integration with InfluxDB

See the `raspberry2/` directory for scripts like `mqtt_to_influx.py`, which subscribe to the MQTT topic and write sensor data to our InfluxDB database for storage and visualization with our Grafana installation.

See also `mqtt_mean_to_influx.py`, which subscribes to the mean value MQTT topics and writes each mean value to InfluxDB for storage and visualization.

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