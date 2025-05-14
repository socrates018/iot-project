/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2024 Eric Gionet (gionet.c.eric@gmail.com)
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/**
 * @file ens160.c
 *
 * ESP-IDF driver for ENS160 Air Quality sensor
 *
 * Ported from esp-open-rtos
 *
 * Copyright (c) 2024 Eric Gionet (gionet.c.eric@gmail.com)
 *
 * MIT Licensed as described in the file LICENSE
 */
#include "include/ens160.h"
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <esp_log.h>
#include <esp_check.h>
#include <esp_timer.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>


#define ENS160_REG_PART_ID_R            UINT8_C(0x00) //!< ens160 I2C part identifier (default id: 0x01, 0x60)
#define ENS160_REG_OPMODE_RW            UINT8_C(0x10) //!< ens160 I2C operating mode
#define ENS160_REG_INT_CONFIG_RW        UINT8_C(0x11) //!< ens160 I2C interrupt pin configuration
#define ENS160_REG_COMMAND_RW           UINT8_C(0x12) //!< ens160 I2C additional system commands
#define ENS160_REG_TEMP_IN_RW           UINT8_C(0x13) //!< ens160 I2C host ambient temperature information
#define ENS160_REG_RH_IN_RW             UINT8_C(0x15) //!< ens160 I2C host relative humidity information
#define ENS160_REG_DEVICE_STATUS_R      UINT8_C(0x20) //!< ens160 I2C operating status
#define ENS160_REG_DATA_AQI_R           UINT8_C(0x21) //!< ens160 I2C air quality index
#define ENS160_REG_DATA_TVOC_R          UINT8_C(0x22) //!< ens160 I2C TVOC concentration (ppb)
#define ENS160_REG_DATA_ETOH_R          UINT8_C(0x22) //!< ens160 I2C ETOH concentration (ppb)
#define ENS160_REG_DATA_ECO2_R          UINT8_C(0x24) //!< ens160 I2C equivalent CO2 concentration (ppm)
#define ENS160_REG_DATA_BL_R            UINT8_C(0x28) //!< ens160 I2C baseline information
#define ENS160_REG_DATA_TEMP_R          UINT8_C(0x30) //!< ens160 I2C temperature used in calculations
#define ENS160_REG_DATA_RH_R            UINT8_C(0x32) //!< ens160 I2C relative humidity used in calculations
#define ENS160_REG_DATA_MISR_R          UINT8_C(0x38) //!< ens160 I2C data integrity field
#define ENS160_REG_GPR_WRITE0_RW        UINT8_C(0x40) //!< ens160 I2C general purpose write0 register
#define ENS160_REG_GPR_WRITE1_RW        UINT8_C(0x41) //!< ens160 I2C general purpose write1 register
#define ENS160_REG_GPR_WRITE2_RW        UINT8_C(0x42) //!< ens160 I2C general purpose write2 register
#define ENS160_REG_GPR_WRITE3_RW        UINT8_C(0x43) //!< ens160 I2C general purpose write3 register
#define ENS160_REG_GPR_WRITE4_RW        UINT8_C(0x44) //!< ens160 I2C general purpose write4 register
#define ENS160_REG_GPR_WRITE5_RW        UINT8_C(0x45) //!< ens160 I2C general purpose write5 register
#define ENS160_REG_GPR_WRITE6_RW        UINT8_C(0x46) //!< ens160 I2C general purpose write6 register
#define ENS160_REG_GPR_WRITE7_RW        UINT8_C(0x47) //!< ens160 I2C general purpose write7 register
#define ENS160_REG_GPR_READ0_R          UINT8_C(0x48) //!< ens160 I2C general purpose read0 register
#define ENS160_REG_GPR_READ1_R          UINT8_C(0x49) //!< ens160 I2C general purpose read1 register
#define ENS160_REG_GPR_READ2_R          UINT8_C(0x4a) //!< ens160 I2C general purpose read2 register
#define ENS160_REG_GPR_READ3_R          UINT8_C(0x4b) //!< ens160 I2C general purpose read3 register
#define ENS160_REG_GPR_READ4_R          UINT8_C(0x4c) //!< ens160 I2C general purpose read4 register
#define ENS160_REG_GPR_READ5_R          UINT8_C(0x4d) //!< ens160 I2C general purpose read5 register
#define ENS160_REG_GPR_READ6_R          UINT8_C(0x4e) //!< ens160 I2C general purpose read6 register
#define ENS160_REG_GPR_READ7_R          UINT8_C(0x4f) //!< ens160 I2C general purpose read7 register

