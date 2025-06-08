#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <sys/param.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "lwip/inet.h"
#include "freertos/semphr.h"
#include "esp_http_client.h"
#include "driver/i2c_master.h"
#include "ens160.h"
#include "aht20.h"
#include "led_strip.h"
#include "driver/gpio.h"
#include "lwip/sockets.h"
#include "esp_netif.h"
#include <netdb.h>

// UDP/TCP Server configuration
// #define HOST   "team19pi.ddns.net"//"192.168.1.9"
#define HOST   "kaltsas123.dyndns.org"
#define PORT   8080

// Protocol selection: set PROTOCOL_USE_TCP to 1 for TCP, 0 for UDP
#define PROTOCOL_USE_TCP 0

// WiFi configuration
// #define WIFI_SSID "COSMOTE-203853"
// #define WIFI_PASS "4tu3a8fesnptt7n5"
#define WIFI_SSID "1"
#define WIFI_PASS "minecraft123"

// Optionally override the last 3 bytes of the MAC address for device ID
#define USE_VIRTUAL_MAC 0
#define VIRTUAL_MAC_ID "A1B2C3"

// I2C configuration for driver_ng
#define I2C_MASTER_SCL_IO           9
#define I2C_MASTER_SDA_IO           7
#define I2C_MASTER_FREQ_HZ          100000
#define I2C_MASTER_PORT             0

// LED configuration
#define NEOPIXEL_GPIO 8
#define NUM_PIXELS    1

// LED intensity (0-255)
#define LED_INTENSITY 5

// Sensor send interval (in seconds)
#define SENSOR_SEND_INTERVAL_SEC 10

// Event group for WiFi connection
static EventGroupHandle_t s_wifi_event_group;
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1

static const char *TAG = "DEBUG";

// WiFi event handler: Handles WiFi and IP events for connection management
static void wifi_event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        printf("[WiFi] STA start event, connecting...\n");
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        printf("[WiFi] Disconnected, reconnecting...\n");
        esp_wifi_connect();
        xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
        xEventGroupClearBits(s_wifi_event_group, WIFI_CONNECTED_BIT); // Clear connected bit on disconnect
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        printf("[WiFi] Got IP\n");
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

// Sends sensor data as a TCP packet to the configured host and port
#if PROTOCOL_USE_TCP
static void tcp_send_sensor_data(const char *payload) {
    printf("Payload: %s\n", payload);
    struct sockaddr_in dest_addr;
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(PORT);
    const struct hostent *he = gethostbyname(HOST);
    if (!he || he->h_addrtype != AF_INET || he->h_length != 4) {
        printf("Failed to resolve TCP target host\n");
        return;
    }
    memcpy(&dest_addr.sin_addr, he->h_addr, he->h_length);
    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
    if (sock < 0) {
        printf("Unable to create TCP socket\n");
        return;
    }
    if (connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) < 0) {
        printf("TCP connect failed\n");
        close(sock);
        return;
    }
    int sent = send(sock, payload, strlen(payload), 0);
    if (sent < 0) {
        printf("TCP send failed\n");
    } else {
        printf("TCP packet sent to %s:%d (%d bytes)\n", inet_ntoa(dest_addr.sin_addr), PORT, sent);
    }
    close(sock);
}
// Sends sensor data as a UDP packet to the configured host and port (now supports hostname or IP)
#else
static void udp_send_sensor_data(const char *payload) {
    printf("Payload: %s\n", payload);
    struct sockaddr_in dest_addr;
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(PORT);
    const struct hostent *he = gethostbyname(HOST);
    if (!he || he->h_addrtype != AF_INET || he->h_length != 4) {
        printf("Failed to resolve UDP target host\n");
        return;
    }
    memcpy(&dest_addr.sin_addr, he->h_addr, he->h_length);
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) {
        printf("Unable to create UDP socket\n");
        return;
    }
    int sent = sendto(sock, payload, strlen(payload), 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
    if (sent < 0) {
        printf("UDP send failed\n");
    } else {
        printf("UDP packet sent to %s:%d (%d bytes)\n", inet_ntoa(dest_addr.sin_addr), PORT, sent);
    }
    close(sock);
}
#endif

// Initializes WiFi in station mode and waits for connection
static void wifi_init_sta(void) {
    s_wifi_event_group = xEventGroupCreate();
    printf("[WiFi] Initializing network interfaces...\n");
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL, &instance_got_ip));
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());
    printf("[WiFi] Started, waiting for connection...\n");
    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT, pdFALSE, pdFALSE, portMAX_DELAY);
    if (bits & WIFI_CONNECTED_BIT) {
        printf("[WiFi] Connected to WiFi: %s\n", WIFI_SSID);
    } else {
        printf("[WiFi] Connection failed\n");
    }
}

