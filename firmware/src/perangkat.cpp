// Pemasangan perangkat PCB rev1. Kontrak: include/perangkat.h
#ifdef ARDUINO
#include "perangkat.h"

#include <SPI.h>
#include "driver/ledc.h"

Adafruit_ST7789 tft(-1, TFT_DC, TFT_RST);

// Pin dibuat HIGH (diam) sebelum LEDC mengambil alih: pin yang belum diatur
// bisa terbaca LOW oleh modul aktif-LOW dan berbunyi.
// Nada dibuat LEDC dengan keluaran dibalik (output_invert), sehingga duty 0
// menghasilkan HIGH = diam dan gelombang kotak tetap berbunyi.
static void pasang_buzzer()
{
    pinMode(PIN_BUZZ, OUTPUT);
    digitalWrite(PIN_BUZZ, HIGH);
    ledcSetup(KANAL_BUZZ, NADA_HZ, 8);
    ledc_channel_config_t ch = {};
    ch.gpio_num = PIN_BUZZ;
    ch.speed_mode = LEDC_LOW_SPEED_MODE;
    ch.channel = (ledc_channel_t)KANAL_BUZZ;
    ch.timer_sel = LEDC_TIMER_0; // kanal 0 -> timer 0, sama dengan ledcSetup
    ch.duty = 0;
    ch.flags.output_invert = 1;
    ledc_channel_config(&ch);
}

void buzzer(bool nyala)
{
    ledcWriteTone(KANAL_BUZZ, nyala ? NADA_HZ : 0); // duty 0 + invert = HIGH = diam
}

void perangkat_mulai(void)
{
    // SPI WAJIB sebelum buzzer. Di ESP32-S3, miso = -1 tidak berarti "tanpa
    // MISO": spiAttachMISO menggantinya dengan MISO bawaan FSPI, yaitu GPIO 13,
    // lalu menjadikannya INPUT sehingga LEDC kehilangan pin buzzer (bip
    // terhitung tetapi tidak berbunyi). tft.init() memanggil SPI.begin() lagi,
    // tetapi SPIClass::begin() langsung kembali bila bus sudah aktif.
    // Urutan ini dijaga test_hw_buzzer.
    SPI.begin(TFT_SCK, -1, TFT_MOSI);
    pasang_buzzer();

    // INPUT_PULLUP: kabel LO yang putus terbaca HIGH = "elektroda lepas",
    // bukan mengambang. Keluaran LO AD8232 push-pull, pull-up 45k tidak
    // melawannya.
    pinMode(PIN_LOP, INPUT_PULLUP);
    pinMode(PIN_LON, INPUT_PULLUP);
    for (int p : PIN_BTN)
        pinMode(p, INPUT_PULLUP);

    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(KANAL_EKG, ADC_ATTEN_DB_12);

    tft.init(TFT_H, TFT_W, SPI_MODE3); // CS ke GND -> wajib mode 3
    tft.setRotation(1);
    tft.fillScreen(ST77XX_BLACK);
}
#endif