#define ENS160_TEMPERATURE_MAX         (float)(125.0)  //!< ens160 maximum temperature range
#define ENS160_TEMPERATURE_MIN         (float)(-40.0)  //!< ens160 minimum temperature range
#define ENS160_HUMIDITY_MAX            (float)(100.0)  //!< ens160 maximum humidity range
#define ENS160_HUMIDITY_MIN            (float)(0.0)    //!< ens160 minimum humidity range

#define ENS160_POWERUP_DELAY_MS         UINT16_C(15)            //!< ens160 50ms delay before making i2c transactions
#define ENS160_APPSTART_DELAY_MS        UINT16_C(25)            //!< ens160 25ms delay before making a measurement
#define ENS160_CMD_DELAY_MS             UINT16_C(5)             //!< ens160 5ms delay before making the next i2c transaction
#define ENS160_MODE_DELAY_MS            UINT16_C(10)            //!< ens160 10ms delay when updating the operating mode
#define ENS160_RESET_DELAY_MS           UINT16_C(50)            //!< ens160 50ms delay when resetting the device
#define ENS160_CLEAR_GPR_DELAY_MS       UINT16_C(10)            //!< ens160 10ms delay when clearing general purpose registers
#define ENS160_DATA_READY_DELAY_MS      UINT16_C(1)             //!< ens160 1ms delay when checking data ready in a loop
#define ENS160_DATA_POLL_TIMEOUT_MS     UINT16_C(1500)          //!< ens160 1.5s timeout when making a measurement
#define ENS160_TX_RX_DELAY_MS           UINT16_C(10)

/*
 * macro definitions
*/
#define ENS160_CONVERT_RS_RAW2OHMS_F(x) 	(pow (2, (float)(x) / 2048))
#define ESP_TIMEOUT_CHECK(start, len) ((uint64_t)(esp_timer_get_time() - (start)) >= (len))
#define ESP_ARG_CHECK(VAL) do { if (!(VAL)) return ESP_ERR_INVALID_ARG; } while (0)

/*
* static constant declarations
*/
static const char *TAG = "ens160";


/**
 * @brief ENS160 air quality index of the UBA definition table structure.
 */
static const struct ens160_aqi_uba_row_s ens160_aqi_uba_definition_table[ENS160_ERROR_MSG_TABLE_SIZE] = {
  {ENS160_AQI_UBA_INDEX_UNKNOWN,    "-", "-", "-", "-"},
  {ENS160_AQI_UBA_INDEX_1,          "Excellent",    "No objections",            "Target", "no limit"},
  {ENS160_AQI_UBA_INDEX_2,          "Good",         "No relevant objections",   "Sufficient ventilation recommended", "no limit"},
  {ENS160_AQI_UBA_INDEX_3,          "Moderate",     "Some objections",          "Increased ventilation recommended, search for sources", "<12 months"},
  {ENS160_AQI_UBA_INDEX_4,          "Poor",         "Major objections",         "Intensified ventilation recommended, search for sources", "<1 month"},
  {ENS160_AQI_UBA_INDEX_5,          "Unhealthy",    "Situation not acceptable", "Use only if unavoidable, intensified ventilation recommended", "hours"}
};

/*
* functions and subroutines
*/

/**
 * @brief Get air quality (uba) index.
 */
static inline ens160_aqi_uba_indexes_t ens160_get_aqi_uba_index(const ens160_caqi_data_register_t reg) {
    switch(reg.bits.aqi_uba) {
        case 1: return ENS160_AQI_UBA_INDEX_1;
        case 2: return ENS160_AQI_UBA_INDEX_2;
        case 3: return ENS160_AQI_UBA_INDEX_3;
        case 4: return ENS160_AQI_UBA_INDEX_4;
        case 5: return ENS160_AQI_UBA_INDEX_5;
        default:
            return ENS160_AQI_UBA_INDEX_UNKNOWN;
    }
}

/**
 * @brief ENS160 I2C write byte to register address transaction.
 * 
 * @param handle ENS160 device handle.
 * @param reg_addr ENS160 register address to write to.
 * @param byte ENS160 write transaction input byte.
 * @return esp_err_t ESP_OK on success.
 */
static inline esp_err_t ens160_i2c_write_byte_to(ens160_handle_t handle, const uint8_t reg_addr, const uint8_t byte) {
    const bit16_uint8_buffer_t tx = { reg_addr, byte };

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c write transaction */
    ESP_RETURN_ON_ERROR( i2c_master_transmit(handle->i2c_handle, tx, BIT16_UINT8_BUFFER_SIZE, I2C_XFR_TIMEOUT_MS), TAG, "i2c_master_transmit, i2c write failed" );
                        
    return ESP_OK;
}

