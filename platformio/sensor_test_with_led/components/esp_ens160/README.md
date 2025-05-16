# ScioSense ENS160 Sensor

[![License: MIT](https://cdn.prod.website-files.com/5e0f1144930a8bc8aace526c/65dd9eb5aaca434fac4f1c34_License-MIT-blue.svg)](/LICENSE)
[![Edited with VS Code](https://badgen.net/badge/icon/VS%20Code?icon=visualstudio&label=edited%20with)](https://visualstudio.microsoft.com)
[![Build with PlatformIO](https://img.shields.io/badge/build%20with-PlatformIO-orange?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMjUwMCIgaGVpZ2h0PSIyNTAwIiB2aWV3Qm94PSIwIDAgMjU2IDI1NiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJ4TWlkWU1pZCI+PHBhdGggZD0iTTEyOCAwQzkzLjgxIDAgNjEuNjY2IDEzLjMxNCAzNy40OSAzNy40OSAxMy4zMTQgNjEuNjY2IDAgOTMuODEgMCAxMjhjMCAzNC4xOSAxMy4zMTQgNjYuMzM0IDM3LjQ5IDkwLjUxQzYxLjY2NiAyNDIuNjg2IDkzLjgxIDI1NiAxMjggMjU2YzM0LjE5IDAgNjYuMzM0LTEzLjMxNCA5MC41MS0zNy40OUMyNDIuNjg2IDE5NC4zMzQgMjU2IDE2Mi4xOSAyNTYgMTI4YzAtMzQuMTktMTMuMzE0LTY2LjMzNC0zNy40OS05MC41MUMxOTQuMzM0IDEzLjMxNCAxNjIuMTkgMCAxMjggMCIgZmlsbD0iI0ZGN0YwMCIvPjxwYXRoIGQ9Ik0yNDkuMzg2IDEyOGMwIDY3LjA0LTU0LjM0NyAxMjEuMzg2LTEyMS4zODYgMTIxLjM4NkM2MC45NiAyNDkuMzg2IDYuNjEzIDE5NS4wNCA2LjYxMyAxMjggNi42MTMgNjAuOTYgNjAuOTYgNi42MTQgMTI4IDYuNjE0YzY3LjA0IDAgMTIxLjM4NiA1NC4zNDYgMTIxLjM4NiAxMjEuMzg2IiBmaWxsPSIjRkZGIi8+PHBhdGggZD0iTTE2MC44NjkgNzQuMDYybDUuMTQ1LTE4LjUzN2M1LjI2NC0uNDcgOS4zOTItNC44ODYgOS4zOTItMTAuMjczIDAtNS43LTQuNjItMTAuMzItMTAuMzItMTAuMzJzLTEwLjMyIDQuNjItMTAuMzIgMTAuMzJjMCAzLjc1NSAyLjAxMyA3LjAzIDUuMDEgOC44MzdsLTUuMDUgMTguMTk1Yy0xNC40MzctMy42Ny0yNi42MjUtMy4zOS0yNi42MjUtMy4zOWwtMi4yNTggMS4wMXYxNDAuODcybDIuMjU4Ljc1M2MxMy42MTQgMCA3My4xNzctNDEuMTMzIDczLjMyMy04NS4yNyAwLTMxLjYyNC0yMS4wMjMtNDUuODI1LTQwLjU1NS01Mi4xOTd6TTE0Ni41MyAxNjQuOGMtMTEuNjE3LTE4LjU1Ny02LjcwNi02MS43NTEgMjMuNjQzLTY3LjkyNSA4LjMyLTEuMzMzIDE4LjUwOSA0LjEzNCAyMS41MSAxNi4yNzkgNy41ODIgMjUuNzY2LTM3LjAxNSA2MS44NDUtNDUuMTUzIDUxLjY0NnptMTguMjE2LTM5Ljc1MmE5LjM5OSA5LjM5OSAwIDAgMC05LjM5OSA5LjM5OSA5LjM5OSA5LjM5OSAwIDAgMCA5LjQgOS4zOTkgOS4zOTkgOS4zOTkgMCAwIDAgOS4zOTgtOS40IDkuMzk5IDkuMzk5IDAgMCAwLTkuMzk5LTkuMzk4em0yLjgxIDguNjcyYTIuMzc0IDIuMzc0IDAgMSAxIDAtNC43NDkgMi4zNzQgMi4zNzQgMCAwIDEgMCA0Ljc0OXoiIGZpbGw9IiNFNTcyMDAiLz48cGF0aCBkPSJNMTAxLjM3MSA3Mi43MDlsLTUuMDIzLTE4LjkwMWMyLjg3NC0xLjgzMiA0Ljc4Ni01LjA0IDQuNzg2LTguNzAxIDAtNS43LTQuNjItMTAuMzItMTAuMzItMTAuMzItNS42OTkgMC0xMC4zMTkgNC42Mi0xMC4zMTkgMTAuMzIgMCA1LjY4MiA0LjU5MiAxMC4yODkgMTAuMjY3IDEwLjMxN0w5NS44IDc0LjM3OGMtMTkuNjA5IDYuNTEtNDAuODg1IDIwLjc0Mi00MC44ODUgNTEuODguNDM2IDQ1LjAxIDU5LjU3MiA4NS4yNjcgNzMuMTg2IDg1LjI2N1Y2OC44OTJzLTEyLjI1Mi0uMDYyLTI2LjcyOSAzLjgxN3ptMTAuMzk1IDkyLjA5Yy04LjEzOCAxMC4yLTUyLjczNS0yNS44OC00NS4xNTQtNTEuNjQ1IDMuMDAyLTEyLjE0NSAxMy4xOS0xNy42MTIgMjEuNTExLTE2LjI4IDMwLjM1IDYuMTc1IDM1LjI2IDQ5LjM2OSAyMy42NDMgNjcuOTI2em0tMTguODItMzkuNDZhOS4zOTkgOS4zOTkgMCAwIDAtOS4zOTkgOS4zOTggOS4zOTkgOS4zOTkgMCAwIDAgOS40IDkuNCA5LjM5OSA5LjM5OSAwIDAgMCA5LjM5OC05LjQgOS4zOTkgOS4zOTkgMCAwIDAtOS4zOTktOS4zOTl6bS0yLjgxIDguNjcxYTIuMzc0IDIuMzc0IDAgMSAxIDAtNC43NDggMi4zNzQgMi4zNzQgMCAwIDEgMCA0Ljc0OHoiIGZpbGw9IiNGRjdGMDAiLz48L3N2Zz4=)](https://platformio.org/)
[![PlatformIO Registry](https://badges.registry.platformio.org/packages/k0i05/library/esp_ens160.svg)](https://registry.platformio.org/libraries/k0i05/esp_ens160)
[![ESP Component Registry](https://components.espressif.com/components/k0i05/esp_ens160/badge.svg)](https://components.espressif.com/components/k0i05/esp_ens160)

This ESP32 espressif IoT development framework (esp-idf) i2c peripheral driver was developed for the ScioSense ENS160 digital metal-oxide multi-gas sensor.  Information on features and functionality are documented and can be found in the `ens160.h` header file and in the `documentation` folder.

## Repository

The component is hosted on github and is located here: <https://github.com/K0I05/ESP32-S3_ESP-IDF_COMPONENTS/tree/main/components/peripherals/i2c/esp_ens160>

## General Usage

To get started, simply copy the component to your project's `components` folder and reference the `ens160.h` header file as an include.  The component includes documentation for the peripheral such as the datasheet, application notes, and/or user manual where applicable.

```text
components
└── esp_ens160
    ├── CMakeLists.txt
    ├── README.md
    ├── LICENSE
    ├── idf_component.yml
    ├── library.json
    ├── documentation
    │   └── datasheets, etc.
    ├── include
    │   └── ens160_version.h
    │   └── ens160.h
    └── ens160.c
```

## Basic Example

Once a driver instance is instantiated the sensor is ready for usage as shown in the below example.   This basic implementation of the driver utilizes default configuration settings and makes a measurement request from the sensor at user defined interval and prints the results.

```c
#include <ens160.h>

void i2c0_ens160_task( void *pvParameters ) {
    // initialize the xLastWakeTime variable with the current time.
    TickType_t          last_wake_time   = xTaskGetTickCount ();
    //
    // initialize i2c device configuration
    ens160_config_t dev_cfg          = I2C_ENS160_CONFIG_DEFAULT;
    ens160_handle_t dev_hdl;
    //
    // init device
    ens160_init(i2c0_bus_hdl, &dev_cfg, &dev_hdl);
    if (dev_hdl == NULL) {
        ESP_LOGE(APP_TAG, "ens160 handle init failed");
        assert(dev_hdl);
    }
    //
    uint16_t startup_time = 0; // seconds
    //
    // task loop entry point
    for ( ;; ) {
        ESP_LOGI(APP_TAG, "######################## ENS160 - START #########################");
        //
        // handle sensor
        ens160_validity_flags_t dev_flag;
        if(ens160_get_validity_status(dev_hdl, &dev_flag) == ESP_OK) {
            // validate device status
            if(dev_flag == ENS160_VALFLAG_NORMAL) {
                ens160_air_quality_data_t aq_data;
                esp_err_t result = ens160_get_measurement(dev_hdl, &aq_data);
                if(result != ESP_OK) {
                    ESP_LOGE(APP_TAG, "ens160 device read failed (%s)", esp_err_to_name(result));
                } else {
                    ens160_aqi_uba_row_t uba_aqi = ens160_aqi_index_to_definition(aq_data.uba_aqi);

                    ESP_LOGW(APP_TAG, "index    %1x (%s)", aq_data.uba_aqi, uba_aqi.rating);
                    ESP_LOGW(APP_TAG, "tvco     %d (0x%04x)", aq_data.tvoc, aq_data.tvoc);
                    ESP_LOGW(APP_TAG, "etoh     %d (0x%04x)", aq_data.etoh, aq_data.etoh);
                    ESP_LOGW(APP_TAG, "eco2     %d (0x%04x)", aq_data.eco2, aq_data.eco2);
                }
                //
                ens160_air_quality_raw_data_t aq_raw_data;
                result = ens160_get_raw_measurement(dev_hdl, &aq_raw_data);
                if(result != ESP_OK) {
                    ESP_LOGE(APP_TAG, "ens160 device read failed (%s)", esp_err_to_name(result));
                } else {
                    ESP_LOGW(APP_TAG, "ri-res 0 %lu", aq_raw_data.hp0_ri);
                    ESP_LOGW(APP_TAG, "ri-res 1 %lu", aq_raw_data.hp1_ri);
                    ESP_LOGW(APP_TAG, "ri-res 2 %lu", aq_raw_data.hp2_ri);
                    ESP_LOGW(APP_TAG, "ri-res 3 %lu", aq_raw_data.hp3_ri);

                    ESP_LOGW(APP_TAG, "bl-res 0 %lu", aq_raw_data.hp0_bl);
                    ESP_LOGW(APP_TAG, "bl-res 1 %lu", aq_raw_data.hp1_bl);
                    ESP_LOGW(APP_TAG, "bl-res 2 %lu", aq_raw_data.hp2_bl);
                    ESP_LOGW(APP_TAG, "bl-res 3 %lu", aq_raw_data.hp3_bl);
                }
            } else if(dev_flag == ENS160_VALFLAG_WARMUP) {
                ESP_LOGW(APP_TAG, "ens160 device is warming up (180-sec wait [%u-sec])", startup_time);
                startup_time = startup_time + I2C0_TASK_SAMPLING_RATE;
            } else if(dev_flag == ENS160_VALFLAG_INITIAL_STARTUP) {
                ESP_LOGW(APP_TAG, "ens160 device is undrgoing initial starting up (3600-sec wait [%u-sec])", startup_time);
                startup_time = startup_time + I2C0_TASK_SAMPLING_RATE;
            } else if(dev_flag == ENS160_VALFLAG_INVALID_OUTPUT) {
                ESP_LOGW(APP_TAG, "ens160 device signals are giving unexpected values");
            }
        }
        //
        ESP_LOGI(APP_TAG, "######################## ENS160 - END ###########################");
        //
        //
        // pause the task per defined wait period
        vTaskDelaySecUntil( &last_wake_time, I2C0_TASK_SAMPLING_RATE );
    }
    //
    // free resources
    ens160_delete( dev_hdl );
    vTaskDelete( NULL );
}
```

Copyright (c) 2024 Eric Gionet (<gionet.c.eric@gmail.com>)