// Initializes the I2C master bus using the new driver_ng API
esp_err_t i2c_master_bus_init_ng(i2c_master_bus_handle_t *bus_handle) {
    i2c_master_bus_config_t bus_config = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port = I2C_MASTER_PORT,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_LOGI(TAG, "Initializing I2C master bus...");
    return i2c_new_master_bus(&bus_config, bus_handle);
}

// Helper: Set LED color based on CAQI value
static void set_led_color(led_strip_handle_t strip, uint8_t caqi) {
    uint8_t r = 0, g = 0, b = 0;
    uint8_t intensity = LED_INTENSITY;
    switch (caqi) {
        case 0:
            // CAQI 0: full red, max intensity
            r = 255; g = 0; b = 0;
            intensity = 255;
            break;
        case 1:
            r = 0; g = 255; b = 0;
            break;
        case 2:
            r = 255; g = 255; b = 0;
            break;
        case 3:
            r = 255; g = 128; b = 0;
            break;
        case 4:
            r = 128; g = 0; b = 128;
            break;
        case 5:
            r = 255; g = 0; b = 0;
            break;
        default:
            r = 255; g = 255; b = 255;
            break;
    }
    // Scale color by intensity
    r = (r * intensity) / 255;
    g = (g * intensity) / 255;
    b = (b * intensity) / 255;
    led_strip_clear(strip);
    led_strip_set_pixel(strip, 0, r, g, b);
    led_strip_refresh(strip);
}

// Helper: Read ENS160 sensor
static bool read_ens160(ens160_handle_t ens160_handle, ens160_air_quality_data_t *air_data, uint8_t *caqi) {
    if (ens160_get_measurement(ens160_handle, air_data) == ESP_OK &&
        air_data->uba_aqi > 0 && air_data->tvoc > 0 && air_data->eco2 > 0) {
        ens160_aqi_uba_row_t aqi_def = ens160_aqi_index_to_definition(air_data->uba_aqi);
        printf("[ENS160] CAQI: %d (%s) | TVOC: %u ppb | eCO2: %u ppm\n",
               air_data->uba_aqi, aqi_def.rating, air_data->tvoc, air_data->eco2);
        *caqi = air_data->uba_aqi;
        return true;
    } else {
        printf("[ENS160] Read error or invalid data\n");
        *caqi = 0;
        return false;
    }
}

// Helper: Read AHT20 sensor
static bool read_aht20(aht20_dev_handle_t aht20_handle, float *temperature, float *humidity, ens160_handle_t ens160_handle) {
    if (aht20_read_float(aht20_handle, temperature, humidity) == ESP_OK) {
        printf("[AHT20] Temperature: %.2f°C | Humidity: %.2f%%\n", *temperature, *humidity);
        if (ens160_set_compensation_factors(ens160_handle, *temperature, *humidity) != ESP_OK) {
            printf("[ENS160] Failed to set compensation factors\n");
        }
        return true;
    } else {
        printf("[AHT20] Read error\n");
        return false;
    }
}

// Helper: Print WiFi info
static void print_wifi_info() {
    esp_netif_ip_info_t ip_info;
    esp_netif_t *netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
    EventBits_t bits = xEventGroupGetBits(s_wifi_event_group);
    if ((bits & WIFI_CONNECTED_BIT) && netif && esp_netif_get_ip_info(netif, &ip_info) == ESP_OK) {
        wifi_ap_record_t ap_info;
        if (esp_wifi_sta_get_ap_info(&ap_info) == ESP_OK) {
            printf("[WiFi] IP: %s | RSSI: %d dBm | Channel: %d\n",
                   ip4addr_ntoa((const ip4_addr_t *)&ip_info.ip), ap_info.rssi, ap_info.primary);
        } else {
            printf("[WiFi] IP: %s\n", ip4addr_ntoa((const ip4_addr_t *)&ip_info.ip));
        }
    } else {
        printf("[WiFi] No connection\n");
    }
}

// Helper: Send sensor data as JSON
static void send_sensor_json(float temperature, float humidity, uint8_t caqi, uint32_t tvoc, uint32_t eco2, const char *mac_id) {
    char json_payload[128];
    snprintf(json_payload, sizeof(json_payload),
        "{\"temp\":%.2f,\"hum\":%.2f,\"caqi\":%u,\"tvoc\":%lu,\"eco2\":%lu,\"id\":\"%s\"}",
        temperature, humidity, caqi, (unsigned long)tvoc, (unsigned long)eco2, mac_id);
#if PROTOCOL_USE_TCP
    tcp_send_sensor_data(json_payload);
#else
    udp_send_sensor_data(json_payload);
#endif
}

