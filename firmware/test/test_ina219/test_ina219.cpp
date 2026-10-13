#include <unity.h>
#include "ina219.h"

static void test_arus_positif(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 100.0f, ina219_arus_mA(1000, 0.1f));
}

static void test_arus_negatif_saat_terbalik(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.01f, -100.0f, ina219_arus_mA(-1000, 0.1f));
}

static void test_arus_nol(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, ina219_arus_mA(0, 0.1f));
}

static void test_shunt_lain_menggeser_skala(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 50.0f, ina219_arus_mA(1000, 0.2f));
}

static void test_tegangan_bus(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 5.0f, ina219_bus_V(1250 << 3));
}

static void test_tegangan_bus_mengabaikan_bit_status(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 5.0f, ina219_bus_V((1250 << 3) | 0x3));
}

void setUp(void) {}
void tearDown(void) {}

static void jalankan(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_arus_positif);
    RUN_TEST(test_arus_negatif_saat_terbalik);
    RUN_TEST(test_arus_nol);
    RUN_TEST(test_shunt_lain_menggeser_skala);
    RUN_TEST(test_tegangan_bus);
    RUN_TEST(test_tegangan_bus_mengabaikan_bit_status);
    UNITY_END();
}

#ifdef ARDUINO
#include <Arduino.h>
void setup() { Serial.begin(115200); delay(2000); jalankan(); }
void loop() {}
#else
int main(int argc, char **argv) { (void)argc; (void)argv; jalankan(); return 0; }
#endif
