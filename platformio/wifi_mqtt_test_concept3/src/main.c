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
#include "mqtt_client.h"
#include "lwip/inet.h"
#include "freertos/semphr.h"
#include "esp_http_client.h" // Moved here from app_main

// WiFi configuration
#define WIFI_SSID "1"
#define WIFI_PASS "minecraft123"
#define WIFI_AUTH_MODE WIFI_AUTH_WPA2_PSK
#define WIFI_RSSI_THRESHOLD 0
#define WIFI_MODE WIFI_MODE_STA    

// MQTT configuration
// Public IP: 194.177.207.38, Private IP: 10.64.44.156
#define MQTT_BROKER_URI "mqtt://194.177.207.38"
#define MQTT_BROKER_PORT 1883
#define MY_TEAM "team19"
#define MQTT_TOPIC_PREFIX "iot/" MY_TEAM
#define MQTT_QOS 1
#define MQTT_RETAIN 0
#define PUBLISH_INTERVAL_MS 5000

// Add MQTT username and password from .env
#define MQTT_USERNAME "team19"
#define MQTT_PASSWORD "team19(@#$"

// Event group for WiFi connection
static EventGroupHandle_t s_wifi_event_group;
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1

static const char *TAG = "WIFI_MQTT";
static esp_mqtt_client_handle_t mqtt_client;
static char mqtt_topic_temp[128];
static char mqtt_topic_hum[128];

// MQTT event string representations
static const char* mqtt_event_to_str(int32_t event_id) {
    switch (event_id) {
        case MQTT_EVENT_CONNECTED: return "MQTT_EVENT_CONNECTED";
        case MQTT_EVENT_DISCONNECTED: return "MQTT_EVENT_DISCONNECTED";
        case MQTT_EVENT_SUBSCRIBED: return "MQTT_EVENT_SUBSCRIBED";
        case MQTT_EVENT_UNSUBSCRIBED: return "MQTT_EVENT_UNSUBSCRIBED";
        case MQTT_EVENT_PUBLISHED: return "MQTT_EVENT_PUBLISHED";
        case MQTT_EVENT_DATA: return "MQTT_EVENT_DATA";
        case MQTT_EVENT_ERROR: return "MQTT_EVENT_ERROR";
        default: return "UNKNOWN_EVENT";
    }
}

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

static void publish_random_measurements(void) {
    float temperature = (rand() % 3500) / 100.0f + 10.0f; // 10.00 - 44.99 C
    float humidity = (rand() % 8000) / 100.0f + 10.0f + 10.0f;    // 10.00 - 89.99 %

    char temp_str[16];
    char hum_str[16];
    snprintf(temp_str, sizeof(temp_str), "%.2f", temperature);
    snprintf(hum_str, sizeof(hum_str), "%.2f", humidity);

    ESP_LOGI(TAG, "Publishing temperature: %s to topic: %s", temp_str, mqtt_topic_temp);
    ESP_LOGI(TAG, "Publishing humidity: %s to topic: %s", hum_str, mqtt_topic_hum);
    esp_mqtt_client_publish(mqtt_client, mqtt_topic_temp, temp_str, 0, MQTT_QOS, MQTT_RETAIN);
    esp_mqtt_client_publish(mqtt_client, mqtt_topic_hum, hum_str, 0, MQTT_QOS, MQTT_RETAIN);

    ESP_LOGI(TAG, "Temperature: %s °C", temp_str);
    ESP_LOGI(TAG, "Humidity: %s %%", hum_str);
}

static void periodic_publish_task(void *pvParameters) {
    ESP_LOGI(TAG, "Starting periodic publish task");
    //remove while 1 if possible
    while (1) {
        ESP_LOGI(TAG, "Publishing new measurements...");
        publish_random_measurements(); //////
        ESP_LOGI(TAG, "Sleeping for %d ms", PUBLISH_INTERVAL_MS);
        vTaskDelay(pdMS_TO_TICKS(PUBLISH_INTERVAL_MS));
    }
}

