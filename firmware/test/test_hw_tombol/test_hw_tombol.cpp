// Tombol B1/B2/B3 di board, tanpa menunggu manusia: pin diam = HIGH (pull-up,
// tidak ada tombol macet / terhubung singkat ke GND) dan diag_tombol() kembali
// tepat waktu bila tidak ada yang menekan. Uji tekan sungguhan lewat menu Tes.
//
//   pio test -e esp32-s3 -f test_hw_tombol     (JANGAN menekan tombol)
#include <Arduino.h>
#include <unity.h>
#include "diagnosa.h"
#include "perangkat.h"

void test_pin_diam_high(void)
{
    for (int k = 0; k < 3; k++)
        TEST_ASSERT_EQUAL_MESSAGE(HIGH, digitalRead(PIN_BTN[k]), "tombol terbaca ditekan saat diam");
}

void test_tidak_menggantung(void)
{
    const uint32_t t0 = millis();
    const diag_hasil_t h = diag_tombol(300);
    const uint32_t ms = millis() - t0;
    TEST_ASSERT_UINT32_WITHIN(50, 300, ms);
    TEST_ASSERT_FALSE_MESSAGE(h.lulus, h.ringkas);
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    perangkat_mulai();
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_pin_diam_high);
    RUN_TEST(test_tidak_menggantung);
    UNITY_END();
}

void loop() {}
