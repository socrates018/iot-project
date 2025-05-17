```markdown
# IoT Environmental Monitoring System  
**University Course "IoT" Project**  

---

## Table of Contents  
1. [Project Overview](#-project-overview)  
2. [System Architecture](#-system-architecture)  
3. [Hardware Configuration](#-hardware-configuration)  
4. [Software Implementation](#-software-implementation)  
5. [Network Configuration](#-network-configuration)  
6. [Testing & Validation](#-testing--validation)  
7. [Setup & Installation](#-setup--installation)  
8. [Security Considerations](#-security-considerations)  
9. [Future Roadmap](#-future-roadmap)  
10. [Resources](#-resources)  
11. [Contributors](#-contributors)  

---

## 🎯 Project Overview  
A distributed IoT system for city-wide environmental monitoring, featuring:  
- **ESP32-C3 Super Mini** nodes with **ENS160** (air quality) and **AHT21** (temperature/humidity) sensors.  
- **Raspberry Pi 4** acting as a central **MQTT broker** (Mosquitto), **data gateway**, and **database server**.  
- **InfluxDB** for lightweight, time-series data storage.  
- **Grafana** for real-time dashboard visualization.  

**Key Objectives:**  
- Deploy sensors across a city, connected via WiFi to a centralized gateway.  
- Implement secure MQTT communication with QoS 1.  
- Enable remote monitoring through port forwarding and Dynamic DNS (DDNS).  
- Design a cost-effective and scalable architecture.  

---

## 🏗 System Architecture  
```plaintext
                                                                               
[ENS160 + AHT21 Sensors]                 [Raspberry Pi 4 Gateway]  
              │                                      │  
              ▼                                      ▼  
[ESP32-C3] → I²C → Sensor Data → WiFi → Mosquitto MQTT Broker → InfluxDB  
              │                                      │                  ▲  
              └───────── Neopixel (GPIO8) ───────────┘                  └── Grafana Dashboard  
