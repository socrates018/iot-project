# WiFi MQTT Test Concept 4 (UDP Sensor Sender)

This project demonstrates an ESP32-based sensor node that reads environmental data and sends it via UDP to a remote server. It is designed for use with PlatformIO and ESP-IDF, and features air quality and environmental sensing, WiFi connectivity, and a NeoPixel LED status indicator.

## Features

- **WiFi Station Mode**: Connects to a specified WiFi network.
- **UDP Transmission**: Sends sensor data to a remote server using UDP, with DNS hostname resolution.
- **Sensors**:
  - **ENS160**: Air quality sensor (CAQI, TVOC, eCO2)
  - **AHT20**: Temperature and humidity sensor
- **NeoPixel LED**: Visualizes air quality index (CAQI) with color codes.
- **MAC Address Identification**: Includes the last byte of the device's MAC address in each UDP packet for unique identification.

## UDP Packet Format

Before sending, each UDP packet is formatted as:

```
temp=<temperature>,hum=<humidity>,id=<last_mac_byte>
```

Example:
```
temp=23.45,hum=56.78,id=AB
```

- `temp`: Temperature in Celsius (float, 2 decimals)
- `hum`: Relative humidity in percent (float, 2 decimals)
- `id`: Last byte of the ESP32's WiFi MAC address (hex, uppercase)

## Network Configuration

- **WiFi SSID**: `1`
- **WiFi Password**: `minecraft123`
- **UDP Target Host**: `team19pi.ddns.net`
- **UDP Target Port**: `8080`

## Hardware Connections

- **I2C SCL**: GPIO 9
- **I2C SDA**: GPIO 7
- **NeoPixel (WS2812) Data**: GPIO 8

## LED Color Codes (CAQI)

- 1: Green (Good)
- 2: Yellow (Fair)
- 3: Orange (Moderate)
- 4: Purple (Poor)
- 5: Red (Very Poor)
- Default: Blue (Error/Unknown)

## Project Structure

- `src/main.c`: Main application source code
- `components/`: Custom and third-party ESP-IDF components (ENS160, AHT20, led_strip, etc.)
- `platformio.ini`: PlatformIO project configuration

## Building and Flashing

1. Install [PlatformIO](https://platformio.org/)
2. Connect your ESP32 device
3. Build and upload the firmware:
   ```
   pio run --target upload
   ```

## Dependencies

- ESP-IDF (via PlatformIO)
- Custom components: `aht20`, `esp_ens160`, `espressif__led_strip`

## Notes

- Ensure your WiFi credentials and UDP target host/port are correct in `main.c`.
- The project uses DNS to resolve the UDP target hostname.
- The UDP receiver should be listening on the specified host and port to receive sensor data.

---

**Author:** team19pi

For questions or issues, please open an issue in this repository.