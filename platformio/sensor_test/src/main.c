// ESP-IDF version: This project is built using ESP-IDF v5.0.
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2c_master.h"
#include "ens160.h"

// I2C configuration for driver_ng
#define I2C_MASTER_SCL_IO           9
#define I2C_MASTER_SDA_IO           8
#define I2C_MASTER_PORT             0
#define I2C_MASTER_FREQ_HZ          100000

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

void app_main() {
    i2c_master_bus_handle_t i2c_bus_handle = NULL;
    if (i2c_master_bus_init_ng(&i2c_bus_handle) != ESP_OK) {
        printf("I2C bus init failed\n");
    }

    // --- ENS160 device setup (driver_ng) ---
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
        printf("ENS160: Initialization failed\n");
    }

    while (1) {
        // Read ENS160 sensor
        ens160_air_quality_data_t air_data;
        if (ens160_get_measurement(ens160_handle, &air_data) == ESP_OK) {
            // Print all requested data fields
            printf("ENS160: CAQI: %d, TVOC: %u ppb, EtOH: %u ppb, eCO2: %u ppm\n",
                air_data.uba_aqi,      // CAQI register (UBA AQI index)
                air_data.tvoc,         // TVOC data
                air_data.etoh,         // EtOH data
                air_data.eco2          // eCO2 data
            );
        } else {
            printf("ENS160: Read error\n");
        }

        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}