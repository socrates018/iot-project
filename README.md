# IoT Environmental Monitoring System  
**University Course Project | Embedded Systems & IoT Engineering**  

---

## Table of Contents  
1. [Project Overview](#-project-overview)  
2. [System Architecture](#-system-architecture)  
3. [Hardware Configuration](#-hardware-configuration)  
4. [Software Implementation](#-software-implementation)  
5. [Testing & Validation](#-testing--validation)  
6. [Setup & Installation](#-setup--installation)  
7. [Future Roadmap](#-future-roadmap)  
8. [Resources](#-resources)  
9. [Contributors](#-contributors)  

---

## 🎯 Project Overview  
A distributed IoT system for real-time environmental monitoring, featuring:  
- **ESP32-C3 Super Mini** nodes collecting data from **ENS160** (air quality) and **AHT21** (temperature/humidity) sensors.  
- **Raspberry Pi 4** acting as an MQTT broker and data gateway.  
- Public MQTT broker ([HiveMQ](https://www.hivemq.com/public-mqtt-broker/)) for global data access.  
- Time-series database ([TimescaleDB](https://www.timescale.com/)) for persistent storage.  

**Key Objectives:**  
- Demonstrate sensor fusion (I²C multiplexing on a shared bus).  
- Implement reliable MQTT communication with QoS 1.  
- Develop a scalable architecture for multi-node deployments.  

---

## 🏗 System Architecture  
```plaintext
                                                                               
         [ENS160+AHT21]                            [Raspberry Pi 4]          [Cloud]
              │                                        │                       │
              ▼                                        ▼                       ▼
[ESP32-C3] → I²C → Sensor Data → WiFi → MQTT → (Local Broker) → MQTT → (Public Broker) → TimescaleDB
              │                                        │                       ▲
              └───────── Neopixel (GPIO8) ─────────────┘                       └── Grafana Dashboard