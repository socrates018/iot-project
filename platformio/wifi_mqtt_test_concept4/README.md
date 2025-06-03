# ESP32-C3 Environmental Sensor Node

This project implements an ESP32-C3 environmental sensor node that collects temperature, humidity, air quality, TVOC, and eCO2 data, and transmits it via UDP to a designated server. It features:

- AHT20 temperature and humidity sensor integration
- ENS160 air quality sensor for CAQI, TVOC, and eCO2 measurements
- RGB LED status indication (color changes based on air quality)
- WiFi connectivity with automatic reconnection
- JSON-formatted UDP data transmission
- Device identification using MAC address

## Features

- **Sensors**:
  - AHT20: Temperature and humidity measurements
  - ENS160: Air quality index (CAQI), TVOC (ppb), and eCO2 (ppm)

- **Connectivity**:
  - WiFi Station Mode with automatic reconnection
  - UDP data transmission to configurable server

- **Visual Feedback**:
  - RGB LED status indication (changes color based on CAQI level)
  - Green: Excellent (1)
  - Yellow: Good (2)
  - Orange: Moderate (3)
  - Purple: Poor (4)
  - Red: Very Poor (5)
  - White: Sensor error

- **Data Format**:
  - JSON payload with timestamp and sensor readings
  - Example: `{"temp":23.45,"hum":56.78,"caqi":2,"tvoc":123,"eco2":456,"id":"AABBCC"}`

## Getting Started

1. Open this folder in PlatformIO/VS Code
2. Configure your settings in `src/main.c`:
   - WiFi SSID and password (`WIFI_SSID` and `WIFI_PASS`)
   - UDP target host and port (`UDP_TARGET_HOST` and `UDP_TARGET_PORT`)
   - I2C pins for sensors (`I2C_MASTER_SCL_IO` and `I2C_MASTER_SDA_IO`)
   - RGB LED pin (`NEOPIXEL_GPIO`)
   - Sensor reading interval (`SENSOR_SEND_INTERVAL_SEC`)
3. Build and upload the project

## Hardware Requirements

- ESP32-C3 board (tested with ESP32-C3-DevKitM-1)
- AHT20 temperature and humidity sensor
- ENS160 air quality sensor
- Addressable RGB LED (WS2812)
- I2C connections for sensors

## Pin Configuration

- **I2C**: SCL Pin 9, SDA Pin 7 (configurable)
- **RGB LED**: Pin 8 (configurable)

## Components

- `src/` - Main application code
- `include/` - Header files
- `components/` - Sensor drivers:
  - `aht20/` - Temperature and humidity sensor driver
  - `esp_ens160/` - Air quality sensor driver
  - `esp-builtin-led/` - LED control utilities
  - `espressif__led_strip/` - LED strip driver
  - `esp_type_utils/` - Helper utilities

## License
MIT