# IoT Project: Concept 4 Architecture  

## Project Evolution: From Concept 3 to Concept 4  

This project initially started with Concept 3, but was later upgraded to Concept 4 for improved scalability and real-world deployment. You can find visual diagrams for each concept in the `concepts/` folder.  

### Concept 3 (Initial Design)  
- ESP32 sensor nodes collect environmental data and send it directly to a central server or broker.  
- Centralized approach, but less scalable for distributed, real-world deployments where each node is in a different home.  

### Concept 4 (Final Design)  
- Multiple ESP32 sensor nodes all send data to a single central Raspberry Pi gateway (Raspberry Pi 1).
- Sensor data is sent via UDP from ESP32 nodes to the Raspberry Pi 1 gateway.
- Raspberry Pi 1 acts as a central gateway, collecting data from all ESP32 nodes and publishing consolidated data to a remote MQTT broker.
- A second Raspberry Pi (Raspberry Pi 2) subscribes to the MQTT broker, writes data to a remote database, and hosts a web server for visualization.
- This centralized gateway approach is efficient for collecting data from multiple sensor nodes while reducing the complexity of having multiple gateways.  

**Why Concept 4?**  
- Concept 4 was chosen because it provides a centralized collection point (Raspberry Pi 1) for all ESP32 sensor data, with the gateway handling connectivity and security to the MQTT broker. This approach simplifies the architecture while still being scalable and secure for monitoring multiple sensor locations.  

This repository implements an IoT system for environmental sensing and data collection, based on Concept 4. The system collects environmental measurements from ESP32 nodes every 10 seconds and sends them via UDP to a central Raspberry Pi 1 gateway. The gateway adds timestamps to the data and forwards it to a remote MQTT broker every 2 seconds in batched updates. The architecture includes ESP32-C3 Super Mini boards with environmental sensors, a central Raspberry Pi gateway, a data aggregator Raspberry Pi, a remote MQTT broker, and an InfluxDB database server.  

## System Overview  

- **ESP32 Sensor Nodes** (PlatformIO projects in `platformio/`):  
  - Hardware: ESP32-C3 Super Mini boards  
  - Sensors: AHT20 (temperature/humidity), ENS160 (air quality/CO2/TVOC)  
  - Multiple ESP32 nodes deployed in different locations, collecting environmental data.  
  - Sensor data is sent via UDP every 10 seconds to a central Raspberry Pi gateway (Raspberry Pi 1).  
  - The ESP32 nodes don't include timestamps in their data; timestamps are added by the gateway.  

- **Raspberry Pi 1 (raspberry1) – Central Gateway**:  
  - Runs a UDP server to receive sensor data from all ESP32 nodes (see `raspberry1/udp_to_mqtt.py`).  
  - Acts as a central collection point, consolidating data from multiple sensor nodes.  
  - Adds Unix timestamps (in nanoseconds) to incoming sensor data.
  - Processes and formats the sensor data before publishing to a remote MQTT broker on topic "iot/team19".
  - Publishes updates to the MQTT broker every 2 seconds with batched data.
  - Example scripts and templates are in the `raspberry1/` folder, including class examples for MQTT publishing.  

- **Remote MQTT Broker**:  
  - Hosted on a server at IP address 194.177.207.38, port 1883.  
  - Receives consolidated sensor data from all ESP32 nodes via the central Raspberry Pi gateway.  
  - Forwards data to all subscribers, primarily the Raspberry Pi 2 using topic "iot/team19".  

- **Raspberry Pi 2 (raspberry2) – Remote Data Aggregator**:  
  - Subscribes to the remote MQTT broker to receive sensor data from all ESP32 nodes.  
  - Saves incoming data to an InfluxDB database for long-term storage and analysis.  
  - Hosts a Grafana web server to visualize and monitor the collected sensor data.  
  - Core scripts include `mqtt_to_influx.py` for data collection and storage in the `raspberry2/` folder.  

- **InfluxDB Database Server**:  
  - Located at IP address 194.177.207.38, port 8086.
  - Stores all sensor data received via MQTT in the "team19_db" database.
  - Provides time-series database capabilities for the Grafana visualization platform.  