```  
**Flow Explanation:**  
1. Sensors transmit data via I²C to ESP32-C3 nodes.  
2. ESP32-C3 nodes publish JSON payloads to the Mosquitto broker on the Raspberry Pi over WiFi.  
3. The Raspberry Pi processes data and stores it in InfluxDB.  
4. Grafana pulls data from InfluxDB for visualization.  
5. Neopixel LEDs on ESP32-C3 provide local status feedback (e.g., air quality alerts).  

---

## 🛠 Hardware Configuration  
**Sensor Node (ESP32-C3):**  
- **Microcontroller**: ESP32-C3 Super Mini (WiFi/Bluetooth LE).  
- **Sensors**:  
  - [ENS160](https://www.sciosense.com/products/environmental-sensors/ens160/) (Air Quality: CO₂, TVOC, AQI).  
  - [AHT21](https://www.adafruit.com/product/4566) (Temperature & Humidity).  
- **Peripheral**: Neopixel LED (GPIO8) for visual alerts.  

**Gateway (Raspberry Pi 4):**  
- **CPU**: Broadcom BCM2711 (Quad-core Cortex-A72).  
- **Storage**: 64GB MicroSD card.  
- **Connectivity**: Ethernet/WiFi for 24/7 operation.  

---

## 💻 Software Implementation  
**ESP32-C3 Firmware:**  
- Arduino-based code for I²C sensor communication.  
- MQTT client ([PubSubClient](https://github.com/knolleary/pubsubclient) library) with QoS 1.  
- JSON payload format:  
  ```json
  {
    "node_id": "node_01",
    "temp": 23.5,
    "humidity": 45,
    "aqi": 12,
    "timestamp": 1678901234
  }
  ```  

**Raspberry Pi Services:**  
- **Mosquitto MQTT Broker**: Secured with username/password authentication.  
- **InfluxDB**: Time-series database with retention policies.  
- **Grafana**: Dashboard configured with real-time graphs and alerts.  

---

## 🌐 Network Configuration  
**Key Components:**  
- **Port Forwarding**: MQTT port (default 1883) forwarded on the gateway's router.  
- **Dynamic DNS (DDNS)**: Ensures consistent domain name (e.g., `gateway.example.com`) despite dynamic public IP changes.  
- **Static IP**: Raspberry Pi assigned a static LAN IP (e.g., `192.168.1.100`).  

**Deployment Topology:**  
- Sensors connect to the gateway via public IP/domain over WiFi.  
- Data flows: `Sensor → Public Internet → DDNS → Raspberry Pi → InfluxDB`.  

---

## 🧪 Testing & Validation  
1. **Sensor Calibration**: Validate ENS160 and AHT21 readings against reference devices.  
2. **MQTT Reliability**: Test QoS 1 message delivery under intermittent connectivity.  
3. **End-to-End Latency**: Measure data transmission delay from sensor to dashboard (<2s target).  
4. **Stress Testing**: Simulate 20+ nodes publishing simultaneously.  

---

## ⚙ Setup & Installation  
### Raspberry Pi Setup  
1. Install Mosquitto:  
   ```bash
   sudo apt update && sudo apt install mosquitto mosquitto-clients
   ```  
2. Configure Mosquitto:  
   - Create credentials:  
     ```bash
     sudo mosquitto_passwd -c /etc/mosquitto/passwd your_username
     ```  
   - Edit `/etc/mosquitto/mosquitto.conf` to enable authentication.  
3. Install InfluxDB & Grafana:  
   ```bash
   wget -q https://repos.influxdata.com/influxdb.key
   sudo apt-key add influxdb.key
   echo "deb https://repos.influxdata.com/debian buster stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
   sudo apt update && sudo apt install influxdb grafana
   ```  
4. Start services:  
   ```bash
   sudo systemctl enable influxdb grafana-server mosquitto
   ```  

### ESP32-C3 Setup  
1. Flash firmware using [PlatformIO](https://platformio.org/) or Arduino IDE.  
2. Configure `config.h`:  
   ```cpp
   #define WIFI_SSID "Your_SSID"
   #define WIFI_PASS "Your_Password"
   #define MQTT_SERVER "gateway.example.com"
   #define MQTT_USER "your_username"
   #define MQTT_PASS "your_password"
   ```  

---

## 🔒 Security Considerations  
- **MQTT Security**:  
  - Use TLS/SSL encryption (see [Mosquitto TLS guide](https://mosquitto.org/man/mosquitto-tls-7.html)).  
  - Enforce client authentication.  
- **Network Security**:  
  - Regularly update Raspberry Pi OS and services.  
  - Restrict SSH access via `ufw` firewall.  
- **Data Privacy**: Anonymize sensor locations in public dashboards.  

---

## 🛣 Future Roadmap  
- Integrate LoRaWAN for low-power, long-range sensor nodes.  
- Migrate to InfluxDB Cloud for centralized monitoring.  
- Add edge computing (e.g., anomaly detection on Raspberry Pi).  
- Implement OTA firmware updates for ESP32-C3 nodes.  

---

## 📚 Resources  
- **Mosquitto MQTT**: [mosquitto.org](https://mosquitto.org/)  
- **InfluxDB Documentation**: [docs.influxdata.com](https://docs.influxdata.com/influxdb/v2.6/)  
- **Grafana Dashboard Setup**: [grafana.com/docs](https://grafana.com/docs/grafana/latest/datasources/influxdb/)  

---

## 👥 Contributors  
- [John Doe](https://github.com/johndoe) - Hardware Integration  
- [Jane Smith](https://github.com/janesmith) - Software Development  
- University of IoT, Class of 2023  
``` 

**Key Improvements:**  
- Added detailed code snippets with syntax highlighting.  
- Included direct links to hardware datasheets and software libraries.  
- Expanded setup instructions with step-by-step commands.  
- Added security guide references and firewall tips.  
- Improved readability with consistent formatting and emojis.