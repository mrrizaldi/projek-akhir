// Uji buzzer TERPISAH: cuma GPIO 13 + LED onboard. Tanpa TFT, ADC, INA219,
// detektor, jadi kalau buzzer tetap diam di sini, penyebabnya bukan hwtest.
//   pio run -e buzztest -t upload && pio device monitor
//
// Satu siklus ~17 detik, berulang terus. LED onboard menyala selama buzzer
// SEHARUSNYA bunyi (merah = pin LOW, hijau = nada). Modul buzzer 3 pin aktif
// LOW: diam = HIGH.
#include <Arduino.h>
#include "driver/ledc.h"

constexpr int PIN_BUZZ = 13, KANAL = 0, PIN_LED = 48;

static void diam()
{
    ledcDetachPin(PIN_BUZZ);
    pinMode(PIN_BUZZ, OUTPUT);
    digitalWrite(PIN_BUZZ, HIGH);
    neopixelWrite(PIN_LED, 0, 0, 0);
}

static void nada(uint32_t hz, uint32_t ms)
{
    Serial.printf("  nada %u Hz, %u ms\n", (unsigned)hz, (unsigned)ms);
    ledcSetup(KANAL, hz, 8);
    ledcAttachPin(PIN_BUZZ, KANAL);
    ledcWrite(KANAL, 128); // gelombang kotak 50%
    neopixelWrite(PIN_LED, 0, 40, 0);
    delay(ms);
    diam();
}

void setup()
{
    pinMode(PIN_BUZZ, OUTPUT);
    digitalWrite(PIN_BUZZ, HIGH);
    Serial.begin(115200);
}

void loop()
{
    Serial.println("\n1) pin pelan, 3x: LOW 1 dtk / HIGH 1 dtk. Ukur I/O modul: 0 V <-> 3,3 V; tiap LOW = 'klik'");
    for (int i = 0; i < 3; i++)
    {
        digitalWrite(PIN_BUZZ, LOW);
        neopixelWrite(PIN_LED, 40, 0, 0);
        Serial.println("  LOW");
        delay(1000);
        digitalWrite(PIN_BUZZ, HIGH);
        neopixelWrite(PIN_LED, 0, 0, 0);
        Serial.println("  HIGH");
        delay(1000);
    }

    Serial.println("2) nada panjang 2 kHz");
    nada(2000, 2000);
    delay(500);

    Serial.println("3) sapuan 1-5 kHz (cari yang paling keras)");
    for (uint32_t f = 1000; f <= 5000; f += 500)
    {
        nada(f, 400);
        delay(200);
    }

    Serial.println("4) bip 75 bpm, 6x");
    for (int i = 0; i < 6; i++)
    {
        nada(2000, 50);
        delay(750);
    }
    delay(1000);

    // Persis cara hwtest.cpp (pasang_buzzer + buzzer()): kanal dibalik lewat
    // output_invert, nada lewat ledcWriteTone. LED BIRU selama seharusnya bunyi.
    Serial.println("5) cara hwtest: output_invert + ledcWriteTone 2 kHz, 2 dtk");
    ledcSetup(KANAL, 2000, 8);
    ledc_channel_config_t ch = {};
    ch.gpio_num = PIN_BUZZ;
    ch.speed_mode = LEDC_LOW_SPEED_MODE;
    ch.channel = (ledc_channel_t)KANAL;
    ch.timer_sel = LEDC_TIMER_0;
    ch.duty = 0;
    ch.flags.output_invert = 1;
    ledc_channel_config(&ch);
    delay(300);
    neopixelWrite(PIN_LED, 0, 0, 40);
    ledcWriteTone(KANAL, 2000);
    delay(2000);
    ledcWriteTone(KANAL, 0);
    neopixelWrite(PIN_LED, 0, 0, 0);
    diam();
    delay(1500);
}
