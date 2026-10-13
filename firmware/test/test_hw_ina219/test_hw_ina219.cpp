#include <Arduino.h>
#include <unity.h>
#include "diagnosa.h"
#include "perangkat.h"

void test_diag_ina219(void)
{
    for (int i = 0; i < 3; i++) {
        const diag_hasil_t h = diag_ina219();
        TEST_ASSERT_TRUE_MESSAGE(h.lulus, h.ringkas);
    }
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    perangkat_mulai();
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_diag_ina219);
    UNITY_END();
}

void loop() {}
