#ifdef ARDUINO
#include "board.h"

#include <SPI.h>
#include "driver/ledc.h"

constexpr int WITHOUT_MISO = -1;
constexpr uint32_t TONE_IDLE = 0;

Adafruit_ST7789 tft(-1, TFT_DC, TFT_RST);

static void attach_buzzer()
{
    pinMode(PIN_BUZZ, OUTPUT);
    digitalWrite(PIN_BUZZ, HIGH);
    ledcSetup(CHANNEL_BUZZ, TONE_HZ, 8);
    ledc_channel_config_t ch = {};
    ch.gpio_num = PIN_BUZZ;
    ch.speed_mode = LEDC_LOW_SPEED_MODE;
    ch.channel = (ledc_channel_t)CHANNEL_BUZZ;
    ch.timer_sel = LEDC_TIMER_0;
    ch.duty = 0;
    ch.flags.output_invert = 1;
    ledc_channel_config(&ch);
}

void buzzer(bool enabled)
{
    ledcWriteTone(CHANNEL_BUZZ, enabled ? TONE_HZ : TONE_IDLE);
}

void board_begin(void)
{
    SPI.begin(TFT_SCK, WITHOUT_MISO, TFT_MOSI);
    attach_buzzer();

    pinMode(PIN_LOP, INPUT_PULLUP);
    pinMode(PIN_LON, INPUT_PULLUP);
    for (int p : PIN_BTN)
        pinMode(p, INPUT_PULLUP);

    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(CHANNEL_ECG, ADC_ATTEN_DB_12);

    tft.init(TFT_H, TFT_W, SPI_MODE3);
    tft.setRotation(1);
    tft.fillScreen(ST77XX_BLACK);
}
#endif
