#include <Arduino.h>
#include <unity.h>
#include "diagnostics.h"
#include "board.h"

void test_pin_diam_high(void)
{
    for (int k = 0; k < 3; k++)
        TEST_ASSERT_EQUAL_MESSAGE(HIGH, digitalRead(PIN_BTN[k]), "tombol terbaca ditekan saat diam");
}

void test_tidak_menggantung(void)
{
    const uint32_t t0 = millis();
    const diag_result_t h = diag_button(300);
    const uint32_t ms = millis() - t0;
    TEST_ASSERT_UINT32_WITHIN(50, 300, ms);
    TEST_ASSERT_FALSE_MESSAGE(h.pass, h.summary);
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    board_begin();
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_pin_diam_high);
    RUN_TEST(test_tidak_menggantung);
    UNITY_END();
}

void loop() {}
