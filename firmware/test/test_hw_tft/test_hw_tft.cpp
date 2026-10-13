// TFT ST7789 172x320 di board: inisialisasi tanpa crash, lalu diag_layar()
// (src/diagnosa.cpp, sama dengan menu Tes): waktu fillScreen membuktikan SPI
// mengirim, pola warna dinilai mata.
//
//   pio test -e esp32-s3 -f test_hw_tft
#include <Arduino.h>
#include <unity.h>
#include "diagnosa.h"
#include "perangkat.h"

static uint32_t ms_mulai;

void test_init_selesai(void)
{
    Serial.printf("perangkat_mulai: %u ms\n", (unsigned)ms_mulai);
    TEST_ASSERT_LESS_THAN_UINT32(2000, ms_mulai);
}

void test_diag_layar(void)
{
    const diag_hasil_t h = diag_layar();
    TEST_ASSERT_TRUE_MESSAGE(h.lulus, h.ringkas);
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
    RUN_TEST(test_diag_layar);
    UNITY_END();
}

void loop() {}
