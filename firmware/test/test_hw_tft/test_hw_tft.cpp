// TFT ST7789 172x320 di board: inisialisasi tanpa crash dan transfer SPI
// benar-benar terjadi.
//
//   pio test -e esp32-s3 -f test_hw_tft
//
// Layar tidak bisa dibaca balik (CS ke GND, tanpa MISO), jadi yang diukur
// adalah waktu transfer: satu layar penuh = 110 KB, dan bus SPI yang tidak
// mengirim apa pun selesai seketika. Isi layar dinilai mata: empat pita
// warna (merah, hijau, biru, putih) dan tulisan "TFT OK".
#include <Arduino.h>
#include <unity.h>
#include "perangkat.h"

static uint32_t ms_mulai;

void test_init_selesai(void)
{
    TEST_ASSERT_EQUAL(TFT_W, tft.width());
    TEST_ASSERT_EQUAL(TFT_H, tft.height());
    Serial.printf("perangkat_mulai: %u ms\n", (unsigned)ms_mulai);
    TEST_ASSERT_LESS_THAN_UINT32(2000, ms_mulai);
}

void test_isi_layar_penuh_lewat_spi(void)
{
    const uint32_t t0 = micros();
    tft.fillScreen(ST77XX_BLUE);
    const uint32_t us = micros() - t0;
    Serial.printf("fillScreen 320x172: %u us\n", (unsigned)us);
    // 110 KB pada 80 MHz pun butuh >= 11 ms; di bawah 5 ms berarti tidak ada transfer.
    TEST_ASSERT_GREATER_THAN_UINT32_MESSAGE(5000, us, "fillScreen terlalu cepat: SPI tidak mengirim?");
    TEST_ASSERT_LESS_THAN_UINT32_MESSAGE(500000, us, "fillScreen terlalu lambat");
}

void test_pola_untuk_dilihat(void)
{
    const uint16_t warna[4] = {ST77XX_RED, ST77XX_GREEN, ST77XX_BLUE, ST77XX_WHITE};
    for (int i = 0; i < 4; i++)
        tft.fillRect(i * TFT_W / 4, 0, TFT_W / 4, TFT_H, warna[i]);
    tft.setTextSize(4);
    tft.setTextColor(ST77XX_BLACK, ST77XX_YELLOW);
    tft.setCursor(80, 70);
    tft.print("TFT OK");
    Serial.println("LIHAT LAYAR: pita merah-hijau-biru-putih dan tulisan \"TFT OK\".");
    TEST_PASS();
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    const uint32_t t0 = millis();
    perangkat_mulai();
    ms_mulai = millis() - t0;
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_init_selesai);
    RUN_TEST(test_isi_layar_penuh_lewat_spi);
    RUN_TEST(test_pola_untuk_dilihat);
    UNITY_END();
}

void loop() {}
