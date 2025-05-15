#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "led_strip.h"
#include "driver/gpio.h"

#define NEOPIXEL_GPIO 8
#define NUM_PIXELS    1

void app_main(void)
{
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
        .resolution_hz = 10 * 1000 * 1000, // 10MHz
        .mem_block_symbols = 0,
        .flags.with_dma = false,
    };
    led_strip_new_rmt_device(&strip_config, &rmt_config, &strip);

    uint8_t r, g, b;
    while (1) {
        // Cycle through the color wheel (0-255)
        for (int i = 0; i < 256; i++) {
            // Simple HSV to RGB conversion for smooth color cycling
            uint8_t region = i / 43;
            uint8_t remainder = (i - (region * 43)) * 6;

            uint8_t p = 0;
            uint8_t q = 255 - remainder;
            uint8_t t = remainder;

            switch (region) {
                case 0:
                    r = 255; g = t; b = p;
                    break;
                case 1:
                    r = q; g = 255; b = p;
                    break;
                case 2:
                    r = p; g = 255; b = t;
                    break;
                case 3:
                    r = p; g = q; b = 255;
                    break;
                case 4:
                    r = t; g = p; b = 255;
                    break;
                default:
                    r = 255; g = p; b = q;
                    break;
            }
            led_strip_set_pixel(strip, 0, r, g, b);
            led_strip_refresh(strip);
            vTaskDelay(pdMS_TO_TICKS(20));
        }
    }
}