/**
 * @brief ENS160 I2C write halfword to register address transaction.
 * 
 * @param handle ENS160 device handle.
 * @param reg_addr ENS160 register address to write to.
 * @param word ENS160 write transaction input halfword.
 * @return esp_err_t ESP_OK on success.
 */
static inline esp_err_t ens160_i2c_write_word_to(ens160_handle_t handle, const uint8_t reg_addr, const uint16_t word) {
    const bit24_uint8_buffer_t tx = { reg_addr, (uint8_t)(word & 0xff), (uint8_t)((word >> 8) & 0xff) };

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c write transaction */
    ESP_RETURN_ON_ERROR( i2c_master_transmit(handle->i2c_handle, tx, BIT24_UINT8_BUFFER_SIZE, I2C_XFR_TIMEOUT_MS), TAG, "i2c_master_transmit, i2c write failed" );
                        
    return ESP_OK;
}

/**
 * @brief ENS160 I2C read from register address transaction.  This is a write and then read process.
 * 
 * @param handle ENS160 device handle.
 * @param reg_addr ENS160 register address to read from.
 * @param buffer ENS160 read transaction return buffer.
 * @param size Length of buffer to store results from read transaction.
 * @return esp_err_t ESP_OK on success.
 */
static inline esp_err_t ens160_i2c_read_from(ens160_handle_t handle, const uint8_t reg_addr, uint8_t *buffer, const uint8_t size) {
    const bit8_uint8_buffer_t tx = { reg_addr };

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    ESP_RETURN_ON_ERROR( i2c_master_transmit_receive(handle->i2c_handle, tx, BIT8_UINT8_BUFFER_SIZE, buffer, size, I2C_XFR_TIMEOUT_MS), TAG, "ens160_i2c_read_from failed" );

    return ESP_OK;
}

/**
 * @brief ENS160 I2C read halfword from register address transaction.
 * 
 * @param handle ENS160 device handle.
 * @param reg_addr ENS160 register address to read from.
 * @param word ENS160 read transaction return halfword.
 * @return esp_err_t ESP_OK on success.
 */
static inline esp_err_t ens160_i2c_read_word_from(ens160_handle_t handle, const uint8_t reg_addr, uint16_t *const word) {
    const bit8_uint8_buffer_t tx = { reg_addr };
    bit16_uint8_buffer_t rx = { 0 };

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    ESP_RETURN_ON_ERROR( i2c_master_transmit_receive(handle->i2c_handle, tx, BIT8_UINT8_BUFFER_SIZE, rx, BIT16_UINT8_BUFFER_SIZE, I2C_XFR_TIMEOUT_MS), TAG, "ens160_i2c_read_word_from failed" );

    /* set output parameter */
    *word = (uint16_t)rx[0] | ((uint16_t)rx[1] << 8);

    return ESP_OK;
}

/**
 * @brief ENS160 I2C read byte from register address transaction.
 * 
 * @param handle ENS160 device handle.
 * @param reg_addr ENS160 register address to read from.
 * @param byte ENS160 read transaction return byte.
 * @return esp_err_t ESP_OK on success.
 */
static inline esp_err_t ens160_i2c_read_byte_from(ens160_handle_t handle, const uint8_t reg_addr, uint8_t *const byte) {
    const bit8_uint8_buffer_t tx = { reg_addr };
    bit8_uint8_buffer_t rx = { 0 };

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    ESP_RETURN_ON_ERROR( i2c_master_transmit_receive(handle->i2c_handle, tx, BIT8_UINT8_BUFFER_SIZE, rx, BIT8_UINT8_BUFFER_SIZE, I2C_XFR_TIMEOUT_MS), TAG, "ens160_i2c_read_byte_from failed" );

    /* set output parameter */
    *byte = rx[0];

    return ESP_OK;
}

/**
 * @brief Decodes `uint16_t` temperature format to degrees Celsius.
 * 
 * @param[in] encoded_temperature compensation temperature from register.
 * @return float temperature compensation in degrees Celsius.
 */
static inline float ens160_decode_temperature(const uint16_t encoded_temperature) {
    return (float)((encoded_temperature / 64) - 273.15);
}

/**
 * @brief Encodes temperature in degrees Celsius to `uint16_t` format.
 * 
 * @param[in] decoded_temperature compensation temperature in degrees Celsius.
 * @return uint16_t temperature compensation.
 */
static inline uint16_t ens160_encode_temperature(const float decoded_temperature) {
    return (uint16_t)((decoded_temperature + 273.15) * 64);
}

/**
 * @brief Decodes `uint16_t` humidity format.
 * 
 * @param[in] encoded_humidity compensation humidity from register.
 * @return float humidity compensation.
 */
