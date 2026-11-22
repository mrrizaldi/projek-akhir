#include <unity.h>
#include "ina219.h"

static void test_current_positive(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 100.0f, ina219_current_mA(1000, 0.1f));
}

static void test_current_negative_when_reversed(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.01f, -100.0f, ina219_current_mA(-1000, 0.1f));
}

static void test_current_zero(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, ina219_current_mA(0, 0.1f));
}

static void test_other_shunt_shifts_scale(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 50.0f, ina219_current_mA(1000, 0.2f));
}

static void test_bus_voltage(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 5.0f, ina219_bus_V(1250 << 3));
}

static void test_bus_voltage_ignores_status_bits(void)
{
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 5.0f, ina219_bus_V((1250 << 3) | 0x3));
}

void setUp(void) {}
void tearDown(void) {}

int main(int, char **)
{
    UNITY_BEGIN();
    RUN_TEST(test_current_positive);
    RUN_TEST(test_current_negative_when_reversed);
    RUN_TEST(test_current_zero);
    RUN_TEST(test_other_shunt_shifts_scale);
    RUN_TEST(test_bus_voltage);
    RUN_TEST(test_bus_voltage_ignores_status_bits);
    return UNITY_END();
}
