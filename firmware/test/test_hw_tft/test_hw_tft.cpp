#include <Arduino.h>
#include <unity.h>
#include "diagnostics.h"
#include "board.h"

static uint32_t ms_begin;

void test_init_done(void)
{
    Serial.printf("perangkat_mulai: %u ms\n", (unsigned)ms_begin);
    TEST_ASSERT_LESS_THAN_UINT32(2000, ms_begin);
}

void test_diag_screen(void)
{
    const diag_result_t h = diag_screen();
    TEST_ASSERT_TRUE_MESSAGE(h.pass, h.summary);
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    const uint32_t t0 = millis();
    board_begin();
    ms_begin = millis() - t0;
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_init_done);
    RUN_TEST(test_diag_screen);
    UNITY_END();
}

void loop() {}