static inline float ens160_decode_humidity(const uint16_t encoded_humidity) {
    return (float)(encoded_humidity / 512);
}

/**
 * @brief Encodes humidity to `uint16_t` format.
 * 
 * @param[in] decoded_humidity compensation humidity.
 * @return uint16_t humidity compensation.
 */
static inline uint16_t ens160_encode_humidity(const float decoded_humidity) {
    return (uint16_t)(decoded_humidity * 512);
}

/**
 * @brief Reads command from ENS160 command register.
 * 
 * @param handle ENS160 device handle.
 * @param command Command returned from ENS160 command register.
 * @return esp_err_t ESP_OK on success.
 */
static inline esp_err_t ens160_get_command(ens160_handle_t handle, ens160_commands_t *const command) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c read transaction */
    ESP_RETURN_ON_ERROR( ens160_i2c_read_byte_from(handle, ENS160_REG_COMMAND_RW, (uint8_t*)command), TAG, "read command register failed" );

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK;
}

/**
 * @brief Writes command to ENS160 command register.
 * 
 * @param handle ENS160 device handle.
 * @param command ENS160 command for command register.
 * @return esp_err_t ESP_OK on success.
 */
static inline esp_err_t ens160_set_command(ens160_handle_t handle, const ens160_commands_t command) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c write transaction */
    ESP_RETURN_ON_ERROR( ens160_i2c_write_byte_to(handle, ENS160_REG_COMMAND_RW, command), TAG, "write command register failed" );

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK;
}

/**
 * @brief Reads operating mode register from ENS160.
 * 
 * @param[in] handle ENS160 device handle.
 * @return esp_err_t ESP_OK on success.
 */
static inline esp_err_t ens160_get_mode_register(ens160_handle_t handle, ens160_operating_modes_t *const mode) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c read transaction */
    ESP_RETURN_ON_ERROR( ens160_i2c_read_byte_from(handle, ENS160_REG_OPMODE_RW, (uint8_t*)mode), TAG, "read operating mode register for get mode failed" );

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_MODE_DELAY_MS));

    return ESP_OK;
}

/**
 * @brief Writes operating mode register to ENS160.
 * 
 * @param[in] handle ENS160 device handle.
 * @param[in] mode Operating mode register setting.
 * @return esp_err_t ESP_OK on success.
 */
static inline esp_err_t ens160_set_mode_register(ens160_handle_t handle, const ens160_operating_modes_t mode) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c write transaction */
    ESP_RETURN_ON_ERROR( ens160_i2c_write_byte_to(handle, ENS160_REG_OPMODE_RW, mode), TAG, "write operating mode register for set mode failed" );

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_MODE_DELAY_MS));

    return ESP_OK;
}

esp_err_t ens160_get_interrupt_config_register(ens160_handle_t handle, ens160_interrupt_config_register_t *const reg) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c read transaction */
    ESP_RETURN_ON_ERROR( ens160_i2c_read_byte_from(handle, ENS160_REG_INT_CONFIG_RW, &reg->reg), TAG, "read interrupt configuration register failed" );
    
    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK;
}

esp_err_t ens160_set_interrupt_config_register(ens160_handle_t handle, const ens160_interrupt_config_register_t reg) {
   /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* set interrupt configuration register reserved fields to 0 */
    ens160_interrupt_config_register_t irq_config = { .reg = reg.reg };
    irq_config.bits.reserved1 = 0;
    irq_config.bits.reserved2 = 0;
    irq_config.bits.reserved3 = 0;

    /* attempt i2c write transaction */
    ESP_RETURN_ON_ERROR( ens160_i2c_write_byte_to(handle, ENS160_REG_INT_CONFIG_RW, irq_config.reg), TAG, "write interrupt configuration register failed" );

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK; 
}

esp_err_t ens160_get_status_register(ens160_handle_t handle, ens160_status_register_t *const reg) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c read transaction */
    ESP_RETURN_ON_ERROR( ens160_i2c_read_byte_from(handle, ENS160_REG_DEVICE_STATUS_R, &reg->reg), TAG, "read device status register failed" );
    
    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK;
}

esp_err_t ens160_clear_general_purpose_registers(ens160_handle_t handle) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to set normal operation command */
    ESP_RETURN_ON_ERROR( ens160_set_command(handle, ENS160_CMD_NORMAL), TAG, "write normal operation command failed" );
    
    /* attempt to set clear general purpose registers command */
    ESP_RETURN_ON_ERROR( ens160_set_command(handle, ENS160_CMD_CLEAR_GPR), TAG, "write clear general purpose registers command failed" );

    /* delay task before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CLEAR_GPR_DELAY_MS));

    /* attempt to set normal operation command */
    ESP_RETURN_ON_ERROR( ens160_set_command(handle, ENS160_CMD_NORMAL), TAG, "write normal operation command failed" );

    return ESP_OK;
}