## Deployment Details  

- **Network Configuration**: The Raspberry Pi 1 gateway listens on UDP port 8080 to receive data from all ESP32 nodes.
- **ESP32 Configuration**: Each ESP32 node is configured with the hostname "team19pi.ddns.net" as the UDP target and sends data every 10 seconds.
- **Data Collection**: The ESP32 nodes collect temperature, humidity, air quality (CAQI), TVOC, and eCO2 measurements.
- **Data Flow**: 
  1. ESP32 nodes send data to Raspberry Pi 1 via UDP
  2. Raspberry Pi 1 adds timestamps and forwards to MQTT broker every 2 seconds
  3. Raspberry Pi 2 stores data in InfluxDB and visualizes with Grafana
- **Security**: Using "team19" credentials for MQTT and database access with proper authentication.  

## Concept 4: Full Data and Mean Aggregation Pipelines

This repository supports two main data pipelines for environmental sensing and collection:

### 1. Full Data Pipeline
- **ESP32 Sensor Nodes** (see `platformio/wifi_mqtt_test_concept4/`):
  - Collect temperature, humidity, CAQI, TVOC, and eCO2 data using AHT20 and ENS160 sensors.
  - Send JSON-formatted UDP packets every 10 seconds to Raspberry Pi 1.
  - Example JSON: `{ "id": "AABBCC", "temp": 23.45, "hum": 56.78, "caqi": 2, "tvoc": 123, "eco2": 456 }`
- **Raspberry Pi 1** (`raspberry1/udp_to_mqtt.py`):
  - Receives UDP packets from all ESP32 nodes.
  - Adds a timestamp and stores the latest reading for each device.
  - Every 2 seconds, publishes a single MQTT message to `iot/team19` containing a JSON array of all latest readings.
- **Raspberry Pi 2** (`raspberry2/mqtt_to_influx.py`):
  - Subscribes to `iot/team19`.
  - Parses each device's data and writes it to InfluxDB, using the device ID as the measurement name and sensor type as a tag.

### 2. Mean Aggregation Pipeline
- **Raspberry Pi 1** (`raspberry1/udp_to_mqtt_mean.py`):
  - Aggregates all received UDP sensor data over a configurable interval (default: 20 seconds).
  - Computes the mean for each measurement (temp, hum as float with 2 decimals, others as int).
  - Publishes each mean value to its own MQTT topic (e.g., `iot/team19/mean_value/temp`).
- **Raspberry Pi 2** (`raspberry2/mqtt_mean_to_influx.py`):
  - Subscribes to all mean value topics (e.g., `iot/team19/mean_value/+`).
  - Writes each mean value to InfluxDB as a measurement named `mean_value` with the sensor type as a tag.

---

## ESP32 Firmware (Concept 4)
- See `platformio/wifi_mqtt_test_concept4/` for the latest ESP32 firmware supporting UDP JSON transmission, device identification, and sensor integration.
- The firmware is configurable for WiFi, UDP target, and sensor pins. See the folder's README for details.
- Example JSON sent by ESP32:
  ```json
  {"id": "AABBCC", "temp": 23.45, "hum": 56.78, "caqi": 2, "tvoc": 123, "eco2": 456}
  ```

---

## Example Data Flows

### Full Data Example
1. ESP32 sends UDP packet:
   ```json
   {"id": "AABBCC", "temp": 23.4, "hum": 56.7, "caqi": 2, "tvoc": 123, "eco2": 456}
   ```
2. `udp_to_mqtt.py` receives and stores the latest reading for each device.
3. Every 2 seconds, publishes:
   ```json
   [
     {"id": "AABBCC", "temp": 23.4, ...},
     {"id": "DDEEFF", "temp": 24.1, ...},
     ...
   ]
   ```
   to MQTT topic `iot/team19`.
4. `mqtt_to_influx.py` on Raspberry Pi 2 subscribes and writes each device's data to InfluxDB.

