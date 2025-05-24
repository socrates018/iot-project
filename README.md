# IoT Project: Concept 4 Architecture  

This repository implements a distributed IoT system for environmental sensing and data collection, based on Concept 4. The system is designed for real-world deployment, with each ESP32 sensor node and Raspberry Pi gateway located in different homes, using DDNS and port forwarding for remote connectivity. The architecture includes ESP32-C3 Super Mini boards, environmental sensors, two Raspberry Pi devices, a remote MQTT broker, and a remote database server.  

## System Overview  

- **ESP32 Sensor Nodes** (PlatformIO projects in `platformio/`):  
  - Hardware: ESP32-C3 Super Mini boards  
  - Sensors: AHT20 (temperature/humidity), ENS160 (air quality/CO2/TVOC)  
  - Each ESP32 node is deployed in a separate home, collecting local environmental data.  
  - Sensor data is sent via UDP to a Raspberry Pi gateway (Raspberry Pi 1) in the same home.  

- **Raspberry Pi 1 (raspberry1) – Home Gateway**:  
  - Runs a UDP server to receive sensor data from the local ESP32 node (see `platformio/wifi_mqtt_test_concept4/udp_server_raspi_example.py`).  
  - Uses Dynamic DNS (DDNS) and port forwarding to be accessible from outside the home network.  
  - Acts as a gateway: receives UDP packets, parses them, and publishes the data to a remote MQTT broker.  
  - Example scripts and templates are in the `raspberry1/` folder, including class examples for MQTT publishing.  

- **Remote MQTT Broker**:  
  - Hosted on a remote server (cloud or university server).  
  - Receives published sensor data from all Raspberry Pi 1 gateways (from different homes).  
  - Forwards data to all subscribers, including Raspberry Pi 2 and other clients.  

- **Raspberry Pi 2 (raspberry2) – Remote Data Aggregator**:  
  - Subscribes to the remote MQTT broker to receive sensor data from all homes.  
  - Saves incoming data to a remote database (e.g., InfluxDB) for long-term storage and analysis.  
  - Hosts a web server to visualize or provide access to the stored data.  
  - Example scripts for MQTT-to-DB and web server are in the `raspberry2/` folder.  

- **Remote Database Server**:  
  - Stores all sensor data received via MQTT.  
  - Can be queried by the web server for visualization and analytics.  

## Deployment Details  

- **DDNS & Port Forwarding**: Each Raspberry Pi 1 uses a DDNS service (e.g., DuckDNS, No-IP) and router port forwarding to allow ESP32 nodes to send UDP packets from anywhere, and to enable remote management.  
- **Distributed Homes**: Each ESP32 and Raspberry Pi 1 pair is installed in a different home, enabling a scalable, multi-location sensor network.  
- **Security**: Ensure strong passwords and secure port forwarding on all home routers.  

## Folder Structure  
- `platformio/` - ESP32 firmware projects (sensor, LED, WiFi/MQTT/UDP examples)  
- `raspberry1/` - Gateway scripts for UDP-to-MQTT publishing, DDNS setup, and class MQTT examples  
- `raspberry2/` - Scripts for MQTT subscription, database writing, and web server  
- `pymakr/` - MicroPython projects for ESP32 (optional/legacy)  
- `concepts/` - Project concept images and documentation  

## Getting Started  
1. **ESP32 Nodes**: Flash the appropriate firmware from `platformio/` to your ESP32-C3 Super Mini boards. Connect AHT20 and ENS160 sensors as described in the project documentation.  
2. **Raspberry Pi 1**: Set up DDNS and port forwarding. Run the UDP server and MQTT publisher scripts from `raspberry1/`.  
3. **MQTT Broker**: Set up a remote MQTT broker (e.g., Mosquitto, HiveMQ) accessible to all Raspberry Pis and the remote server.  
4. **Raspberry Pi 2**: Run the MQTT subscriber, database writer, and web server scripts from `raspberry2/`.  
5. **Remote Database**: Ensure the remote database server (e.g., InfluxDB) is running and accessible.  

See the README files in each subfolder for detailed setup and usage instructions. Refer to the class example scripts in `raspberry1/class_examples/` for MQTT publishing and other utilities.  

## Requirements  
- ESP32-C3 Super Mini boards with AHT20 and ENS160 sensors  
- Two Raspberry Pi devices (or similar Linux SBCs)  
- DDNS service and router port forwarding for each home gateway  
- Remote MQTT broker  
- Remote database server (e.g., InfluxDB)  
- Python 3.x (for Raspberry Pi scripts)  
- PlatformIO (for ESP32 firmware)  

## License  
MIT
