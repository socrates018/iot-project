# IoT Environmental Monitoring System  
**University Course Project**  
*ESP32 + Raspberry Pi + MQTT + Sensor Fusion*  

![Architecture Diagram](./assets/architecture.png) *Replace with your actual diagram*

---

## 📌 Project Overview  
We’re building an IoT system to monitor air quality (VOC/CO₂ via **ENS160**) and temperature/humidity (**AHT21**), using **ESP32-C3 Super Mini** nodes and a **Raspberry Pi** hub. Data is transmitted via MQTT to a public broker and stored in a database for visualization.  

### Key Features  
- ✅ Real-time sensor fusion (ENS160 + AHT21)  
- ✅ MQTT communication (ESP32 → Raspberry Pi → Public Broker)  
- ✅ RGB Neopixel feedback for local sensor status  
- ✅ PlatformIO-based firmware (ESP32) + Python middleware (RPi)  
- ✅ Public broker integration (HiveMQ/Mosquitto) + Database logging  

---

## 🛠 Hardware Setup  

### Components  
| Device/Part          | Details                                                                 |  
|----------------------|-------------------------------------------------------------------------|  
| **ESP32-C3 Super Mini** | 32-bit RISC-V, WiFi/BLE, 4MB Flash                                     |  
| **ENS160**           | Air Quality Sensor (VOC, eCO₂, AQI)                                    |  
| **AHT21**            | Temperature & Humidity Sensor (±2% RH accuracy)                        |  
| **RGB Neopixel**     | WS2812B Addressable LED (Status Indicator)                             |  
| **Raspberry Pi 4**   | MQTT Broker Middleware + Database Connector                            |  

### 🔌 Sensor & ESP32 Pinout  
**Custom Sensor Board (ENS160 + AHT21):**  
| Sensor  | ESP32 Pin | Function       |  
|---------|-----------|----------------|  
| ENS160  | GPIO4     | I²C SDA        |  
| ENS160  | GPIO5     | I²C SCL        |  
| AHT21   | GPIO4     | Shared I²C SDA |  
| AHT21   | GPIO5     | Shared I²C SCL |  
| Neopixel| GPIO8     | Data Line      |  

**ESP32-C3 Super Mini Pinout Reference:**  
![ESP32-C3 Pinout](./assets/esp32c3_pinout.png) *Add actual pinout image*  

---

## 📡 System Architecture  
```mermaid
graph LR
    A[ESP32-C3 Sensors] -->|MQTT (WiFi)| B[Raspberry Pi]
    B -->|MQTT| C[(Public Broker e.g. HiveMQ)]
    C --> D[(Database: InfluxDB/TimescaleDB)]
    D --> E[Dashboard: Grafana]