### Mean Aggregation Example
1. ESP32 sends UDP packet as above.
2. `udp_to_mqtt_mean.py` aggregates values for each measurement from all received packets.
3. Every 20 seconds, publishes:
   - `iot/team19/mean_value/temp`: `23.45` (float, 2 decimals)
   - `iot/team19/mean_value/hum`: `56.70` (float, 2 decimals)
   - `iot/team19/mean_value/caqi`: `2` (int)
   - ...
4. `mqtt_mean_to_influx.py` subscribes to all mean value topics and writes each mean value to InfluxDB.

---

## Folder Structure  
- `platformio/` - ESP32 firmware projects (sensor, LED, WiFi/MQTT/UDP examples)  
- `raspberry1/` - Gateway scripts for UDP-to-MQTT publishing, DDNS setup, and class MQTT examples  
- `raspberry2/` - Scripts for MQTT subscription, database writing, and web server  
- `pymakr/` - MicroPython projects for ESP32 (optional/legacy)  
- `concepts/` - Project concept images and documentation  

## Helper Scripts
The repository includes several shell scripts to help with common tasks:

- `run_raspi_python.sh` - Interactive script to run the appropriate Python service based on which Raspberry Pi you're using:
  - For Raspberry Pi 1: Runs the UDP-to-MQTT gateway service
  - For Raspberry Pi 2: Runs the MQTT-to-InfluxDB service
  - Automatically runs `update.sh` and `venv.sh` first for a seamless setup

- `update.sh` - Simple Git script to pull the latest changes from the main branch, keeping your local repository in sync with the remote

- `venv.sh` - Python virtual environment management script that:
  - Creates a Python virtual environment if one doesn't exist
  - Activates the virtual environment
  - Updates pip to the latest version
  - Installs all dependencies from requirements.txt
  - Optionally runs a specified Python script with the proper environment

- `git-clone-replace.sh` - Utility for replacing the current repository with a fresh clone (useful for resolving Git conflicts)

## Getting Started  
1. **ESP32 Nodes**: Flash the appropriate firmware from `platformio/` to your ESP32-C3 Super Mini boards. Connect AHT20 and ENS160 sensors as described in the project documentation.  
2. **Raspberry Pi 1**: Set up the central gateway to listen on UDP port 8080. Run the UDP server and MQTT publisher scripts:
   ```bash
   # Option 1: Using helper script (recommended)
   ./run_raspi_python.sh  # Then select option 1 when prompted

   # Option 2: Direct execution
   python raspberry1/udp_to_mqtt.py
   ```
   This will listen for UDP packets, add timestamps, and publish to the MQTT broker every 2 seconds.

3. **MQTT Broker**: Ensure the MQTT broker at 194.177.207.38:1883 is accessible to both Raspberry Pi devices.  
4. **Raspberry Pi 2**: Run the MQTT subscriber, database writer, and web server scripts:
   ```bash
   # Option 1: Using helper script (recommended)
   ./run_raspi_python.sh  # Then select option 2 when prompted

   # Option 2: Direct execution
   python raspberry2/mqtt_to_influx.py
   ```

5. **InfluxDB Database**: Ensure the InfluxDB server at 194.177.207.38:8086 is running and accessible.  

See the README files in each subfolder for detailed setup and usage instructions. Refer to the class example scripts in `raspberry1/class_examples/` for MQTT publishing and other utilities.  

## Requirements  
- ESP32-C3 Super Mini boards with AHT20 and ENS160 sensors  
- Two Raspberry Pi devices (or similar Linux SBCs):
  - Raspberry Pi 1: For the central UDP gateway and MQTT publishing
  - Raspberry Pi 2: For MQTT subscription, database writing, and visualization
- Network connectivity between all ESP32 nodes and the central gateway
- MQTT broker at 194.177.207.38:1883 with "team19" credentials
- InfluxDB database server at 194.177.207.38:8086 with "team19_db" database
- Grafana visualization platform
- Python 3.x (for Raspberry Pi scripts)  
- PlatformIO (for ESP32 firmware)  

## License  
MIT