esp_err_t ens160_get_compensation_registers(ens160_handle_t handle, float *const temperature, float *const humidity) {
    uint16_t t; uint16_t h;

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c temperature & humidity compensation read transactions */
    ESP_RETURN_ON_ERROR( ens160_i2c_read_word_from(handle, ENS160_REG_TEMP_IN_RW, &t), TAG, "read temperature compensation register failed" );
    ESP_RETURN_ON_ERROR( ens160_i2c_read_word_from(handle, ENS160_REG_RH_IN_RW, &h), TAG, "read humidity compensation register failed" );

    /* decode temperature & humidity compensation and set handle parameters */
    *temperature = ens160_decode_temperature(t);
    *humidity    = ens160_decode_humidity(h);

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK;
}

esp_err_t ens160_set_compensation_registers(ens160_handle_t handle, const float temperature, const float humidity) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* validate temperature argument */
    if(temperature > ENS160_TEMPERATURE_MAX || temperature < ENS160_TEMPERATURE_MIN) {
        ESP_RETURN_ON_FALSE( false, ESP_ERR_INVALID_ARG, TAG, "temperature is out of range, write compensation registers failed");
    }

    /* validate humidity argument */
    if(humidity > ENS160_HUMIDITY_MAX || humidity < ENS160_HUMIDITY_MIN) {
        ESP_RETURN_ON_FALSE( false, ESP_ERR_INVALID_ARG, TAG, "humidity is out of range, write compensation registers failed");
    }

    /* encode temperature & humidity compensation */
    uint16_t t = ens160_encode_temperature(temperature); 
    uint16_t h = ens160_encode_humidity(humidity);

    /* attempt i2c temperature & humidity compensation write transactions */
    ESP_RETURN_ON_ERROR( ens160_i2c_write_word_to(handle, ENS160_REG_TEMP_IN_RW, t), TAG, "write temperature compensation register failed" );
    ESP_RETURN_ON_ERROR( ens160_i2c_write_word_to(handle, ENS160_REG_RH_IN_RW, h), TAG, "write humidity compensation register failed" );

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK;
}

esp_err_t ens160_get_part_id_register(ens160_handle_t handle, uint16_t *const reg) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt i2c read transaction */
    ESP_RETURN_ON_ERROR( ens160_i2c_read_word_from(handle, ENS160_REG_PART_ID_R, reg), TAG, "read part identifier register failed" );
    
    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK;
}

esp_err_t ens160_init(i2c_master_bus_handle_t master_handle, const ens160_config_t *ens160_config, ens160_handle_t *ens160_handle) {
    /* validate arguments */
    ESP_ARG_CHECK( master_handle && ens160_config );

    /* power-up task delay */
    vTaskDelay(pdMS_TO_TICKS(ENS160_POWERUP_DELAY_MS));

    /* validate device exists on the master bus */
    esp_err_t ret = i2c_master_probe(master_handle, ens160_config->i2c_address, I2C_XFR_TIMEOUT_MS);
    ESP_GOTO_ON_ERROR(ret, err, TAG, "device does not exist at address 0x%02x, ens160 device handle initialization failed", ens160_config->i2c_address);

    /* validate memory availability for handle */
    ens160_handle_t out_handle;
    out_handle = (ens160_handle_t)calloc(1, sizeof(*out_handle));
    ESP_GOTO_ON_FALSE(out_handle, ESP_ERR_NO_MEM, err, TAG, "no memory for i2c ens160 device, init failed");

    /* copy configuration */
    out_handle->dev_config = *ens160_config;

    /* set device configuration */
    const i2c_device_config_t i2c_dev_conf = {
        .dev_addr_length    = I2C_ADDR_BIT_LEN_7,
        .device_address     = out_handle->dev_config.i2c_address,
        .scl_speed_hz       = out_handle->dev_config.i2c_clock_speed,
    };

    /* validate device handle */
    if (out_handle->i2c_handle == NULL) {
        ESP_GOTO_ON_ERROR(i2c_master_bus_add_device(master_handle, &i2c_dev_conf, &out_handle->i2c_handle), err_handle, TAG, "i2c new bus for init failed");
    }

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    /* attempt to reset device and initialize device configuration and handle */
    ESP_GOTO_ON_ERROR( ens160_reset(out_handle), err_handle, TAG, "soft-reset for init failed" );

    /* attempt to read part identifier */
    ESP_GOTO_ON_ERROR( ens160_get_part_id_register(out_handle, &out_handle->part_id), err_handle, TAG, "read part identifier register failed" );

    /* set device handle */
    *ens160_handle = out_handle;

    /* app-start task delay  */
    vTaskDelay(pdMS_TO_TICKS(ENS160_APPSTART_DELAY_MS));

    return ESP_OK;

    err_handle:
        if (out_handle && out_handle->i2c_handle) {
            i2c_master_bus_rm_device(out_handle->i2c_handle);
        }
        free(out_handle);
    err:
        return ret;
}

