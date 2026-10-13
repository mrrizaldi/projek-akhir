// Jalur akuisisi di board: ADC EKG (GPIO 1), pin LO+/LO- (42/2), dan timer
// 360 Hz yang sama dengan firmware utama.
//
//   pio test -e esp32-s3 -f test_hw_adc
//
// Yang menjadi syarat lulus hanya hal yang tidak bergantung pada elektroda:
// ADC menjawab dalam rentang 12-bit dan timer menghasilkan tepat 360 sampel
// per detik. Nilai mentah dan status LO dicetak untuk dibaca manusia: tanpa
// elektroda, keluaran AD8232 wajar menempel di rail atau tengah dan LO = 1.
#include <Arduino.h>
#include <unity.h>
#include "perangkat.h"
#include "ecg_preproc.h"   // ECG_FS

static volatile uint32_t n_isr;
static volatile uint16_t v_min = 4095, v_maks;

static void IRAM_ATTR on_timer()
{
    const int v = adc1_get_raw(KANAL_EKG);
    if (v < 0) return;                  // error ADC: n_isr tidak bertambah
    if (v < v_min) v_min = v;
    if (v > v_maks) v_maks = v;
    n_isr++;
}

void test_adc_terbaca(void)
{
    for (int i = 0; i < 100; i++) {
        const int v = adc1_get_raw(KANAL_EKG);
        TEST_ASSERT_TRUE_MESSAGE(v >= 0 && v <= 4095, "adc1_get_raw di luar 0..4095");
    }
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
    Serial.printf("ADC GPIO1: %u sampel dalam 2 detik, mentah %u..%u (ayun %u)\n",
                  (unsigned)n_isr, v_min, v_maks, (unsigned)(v_maks - v_min));
    TEST_ASSERT_UINT32_WITHIN(4, 2 * ECG_FS, n_isr);
}

void test_lo_terbaca(void)
{
    const int lop = digitalRead(PIN_LOP), lon = digitalRead(PIN_LON);
    Serial.printf("LO+ (GPIO%d) = %d, LO- (GPIO%d) = %d  (1 = elektroda lepas / kabel putus)\n",
                  PIN_LOP, lop, PIN_LON, lon);
    TEST_PASS();
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    perangkat_mulai();
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_adc_terbaca);
    RUN_TEST(test_timer_360hz);
    RUN_TEST(test_lo_terbaca);
    UNITY_END();
}

void loop() {}
