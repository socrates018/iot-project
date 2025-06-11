# IoT Project: Environmental Sensing and Data Collection System

**University Course Project – Internet of Things  & Applications**

This repository contains the final project for a university course on IoT Systems. The project demonstrates the design and implementation of a scalable, real-time environmental monitoring system using modern IoT technologies. It covers the full stack from embedded firmware to cloud-based data visualization.

**Project Team:**
- Team No.19
- Course: Internet of Things & Applications
- Instructor: Choumas Kostas
- Semester: 8th 

---

This robust, scalable IoT system enables real-time environmental monitoring across multiple locations. The architecture is designed to efficiently collect, aggregate, and visualize sensor data from distributed ESP32 nodes, using a two-stage Raspberry Pi gateway and webserver approach. The system leverages UDP, MQTT, InfluxDB, and Grafana to provide reliable data flow and insightful visualization.

**Project Highlights:**
- ESP32-C3 Super Mini boards with environmental sensors (AHT20 and ENS160) deployed in various locations.
- Sensor data is transmitted via UDP to a central Raspberry Pi gateway (Raspberry Pi 1), which aggregates and forwards the data to a remote MQTT broker.
- A second Raspberry Pi (Raspberry Pi 2) subscribes to the MQTT broker, stores the data in an InfluxDB database, and hosts a Grafana web dashboard for visualization.

This system is based on a centralized gateway concept (concept 4), where all sensor nodes communicate with a single gateway, simplifying network management and enhancing scalability. The design ensures secure, reliable, and efficient monitoring for smart home or distributed sensor applications.

---

## System Overview

- **ESP32 Sensor Nodes**
  - Hardware: ESP32-C3 Super Mini boards.
  - Sensors: AHT20 (temperature/humidity), ENS160 (air quality/CO2/TVOC).
  - Multiple ESP32 nodes deployed in different locations, collecting environmental data.
  - Sensor data is sent to a central Raspberry Pi gateway (Raspberry Pi 1).

- **Raspberry Pi 1 (raspberry1) – Central Gateway**:
  - Runs a UDP server to receive sensor data from all ESP32 nodes.
  - Acts as a central collection point, consolidating data from multiple sensor nodes.
  - Processes and formats the sensor data before publishing to a remote MQTT broker.
  - Publishes updates to the MQTT broker.
  - Example scripts and templates are in the `raspberry1/` folder, including class examples for MQTT publishing.

- **Remote MQTT Broker**:
  - Hosted on a server at IP address 194.177.207.38, port 1883.

- **Raspberry Pi 2 (raspberry2) – Webserver**:
  - Subscribes to the remote MQTT broker to receive sensor data from all ESP32 nodes.
  - Saves incoming data to an InfluxDB database for long-term storage and analysis.
  - Hosts a Grafana web server to visualize and monitor the collected sensor data on port 3000.
  - Core scripts include `mqtt_to_influx.py` for data collection and storage in the `raspberry2/` folder.

- **InfluxDB Database Server**:
  - Located at IP address 194.177.207.38, port 8086.

## Deployment Details

- **Network Configuration**: The Raspberry Pi 1 gateway listens on UDP port 8080 to receive data from all ESP32 nodes.
- **ESP32 Configuration**: Each ESP32 node is configured with the hostname "team19pi.ddns.net" as the UDP target and sends data.
- **Data Collection**: The ESP32 nodes collect temperature, humidity, air quality (CAQI), TVOC, and eCO2 measurements.
- **Data Flow**:
  1. ESP32 nodes send data to Raspberry Pi 1 via UDP.
  2. Raspberry Pi 1 adds timestamps and forwards to MQTT broker every 2 seconds.
  3. Raspberry Pi 2 stores data in InfluxDB and visualizes with Grafana.
- **Security**: Using "team19" credentials for MQTT and database access with proper authentication.

## Main Python Scripts Overview:

### ESP32 Firmware (Concept 4)
- `/platformio/wifi_mqtt_test_concept4/src/main.c` – ESP32 firmware for environmental sensing:
  - Connects to WiFi using the configured SSID and password.
  - Uses the onboard LED to indicate status:
    - **Bright red**: Problem with WiFi connection or sensor error.
    - **Green, yellow, orange, purple, red (dim)**: Indicates CAQI level (air quality index), with green as best (CAQI=1) and dim red as worst (CAQI=5).
  - Collects temperature, humidity, CAQI, TVOC, and eCO2 using AHT20 and ENS160 sensors.
  - Sends JSON-formatted UDP packets every 10 seconds to Raspberry Pi 1 from any network (internet).
  - Example JSON: `{ "temp": 23.45, "hum": 56.78, "caqi": 2, "tvoc": 123, "eco2": 456, "id": "A1B2C3" }`.