esp_err_t ens160_get_measurement(ens160_handle_t handle, ens160_air_quality_data_t *const data) {
    esp_err_t                       ret             = ESP_OK;
    uint64_t                        start_time      = 0;
    bool                            data_is_ready   = false;
    ens160_caqi_data_register_t     caqi_reg;
    uint16_t                        tvoc_data;
    uint16_t                        etoh_data;
    uint16_t                        eco2_data;

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* set start time (us) for timeout monitoring */
    start_time = esp_timer_get_time(); 

    /* attempt to poll until data is available or timeout */
    do {
        /* attempt to poll if data is ready or timeout */
        ESP_GOTO_ON_ERROR( ens160_get_data_status(handle, &data_is_ready), err, TAG, "data ready read for measurement failed." );

        /* delay task before next i2c transaction */
        vTaskDelay(pdMS_TO_TICKS(ENS160_DATA_READY_DELAY_MS));

        /* validate timeout condition */
        if (ESP_TIMEOUT_CHECK(start_time, (ENS160_DATA_POLL_TIMEOUT_MS * 1000)))
            return ESP_ERR_TIMEOUT;
    } while (data_is_ready == false);

    /* attempt i2c data read transactions */
    ESP_GOTO_ON_ERROR( ens160_i2c_read_byte_from(handle, ENS160_REG_DATA_AQI_R, &caqi_reg.value), err, TAG, "read calculated air quality index data register for measurement failed" );
    ESP_GOTO_ON_ERROR( ens160_i2c_read_word_from(handle, ENS160_REG_DATA_TVOC_R, &tvoc_data), err, TAG, "read tvoc data register for measurement failed" );
    ESP_GOTO_ON_ERROR( ens160_i2c_read_word_from(handle, ENS160_REG_DATA_ETOH_R, &etoh_data), err, TAG, "read etoh data register for measurement failed" );
    ESP_GOTO_ON_ERROR( ens160_i2c_read_word_from(handle, ENS160_REG_DATA_ECO2_R, &eco2_data), err, TAG, "read eco2 data register for measurement failed" );

    /* set air quality fields */
    data->uba_aqi = ens160_get_aqi_uba_index(caqi_reg);
    data->tvoc    = tvoc_data;
    data->etoh    = etoh_data;
    data->eco2    = eco2_data;

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK;

    err:
        return ret;
}

