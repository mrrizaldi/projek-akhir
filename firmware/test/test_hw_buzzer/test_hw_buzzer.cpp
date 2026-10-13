// Buzzer di board lewat diag_buzzer() (src/diagnosa.cpp, sama dengan menu Tes):
// pin, polaritas aktif-LOW, dan LEDC yang tetap memegang GPIO 13 setelah
// SPI + TFT terpasang, lalu tiga bip untuk didengar.
//
//   pio test -e esp32-s3 -f test_hw_buzzer
//
// Bila lulus tetapi bip tidak terdengar, periksa rangkaian (VCC modul 3V3,
// I/O ke GPIO 13).
#include <Arduino.h>
#include <unity.h>
#include "diagnosa.h"
#include "perangkat.h"

void test_diag_buzzer(void)
{
    const diag_hasil_t h = diag_buzzer();
    TEST_ASSERT_TRUE_MESSAGE(h.lulus, h.ringkas);
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    perangkat_mulai();            // urutan yang sama dengan firmware utama
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_diag_buzzer);
    UNITY_END();
}

void loop() {}
