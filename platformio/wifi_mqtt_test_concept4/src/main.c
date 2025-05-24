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
#include "esp_http_client.h" // Moved here from app_main
#include "driver/i2c_master.h"
#include "ens160.h"
#include "aht20.h"
#include "led_strip.h"
#include "driver/gpio.h"
#include "lwip/sockets.h"
#include "esp_netif.h"
#include <netdb.h> // For gethostbyname

// WiFi configuration
#define WIFI_SSID "1"
#define WIFI_PASS "minecraft123"

// I2C configuration for driver_ng
#define I2C_MASTER_SCL_IO           9
#define I2C_MASTER_SDA_IO           7
#define I2C_MASTER_FREQ_HZ          100000
#define I2C_MASTER_PORT             0 // Added missing definition

// LED configuration
#define NEOPIXEL_GPIO 8
#define NUM_PIXELS    1

// UDP configuration
#define UDP_TARGET_HOST   "team19pi.ddns.net" // Changed from IP to hostname
#define UDP_TARGET_PORT   8080 // Changed port to 8080

// Event group for WiFi connection
static EventGroupHandle_t s_wifi_event_group;
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1

static const char *TAG = "UDP_SENSOR";

// WiFi event handler
static void wifi_event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        esp_wifi_connect();
        xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

// UDP send function
static void udp_send_sensor_data(const char *payload) {
    struct sockaddr_in dest_addr = {0};
    struct hostent *he = gethostbyname(UDP_TARGET_HOST);
    if (!he || he->h_addr_list == NULL || he->h_addr_list[0] == NULL) {
        ESP_LOGE(TAG, "DNS lookup failed for %s", UDP_TARGET_HOST);
        return;
    }
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Unable to create UDP socket");
        return;
    }
    dest_addr.sin_addr.s_addr = ((struct in_addr *)he->h_addr_list[0])->s_addr;
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(UDP_TARGET_PORT);
    sendto(sock, payload, strlen(payload), 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
    close(sock);
}

static void wifi_init_sta(void) {
    s_wifi_event_group = xEventGroupCreate();

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
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA)); // Fixed mode
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT, pdFALSE, pdFALSE, portMAX_DELAY);
    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "Connected to WiFi: %s", WIFI_SSID);
    } else {
        ESP_LOGE(TAG, "WiFi connection failed");
    }
}

// Correct the i2c_master_bus_init_ng function signature and usage:
esp_err_t i2c_master_bus_init_ng(i2c_master_bus_handle_t *bus_handle) {
    i2c_master_bus_config_t bus_config = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port = I2C_MASTER_PORT,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    // Use the new driver_ng API function
    return i2c_new_master_bus(&bus_config, bus_handle);
}

static void sensor_udp_task(void *pvParameters) {
    led_strip_handle_t strip = (led_strip_handle_t)pvParameters;
    // Re-initialize I2C and sensors in this task for safety
    i2c_master_bus_handle_t i2c_bus_handle = NULL;
    if (i2c_master_bus_init_ng(&i2c_bus_handle) != ESP_OK) {
        ESP_LOGE(TAG, "I2C bus init failed");
        vTaskDelete(NULL);
    }
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
    if (ens160_init(i2c_bus_handle, &ens160_config, &ens160_handle) != ESP_OK) {
        ESP_LOGE(TAG, "ENS160: Initialization failed");
        vTaskDelete(NULL);
    }
    aht20_dev_handle_t aht20_handle = NULL;
    i2c_aht20_config_t aht20_config = {
        .i2c_config = {
            .device_address = AHT20_ADDRESS_0,
            .scl_speed_hz = I2C_MASTER_FREQ_HZ,
        },
        .i2c_timeout = 1000,
    };
    if (aht20_new_sensor(i2c_bus_handle, &aht20_config, &aht20_handle) != ESP_OK) {
        ESP_LOGE(TAG, "AHT20: Initialization failed");
        vTaskDelete(NULL);
    }
    // Get MAC address
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    char mac_id[3];
    snprintf(mac_id, sizeof(mac_id), "%02X", mac[5]);
    for (;;) {
        ens160_air_quality_data_t air_data;
        uint8_t caqi = 0;
        if (ens160_get_measurement(ens160_handle, &air_data) == ESP_OK) {
            ens160_aqi_uba_row_t aqi_def = ens160_aqi_index_to_definition(air_data.uba_aqi);
            ESP_LOGI(TAG, "ENS160: CAQI: %d (%s), TVOC: %u ppb, eCO2: %u ppm", air_data.uba_aqi, aqi_def.rating, air_data.tvoc, air_data.eco2);
            caqi = air_data.uba_aqi;
        } else {
            ESP_LOGI(TAG, "ENS160: Read error");
            caqi = 0;
        }
        uint8_t r = 0, g = 0, b = 0;
        switch (caqi) {
            case 1: r = 0; g = 255; b = 0; break;
            case 2: r = 255; g = 255; b = 0; break;
            case 3: r = 255; g = 165; b = 0; break;
            case 4: r = 128; g = 0; b = 128; break;
            case 5: r = 255; g = 0; b = 0; break;
            default: r = 0; g = 0; b = 255; break;
        }
        led_strip_clear(strip);
        led_strip_set_pixel(strip, 0, r, g, b);
        led_strip_refresh(strip);
        float temperature = 0.0f, humidity = 0.0f;
        if (aht20_read_float(aht20_handle, &temperature, &humidity) == ESP_OK) {
            ESP_LOGI(TAG, "AHT20: Temperature: %.2f C, Humidity: %.2f %%", temperature, humidity);
            if (ens160_set_compensation_factors(ens160_handle, temperature, humidity) != ESP_OK) {
                ESP_LOGI(TAG, "ENS160: Failed to set compensation factors");
            }
        } else {
            ESP_LOGI(TAG, "AHT20: Read error");
        }
        /*
        UDP packet format before sending:
        temp=<temperature>,hum=<humidity>,id=<last_mac_byte>
        Example: temp=23.45,hum=56.78,id=AB
        */
        char udp_payload[64];
        snprintf(udp_payload, sizeof(udp_payload),
            "temp=%.2f,hum=%.2f,id=%s",
            temperature, humidity, mac_id);
        udp_send_sensor_data(udp_payload);
        ESP_LOGI(TAG, "UDP sent: %s", udp_payload);
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}

void app_main() {
    vTaskDelay(pdMS_TO_TICKS(500));
    ESP_LOGI(TAG, "Starting app_main (UDP sensor sender)");
    ESP_ERROR_CHECK(nvs_flash_init());
    srand((unsigned)time(NULL));
    wifi_init_sta();
    ESP_LOGI(TAG, "WiFi initialized");
    led_strip_handle_t strip;
    led_strip_config_t strip_config = {
        .strip_gpio_num = NEOPIXEL_GPIO,
        .max_leds = NUM_PIXELS,
        .led_pixel_format = LED_PIXEL_FORMAT_GRB,
        .led_model = LED_MODEL_WS2812,
        .flags.invert_out = false,
    };
    led_strip_rmt_config_t rmt_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .resolution_hz = 10 * 1000 * 1000,
        .mem_block_symbols = 0,
        .flags.with_dma = false,
    };
    led_strip_new_rmt_device(&strip_config, &rmt_config, &strip);
    led_strip_clear(strip);
    led_strip_refresh(strip);
    xTaskCreate(sensor_udp_task, "sensor_udp_task", 4096, (void*)strip, 5, NULL);
}