esp_err_t ens160_get_raw_measurement(ens160_handle_t handle, ens160_air_quality_raw_data_t *const data) {
    esp_err_t       ret                 = ESP_OK;
    uint64_t        start_time          = 0;
    bool            gpr_data_is_ready   = false;
    bit64_uint8_buffer_t rx             = { 0 };

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* set start time (us) for timeout monitoring */
    start_time = esp_timer_get_time(); 

    /* attempt to poll until gpr data is available or timeout */
    do {
        /* attempt to check if gpr data is ready */
        ESP_GOTO_ON_ERROR( ens160_get_gpr_data_status(handle, &gpr_data_is_ready), err, TAG, "gpr data ready read for raw measurement failed." );

        /* delay task before next i2c transaction */
        vTaskDelay(pdMS_TO_TICKS(ENS160_DATA_READY_DELAY_MS));

        /* validate timeout condition */
        if (ESP_TIMEOUT_CHECK(start_time, (ENS160_DATA_POLL_TIMEOUT_MS * 1000)))
            return ESP_ERR_TIMEOUT;
    } while (gpr_data_is_ready == false);

    /* attempt i2c gpr data read transactions */
    ESP_GOTO_ON_ERROR( ens160_i2c_read_from(handle, ENS160_REG_GPR_READ0_R, rx, BIT64_UINT8_BUFFER_SIZE), err, TAG, "read resistance signal gpr data registers for raw measurement failed" );

    /* convert gpr raw resistance and set resistance signals */
    data->hp0_ri = ENS160_CONVERT_RS_RAW2OHMS_F((uint32_t)(rx[0] | ((uint16_t)rx[1] << 8)));
    data->hp1_ri = ENS160_CONVERT_RS_RAW2OHMS_F((uint32_t)(rx[2] | ((uint16_t)rx[3] << 8)));
    data->hp2_ri = ENS160_CONVERT_RS_RAW2OHMS_F((uint32_t)(rx[4] | ((uint16_t)rx[5] << 8)));
    data->hp3_ri = ENS160_CONVERT_RS_RAW2OHMS_F((uint32_t)(rx[6] | ((uint16_t)rx[7] << 8)));

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    /* attempt i2c baseline data read transactions */
    ESP_GOTO_ON_ERROR( ens160_i2c_read_from(handle, ENS160_REG_DATA_BL_R, rx, BIT64_UINT8_BUFFER_SIZE), err, TAG, "read baseline resistance data registers for raw measurement failed" );

    /* convert baseline raw resistance and set resistance signals */
    data->hp0_bl = ENS160_CONVERT_RS_RAW2OHMS_F((uint32_t)(rx[0] | ((uint16_t)rx[1] << 8)));
    data->hp1_bl = ENS160_CONVERT_RS_RAW2OHMS_F((uint32_t)(rx[2] | ((uint16_t)rx[3] << 8)));
    data->hp2_bl = ENS160_CONVERT_RS_RAW2OHMS_F((uint32_t)(rx[4] | ((uint16_t)rx[5] << 8)));
    data->hp3_bl = ENS160_CONVERT_RS_RAW2OHMS_F((uint32_t)(rx[6] | ((uint16_t)rx[7] << 8)));

    /* attempt to clear general purpose registers */
    //ESP_GOTO_ON_ERROR( ens160_clear_general_purpose_registers(ens160_handle), err, TAG, "clear general purpose registers failed" );

    /* delay before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_CMD_DELAY_MS));

    return ESP_OK;

    err:
        return ret;
}

esp_err_t ens160_get_data_status(ens160_handle_t handle, bool *const ready) {
    ens160_status_register_t status;

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to read status register  */
    ESP_RETURN_ON_ERROR( ens160_get_status_register(handle, &status), TAG, "read status register for get data status failed" );

    /* set ready state */
    *ready = status.bits.new_data;

    return ESP_OK;
}

esp_err_t ens160_get_gpr_data_status(ens160_handle_t handle, bool *const ready) {
    ens160_status_register_t status;

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to read status register  */
    ESP_RETURN_ON_ERROR( ens160_get_status_register(handle, &status), TAG, "read status register for get general purpose registers data status failed" );

    /* set ready state */
    *ready = status.bits.new_gpr_data;

    return ESP_OK;
}

esp_err_t ens160_get_validity_status(ens160_handle_t handle, ens160_validity_flags_t *const state) {
    ens160_status_register_t status;

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to read status register  */
    ESP_RETURN_ON_ERROR( ens160_get_status_register(handle, &status), TAG, "read status register for get validity flag status failed" );

    /* set validity flag state */
    *state = status.bits.state;

    return ESP_OK;
}

esp_err_t ens160_get_error_status(ens160_handle_t handle, bool *const error) {
    ens160_status_register_t status;

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to read status register  */
    ESP_RETURN_ON_ERROR( ens160_get_status_register(handle, &status), TAG, "read status register for get error status failed" );

    /* set error state */
    *error = status.bits.error;

    return ESP_OK;
}

esp_err_t ens160_get_mode_status(ens160_handle_t handle, bool *const mode) {
    ens160_status_register_t status;

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to read status register  */
    ESP_RETURN_ON_ERROR( ens160_get_status_register(handle, &status), TAG, "read status register for get operating mode status failed" );

    /* set error state */
    *mode = status.bits.mode;

    return ESP_OK;
}

esp_err_t ens160_get_status(ens160_handle_t handle, bool *const data_ready, bool *const gpr_data_ready, ens160_validity_flags_t *const state, bool *const error, bool *const mode) {
    ens160_status_register_t status;

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to read status register  */
    ESP_RETURN_ON_ERROR( ens160_get_status_register(handle, &status), TAG, "read status register for get status failed" );

    /* set states */
    *data_ready     = status.bits.new_data;
    *gpr_data_ready = status.bits.new_gpr_data;
    *state          = status.bits.state;
    *error          = status.bits.error;
    *mode           = status.bits.mode;

    return ESP_OK;
}

esp_err_t ens160_get_compensation_factors(ens160_handle_t handle, float *const temperature, float *const humidity) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to read compensation registers */
    ESP_RETURN_ON_ERROR( ens160_get_compensation_registers(handle, temperature, humidity), TAG, "read compensation registers failed" );

    return ESP_OK;
}