### Raspberry Pi 1 (raspberry1)
- `udp_to_mqtt.py` – Receives UDP packets from all ESP32 nodes, adds a UNIX timestamp (UTC+0), and immediately publishes each device's data to its own MQTT topic (`iot/team19/<id>`). Enables real-time, per-device MQTT publishing.
- `udp_to_mqtt_mean.py` – Aggregates received UDP sensor data over a configurable interval (default: 1 minute), computes the mean for each measurement, and publishes each mean value to its respective MQTT topic (e.g., `iot/team19/mean_value/temp`).
- `udp_sender_test.py` – Test script for sending UDP packets to the gateway for debugging.
- `test_tcp.py` – General TCP & UDP communication test script for debugging.

### Raspberry Pi 2 (raspberry2)
- `mqtt_to_influx.py` – Subscribes to all device topics (`iot/team19/<id>`), parses each device's data, and writes it to InfluxDB using the device ID as the measurement name and sensor type as a tag.
- `mqtt_mean_to_influx.py` – Subscribes to all mean value topics (`iot/team19/mean_value/+`), writes each mean value to InfluxDB as a measurement named `mean_value` with the sensor type as a tag.
- `manage_db.py` – Utility for querying and/or deleting measurements from the InfluxDB database.
- `udp_receiver_test.py` – Test script for gateway UDP server simulation.

---

## Network Setup and Remote Access
For this system to function correctly and allow remote access, port forwarding was implemented to allow external connections to reach specific services on our local network. We've also implemented DynDNS (Dynamic DNS) to provide a consistent domain name that always points to our network's changing public IP address. This enables:
- ESP devices to reliably send UDP packets even when server public IP addresses change.
- Remote SSH access for secure system management from anywhere on the Raspberry Pis.
- Grafana web dashboards accessible remotely for monitoring.

---

## Live Data Visualization

You can view the real-time environmental data and dashboards using our public Grafana instance:

[Grafana Visualization Dashboard](http://localhost:3000/public-dashboards/e0ee925f54a64bd8b3042d138fa0b159)

---

## Folder Structure
- `concepts/` - Project concept images (such as architecture diagrams for Concept 3 and Concept 4) to help visualize the system design and evolution.
- `platformio/` - ESP32 firmware projects (sensor, LED, WiFi/MQTT/UDP examples).
- `raspberry1/` - Gateway scripts for UDP-to-MQTT publishing.
- `raspberry2/` - Scripts for MQTT subscription, database writing, and web server hosting and visualization.
- `pymakr/` - MicroPython test projects for ESP32 (legacy).

## Helper Scripts
The repository includes several shell scripts to help with common tasks:

- `run_raspi_python.sh` - Interactive script to run the appropriate Python service based on which Raspberry Pi you're using:
  - Prompts for Raspberry Pi 1 (UDP to MQTT) or Raspberry Pi 2 (MQTT to Influx).
  - Optionally runs the 'mean' aggregation version of each script.
  - For Raspberry Pi 1: Runs either `raspberry1/udp_to_mqtt.py` or `raspberry1/udp_to_mqtt_mean.py`.
  - For Raspberry Pi 2: Runs either `raspberry2/mqtt_to_influx.py` or `raspberry2/mqtt_mean_to_influx.py`.
  - Automatically runs `update.sh` and `venv.sh` first for a seamless setup.

- `install_raspi_project_service.sh` - Interactive script to install one of the main project Python scripts as a systemd service (auto-start on boot):
  - Lets you choose between UDP-to-MQTT (per-device or mean) and MQTT-to-Influx (per-device or mean).
  - Installs the selected script as a systemd service using the Python virtual environment.
  - Enables and starts the service, and shows live logs.

- `update.sh` - Simple Git script to pull the latest changes from the main branch.

- `venv.sh` - Python virtual environment management script that:
  - Creates a Python virtual environment if one doesn't exist.
  - Activates the virtual environment.
  - Updates pip to the latest version.
  - Installs all dependencies from requirements.txt.
  - Optionally runs a specified Python script with the proper environment.

- `git-clone-replace.sh` - Utility for replacing the current repository with a fresh clone (for resolving Git conflicts).

See the README files in each subfolder for detailed setup and usage instructions.

## License
MIT