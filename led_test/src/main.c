#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/rmt.h"

#define BLINK_GPIO 8
#define WS2812_GPIO 18
#define WS2812_RMT_CHANNEL RMT_CHANNEL_0

// WS2812 timing parameters (in ns)
#define T0H  400  // 0 bit high time
#define T1H  800  // 1 bit high time
#define T0L  850  // 0 bit low time
#define T1L  450  // 1 bit low time
#define RES  50000 // Reset code (50us)

static void ws2812_send_byte(uint8_t byte, rmt_item32_t *items, int *idx) {
    for (int i = 7; i >= 0; i--) {
        if (byte & (1 << i)) {
            items[*idx].duration0 = T1H / 12.5;
            items[*idx].level0 = 1;
            items[*idx].duration1 = T1L / 12.5;
            items[*idx].level1 = 0;
        } else {
            items[*idx].duration0 = T0H / 12.5;
            items[*idx].level0 = 1;
            items[*idx].duration1 = T0L / 12.5;
            items[*idx].level1 = 0;
        }
        (*idx)++;
    }
}

static void ws2812_show(uint8_t blue, uint8_t red, uint8_t green) {
    rmt_item32_t items[24 + 1]; // 24 bits + reset
    int idx = 0;
    // WS2812 expects GRB order, but your LED is B/R/G, so send blue, red, green
    ws2812_send_byte(blue, items, &idx);
    ws2812_send_byte(red, items, &idx);
    ws2812_send_byte(green, items, &idx);
    // Reset pulse
    items[idx].duration0 = RES / 12.5;
    items[idx].level0 = 0;
    items[idx].duration1 = 0;
    items[idx].level1 = 0;

    rmt_write_items(WS2812_RMT_CHANNEL, items, idx + 1, true);
    rmt_wait_tx_done(WS2812_RMT_CHANNEL, portMAX_DELAY);
}

void app_main() {
    gpio_reset_pin(BLINK_GPIO);
    gpio_set_direction(BLINK_GPIO, GPIO_MODE_OUTPUT);

    rmt_config_t config = {
        .rmt_mode = RMT_MODE_TX,
        .channel = WS2812_RMT_CHANNEL,
        .gpio_num = WS2812_GPIO,
        .clk_div = 2, // 80MHz/2 = 40MHz, 1 tick = 25ns, but we use 12.5ns for better accuracy
        .mem_block_num = 1,
        .tx_config = {
            .loop_en = false,
            .carrier_en = false,
            .idle_output_en = true,
            .idle_level = RMT_IDLE_LEVEL_LOW,
        }
    };
    rmt_config(&config);
    rmt_driver_install(WS2812_RMT_CHANNEL, 0, 0);

    uint8_t colors[3][3] = {
        {10, 0, 0},   // Blue
        {0, 10, 0},   // Red
        {0, 0, 10}    // Green
    };
    int color_idx = 0;

    while (1) {
        gpio_set_level(BLINK_GPIO, 1);
        ws2812_show(colors[color_idx][0], colors[color_idx][1], colors[color_idx][2]);
        vTaskDelay(pdMS_TO_TICKS(500));

        gpio_set_level(BLINK_GPIO, 0);
        ws2812_show(0, 0, 0); // Off
        vTaskDelay(pdMS_TO_TICKS(500));

        color_idx = (color_idx + 1) % 3;
    }
}