// Main application entry point: initializes system, WiFi, LED, and starts sensor task
void app_main() {
    vTaskDelay(pdMS_TO_TICKS(500));
    ESP_LOGI(TAG, "Starting app_main");
    ESP_ERROR_CHECK(nvs_flash_init());
    srand((unsigned)time(NULL));
    wifi_init_sta();
    led_strip_handle_t led_strip;
    led_strip_config_t led_strip_config = {
        .strip_gpio_num = NEOPIXEL_GPIO,
        .max_leds = NUM_PIXELS,
        .led_pixel_format = LED_PIXEL_FORMAT_GRB,
        .led_model = LED_MODEL_WS2812,
        .flags.invert_out = false,
    };
    led_strip_rmt_config_t led_rmt_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .resolution_hz = 10 * 1000 * 1000,
        .mem_block_symbols = 0,
        .flags.with_dma = false,
    };
    if (led_strip_new_rmt_device(&led_strip_config, &led_rmt_config, &led_strip) == ESP_OK) {
        ESP_LOGI(TAG, "LED strip initialized");
        led_strip_clear(led_strip);
        led_strip_refresh(led_strip);
    } else {
        ESP_LOGE(TAG, "LED strip initialization failed");
    }
    // --- Begin merged sensor logic ---
    // I2C and sensor initialization
    i2c_master_bus_handle_t i2c_bus_handle = NULL;
    if (i2c_master_bus_init_ng(&i2c_bus_handle) != ESP_OK) {
        ESP_LOGE(TAG, "I2C bus init failed");
        return;
    }
    ESP_LOGI(TAG, "I2C bus initialized");
    ens160_config_t ens160_config = {
        .i2c_address = I2C_ENS160_DEV_ADDR_HI,
        .i2c_clock_speed = I2C_ENS160_DEV_CLK_SPD,
        .irq_enabled = false,
        .irq_data_enabled = false,
        .irq_gpr_enabled = false,
        .irq_pin_driver = ENS160_INT_PIN_DRIVE_OPEN_DRAIN,
        .irq_pin_polarity = ENS160_INT_PIN_POLARITY_ACTIVE_LO
    };
    ens160_handle_t ens160_handle = NULL;
    aht20_dev_handle_t aht20_handle = NULL;
    i2c_aht20_config_t aht20_config = {
        .i2c_config = {
            .device_address = AHT20_ADDRESS_0,
            .scl_speed_hz = I2C_MASTER_FREQ_HZ,
        },
        .i2c_timeout = 1000,
    };
    if (ens160_init(i2c_bus_handle, &ens160_config, &ens160_handle) != ESP_OK ||
        aht20_new_sensor(i2c_bus_handle, &aht20_config, &aht20_handle) != ESP_OK) {
        ESP_LOGE(TAG, "Sensor initialization failed");
        return;
    }
    ESP_LOGI(TAG, "ENS160 and AHT20 sensors initialized");
    char mac_id[7];
#if USE_VIRTUAL_MAC
    strncpy(mac_id, VIRTUAL_MAC_ID, sizeof(mac_id));
    mac_id[6] = '\0';
#else
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    snprintf(mac_id, sizeof(mac_id), "%02X%02X%02X", mac[3], mac[4], mac[5]);
#endif
    float temperature = 0.0f, humidity = 0.0f;
    uint8_t caqi = 6; // Default to 6 (invalid)
    uint32_t last_send_time = xTaskGetTickCount();
    while (1) {
        ens160_air_quality_data_t air_data;
        bool valid_ens160 = read_ens160(ens160_handle, &air_data, &caqi);
        bool valid_aht20 = read_aht20(aht20_handle, &temperature, &humidity, ens160_handle);
        EventBits_t bits = xEventGroupGetBits(s_wifi_event_group);
        uint32_t now = xTaskGetTickCount();
        bool wifi_connected = (bits & WIFI_CONNECTED_BIT) != 0;
        if (wifi_connected && valid_aht20 && valid_ens160) {
            set_led_color(led_strip, caqi);
            if (now - last_send_time >= (SENSOR_SEND_INTERVAL_SEC * 1000 / portTICK_PERIOD_MS)) {
                send_sensor_json(temperature, humidity, caqi, air_data.tvoc, air_data.eco2, mac_id);
                last_send_time = now;
            }
        } else {
            set_led_color(led_strip, 0); // Bright red for error/alert
        }
        static uint32_t last_wifi_print = 0;
        if (now - last_wifi_print >= (2 * SENSOR_SEND_INTERVAL_SEC * 1000 / portTICK_PERIOD_MS)) {
            print_wifi_info();
            last_wifi_print = now;
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
