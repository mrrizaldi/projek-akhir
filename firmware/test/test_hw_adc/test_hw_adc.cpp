#include <Arduino.h>
#include <unity.h>
#include "diagnosa.h"
#include "perangkat.h"
#include "ecg_preproc.h"

static volatile uint32_t n_isr;

static void IRAM_ATTR on_timer()
{
    if (adc1_get_raw(KANAL_EKG) >= 0) n_isr++;
}

void test_diag_adc(void)
{
    const diag_hasil_t h = diag_adc();
    TEST_ASSERT_TRUE_MESSAGE(h.lulus, h.ringkas);
}

void test_timer_360hz(void)
{
    hw_timer_t *timer = timerBegin(0, 80, true);
    timerAttachInterrupt(timer, &on_timer, true);
    timerAlarmWrite(timer, 1000000 / ECG_FS, true);
    n_isr = 0;
    timerAlarmEnable(timer);
    delay(2000);
    timerAlarmDisable(timer);
    timerEnd(timer);
    Serial.printf("timer: %u sampel ADC dalam 2 detik\n", (unsigned)n_isr);
    TEST_ASSERT_UINT32_WITHIN(4, 2 * ECG_FS, n_isr);
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    perangkat_mulai();
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_diag_adc);
    RUN_TEST(test_timer_360hz);
    UNITY_END();
}

void loop() {}