static void mqtt_event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data) {
    ESP_LOGI(TAG, "MQTT event: %s (%ld)", mqtt_event_to_str(event_id), event_id);
    if (event_id == MQTT_EVENT_CONNECTED) {
        ESP_LOGI(TAG, "MQTT connected, starting periodic publish task");
        xTaskCreate(periodic_publish_task, "periodic_publish_task", 4096, NULL, 5, NULL);
    } else if (event_id == MQTT_EVENT_DISCONNECTED) {
        ESP_LOGI(TAG, "MQTT disconnected");
    }
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
            .threshold.authmode = WIFI_AUTH_MODE,
            .threshold.rssi = WIFI_RSSI_THRESHOLD,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT, pdFALSE, pdFALSE, portMAX_DELAY);
    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "Connected to WiFi: %s", WIFI_SSID);
    } else {
        ESP_LOGE(TAG, "WiFi connection failed");
    }
}

static void mqtt_app_start(void) {
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = MQTT_BROKER_URI,
        .broker.address.port = MQTT_BROKER_PORT,
        .credentials.username = MQTT_USERNAME,
        .credentials.authentication.password = MQTT_PASSWORD,
    };
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(mqtt_client);
}

// Helper function to print local (private) IP
static void print_local_ip(void) {
    esp_netif_ip_info_t ip_info;
    esp_netif_t *netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
    if (netif && esp_netif_get_ip_info(netif, &ip_info) == ESP_OK) {
        ESP_LOGI(TAG, "Local IP: " IPSTR, IP2STR(&ip_info.ip));
    } else {
        ESP_LOGI(TAG, "Local IP: Not available");
    }
}

// Helper function to print public IP
static void print_public_ip(void) {
    char public_ip[64] = "Unknown";
    esp_http_client_config_t config = {
        .url = "http://api.ipify.org",
        .timeout_ms = 3000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&config);
    esp_err_t open_err = esp_http_client_open(client, 0);
    if (open_err == ESP_OK) {
        int content_length = esp_http_client_fetch_headers(client);
        int read_len;
        if (content_length > 0 && content_length < sizeof(public_ip)) {
            read_len = esp_http_client_read(client, public_ip, content_length);
        } else {
            read_len = esp_http_client_read(client, public_ip, sizeof(public_ip) - 1);
        }
        if (read_len > 0) {
            public_ip[read_len] = '\0';
            ESP_LOGI(TAG, "Public IP: %s", public_ip);
        } else {
            ESP_LOGI(TAG, "Online: Failed to read public IP");
        }
    } else {
        ESP_LOGI(TAG, "No internet connection");
    }
    esp_http_client_cleanup(client);
}

// Print WiFi status: SSID and RSSI periodically
static void wifi_status_task(void *pvParameters) {
    while (1) {
        wifi_ap_record_t ap_info;
        if (esp_wifi_sta_get_ap_info(&ap_info) == ESP_OK) {
            char ssid[33] = {0};
            strncpy(ssid, (const char*)ap_info.ssid, sizeof(ssid) - 1);
            ESP_LOGI(TAG, "WiFi Status: CONNECTED | SSID: %s | RSSI: %d", ssid, ap_info.rssi);
        } else {
            ESP_LOGI(TAG, "WiFi Status: NOT CONNECTED");
        }
        print_local_ip();
        print_public_ip();
        vTaskDelay(pdMS_TO_TICKS(10000)); // Print every 10 seconds
    }
}

void app_main() {
    vTaskDelay(pdMS_TO_TICKS(500)); // Wait 500ms before any log prints
    ESP_LOGI(TAG, "MQTT Broker URI: %s", MQTT_BROKER_URI);
    ESP_LOGI(TAG, "Starting app_main");
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_LOGI(TAG, "NVS flash initialized");
    srand((unsigned)time(NULL));
    ESP_LOGI(TAG, "Random seed set");
    wifi_init_sta();
    ESP_LOGI(TAG, "WiFi initialized");

    // Start periodic WiFi status task
    xTaskCreate(wifi_status_task, "wifi_status_task", 4096, NULL, 3, NULL);

    uint8_t mac[6];
    ESP_ERROR_CHECK(esp_wifi_get_mac(WIFI_IF_STA, mac));
    ESP_LOGI(TAG, "Device MAC: %02X:%02X:%02X:%02X:%02X:%02X", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    snprintf(mqtt_topic_temp, sizeof(mqtt_topic_temp), MQTT_TOPIC_PREFIX "/airTemperature");
    snprintf(mqtt_topic_hum, sizeof(mqtt_topic_hum), MQTT_TOPIC_PREFIX "/airHumidity");
    ESP_LOGI(TAG, "MQTT topics: %s, %s", mqtt_topic_temp, mqtt_topic_hum);
    mqtt_app_start();
    ESP_LOGI(TAG, "MQTT client started");
}