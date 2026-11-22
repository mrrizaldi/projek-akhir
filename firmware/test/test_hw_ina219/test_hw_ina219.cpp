#include <Arduino.h>
#include <unity.h>
#include "diagnostics.h"
#include "board.h"

void test_diag_ina219(void)
{
    for (int i = 0; i < 3; i++) {
        const diag_result_t h = diag_ina219();
        TEST_ASSERT_TRUE_MESSAGE(h.pass, h.summary);
    }
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    board_begin();
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_diag_ina219);
    UNITY_END();
}

void loop() {}
