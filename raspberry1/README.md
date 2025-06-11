# Raspberry Pi 1 - Central UDP to MQTT Gateway

This directory contains Python scripts for the central gateway that collects sensor data from all ESP32 nodes and forwards it to an MQTT broker.

## Structure
- `udp_to_mqtt.py` - Main gateway script that receives UDP packets from ESP32s and publishes each device's data to its own MQTT topic
- `udp_to_mqtt_mean.py` - Alternative gateway script that aggregates UDP sensor data from all ESP32s over 60 seconds, computes the mean for each measurement, and publishes each mean value to its own MQTT topic
- `test-mqtt-publish/` - MQTT publish example for testing
- `udp_sender_test.py` - Test script for sending UDP packets
- `test_tcp.py` - TCP & UDP communication test script
- `test-mqtt-concept3/` - Script based on concept 3 that subscribes to an MQTT topic and inserts the data to the influx DB (legacy).
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
  - Every 10 seconds (configurable), publishes distinct MQTT messages for each ESP (identified by <mac-id>) to the topic `iot/team19/<mac-id>` containing a JSON array of all latest readings.
- **Configuration:** All settings (UDP port, MQTT broker, topic, publish interval, etc.) are at the top of the script.

### config.json
- **Purpose:** (If present) Can be used to store configuration parameters for the gateway or other scripts. Not used by default in `udp_to_mqtt.py`.

### udp_to_mqtt_mean.py
- **Purpose:** Receives UDP packets from ESP32 sensor nodes, aggregates the sensor data over a configurable interval, computes the mean for each measurement, and publishes each mean value to its own MQTT topic.
- **How it works:**
  - Listens on UDP port 8080 (configurable).
  - Expects each UDP packet to be a JSON string with an `id` field and sensor values (`temp`, `hum`, `caqi`, `tvoc`, `eco2`).
  - Aggregates values for each measurement from all received packets.
  - Every 60 seconds (configurable), publishes the mean value of each measurement to its respective MQTT topic (e.g., `iot/team19/mean_value/temp`).
- **Configuration:** All settings (UDP port, MQTT broker, topic, publish interval, etc.) are at the top of the script.

---

## Data Flow Example

1. **ESP32** sends UDP packet:
   ```json
   {"temp": 23.4, "hum": 56.7, "caqi": 2, "tvoc": 123, "eco2": 456}
   ```
2. **udp_to_mqtt.py** receives the packet, updates the latest reading for `AABBCC`.
   - Adds timestamp: `"timestamp": 1715802896000000000` (nanoseconds since epoch)
3. Every 10 seconds, **udp_to_mqtt.py** publishes:
   ```json
   {"temp": 23.4, "hum": 56.7, "caqi": 2, "tvoc": 123, "eco2": 456, "timestamp": 1715802896000000000}
   ```
   to distinct (for each esp) MQTT topic `iot/team19/<mac-id>`.   
4. **Downstream scripts** (`mqtt_to_influx.py` on raspberry2) subscribe to `iot/team19` and write the data to our InfluxDB database.

---

## Data Flow Example (Mean Aggregation)

1. **ESP32** sends UDP packet:
   ```json
   {"id": "AABBCC", "temp": 23.4, "hum": 56.7, "caqi": 2, "tvoc": 123, "eco2": 456}
   ```
2. **udp_to_mqtt_mean.py** receives packets from all devices, aggregates values for each measurement, and every 60 seconds publishes:
   - `iot/team19/mean_value/temp`: `23.45` (float, 2 decimals)
   - `iot/team19/mean_value/hum`: `56.70` (float, 2 decimals)
   - `iot/team19/mean_value/caqi`: `2` (int)
   - ...

---

## Integration with InfluxDB

See the `raspberry2/` directory for scripts like `mqtt_to_influx.py`, which subscribe to the MQTT topic and write sensor data to our InfluxDB database for storage and visualization with our Grafana installation.

See also `mqtt_mean_to_influx.py`, which subscribes to the mean value MQTT topics and writes each mean value to InfluxDB for storage and visualization.

## License
MIT