esp_err_t ens160_set_compensation_factors(ens160_handle_t handle, const float temperature, const float humidity) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to write compensation registers */
    ESP_RETURN_ON_ERROR( ens160_set_compensation_registers(handle, temperature, humidity), TAG, "write compensation registers failed" );

    return ESP_OK;
}

esp_err_t ens160_enable_standard_mode(ens160_handle_t handle) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to set operating mode to standard  */
    ESP_RETURN_ON_ERROR( ens160_set_mode_register(handle, ENS160_OPMODE_STANDARD), TAG, "write mode for standard operating mode failed" );

    return ESP_OK;
}

esp_err_t ens160_enable_idle_mode(ens160_handle_t handle) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to set operating mode to idle  */
    ESP_RETURN_ON_ERROR( ens160_set_mode_register(handle, ENS160_OPMODE_IDLE), TAG, "write mode for idle operating mode failed" );

    return ESP_OK;
}

esp_err_t ens160_enable_deep_sleep_mode(ens160_handle_t handle) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to set operating mode to deep sleep  */
    ESP_RETURN_ON_ERROR( ens160_set_mode_register(handle, ENS160_OPMODE_DEEP_SLEEP), TAG, "write mode for deep sleep operating mode failed" );

    return ESP_OK;
}

esp_err_t ens160_reset(ens160_handle_t handle) {
    ens160_interrupt_config_register_t irq_config;

    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* attempt to write operating mode to reset  */
    ESP_RETURN_ON_ERROR( ens160_set_mode_register(handle, ENS160_OPMODE_RESET), TAG, "write mode for soft-reset failed" );

    /* delay task before next i2c transaction */
    vTaskDelay(pdMS_TO_TICKS(ENS160_RESET_DELAY_MS));

    /* attempt to read interrupt configuration register */
    ESP_RETURN_ON_ERROR( ens160_get_interrupt_config_register(handle, &irq_config), TAG, "read interrupt configuration register for reset failed" );

    /* attempt to enable idle operating mode before writing to configuration registers */
    ESP_RETURN_ON_ERROR( ens160_enable_idle_mode(handle), TAG, "enable idle operating mode for reset failed" );

    /* attempt to clear general purpose registers */
    ESP_RETURN_ON_ERROR( ens160_clear_general_purpose_registers(handle), TAG, "clear general purpose registers for reset failed" );

    /* copy irq configuration from device handle */
    irq_config.bits.irq_enabled         = handle->dev_config.irq_enabled;
    irq_config.bits.irq_data_enabled    = handle->dev_config.irq_data_enabled;
    irq_config.bits.irq_gpr_enabled     = handle->dev_config.irq_gpr_enabled;
    irq_config.bits.irq_pin_driver      = handle->dev_config.irq_pin_driver;
    irq_config.bits.irq_pin_polarity    = handle->dev_config.irq_pin_polarity;

    /* attempt to write interrupt configuration register */
    ESP_RETURN_ON_ERROR( ens160_set_interrupt_config_register(handle, irq_config), TAG, "write interrupt configuration register for reset failed" );

    /* attempt to enable standard operating mode to start making measurements (idle by default)  */
    ESP_RETURN_ON_ERROR( ens160_enable_standard_mode(handle), TAG, "enable standard operating mode for reset failed" );

    return ESP_OK;
}

esp_err_t ens160_remove(ens160_handle_t handle) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* remove device from i2c master bus */
    return i2c_master_bus_rm_device(handle->i2c_handle);
}

esp_err_t ens160_delete(ens160_handle_t handle) {
    /* validate arguments */
    ESP_ARG_CHECK( handle );

    /* remove device from master bus */
    ESP_RETURN_ON_ERROR( ens160_remove(handle), TAG, "unable to remove device from i2c master bus, delete handle failed" );

    /* validate handle instance and free handles */
    if(handle->i2c_handle) {
        free(handle->i2c_handle);
        free(handle);
    }

    return ESP_OK;
}

ens160_aqi_uba_row_t ens160_aqi_index_to_definition(const ens160_aqi_uba_indexes_t index) {
    /* attempt aqi-uba index lookup */
    for (size_t i = 0; i < sizeof(ens160_aqi_uba_definition_table) / sizeof(ens160_aqi_uba_definition_table[0]); ++i) {
        if (ens160_aqi_uba_definition_table[i].index == index) {
            return ens160_aqi_uba_definition_table[i];
        }
    }

    return ens160_aqi_uba_definition_table[0];
}

const char* ens160_get_fw_version(void) {
    return ENS160_FW_VERSION_STR;
}

int32_t ens160_get_fw_version_number(void) {
    return ENS160_FW_VERSION_INT32;
}