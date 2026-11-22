#include <Arduino.h>
#include <unity.h>
#include "diagnostics.h"
#include "board.h"

void test_diag_buzzer(void)
{
    const diag_result_t h = diag_buzzer();
    TEST_ASSERT_TRUE_MESSAGE(h.pass, h.summary);
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    board_begin();
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_diag_buzzer);
    UNITY_END();
}

void loop() {}
