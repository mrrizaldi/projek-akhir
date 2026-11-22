#include <unity.h>
#include <string.h>
#include "ecg_mqtt.h"

static ecg_mqtt_beat_t beat(uint32_t ms, int label)
{
    ecg_mqtt_beat_t b;
    b.ms = ms;
    b.bpm = 72.0f;
    b.rr_ms = 833.3f;
    b.confidence = 0.9312f;
    b.label = label;
    b.quality_ok = 1;
    for (int i = 0; i < ECG_SNIPPET_N; i++) b.snippet[i] = (int16_t)(i * 10);
    return b;
}

#define TEST_CAP 8
static ecg_mqtt_beat_t ring_test[TEST_CAP];

void setUp(void) { ecg_mqtt_queue_attach(ring_test, TEST_CAP); }
void tearDown(void) {}

static void test_payload_single(void)
{
    char buf[512];
    ecg_mqtt_beat_t b = beat(500, 1);
    const size_t n = ecg_mqtt_payload(buf, sizeof buf, &b, 1, 1700000000000ULL);
    TEST_ASSERT_TRUE(n > 0);
    TEST_ASSERT_EQUAL_size_t(n, strlen(buf));
    TEST_ASSERT_EQUAL('{', buf[0]);
    TEST_ASSERT_NOT_NULL(strstr(buf, "\"ts\":1700000000500"));
    TEST_ASSERT_NOT_NULL(strstr(buf, "\"label\":1"));
    TEST_ASSERT_NOT_NULL(strstr(buf, "\"label_str\":\"Aritmia\""));
    TEST_ASSERT_NOT_NULL(strstr(buf, "\"signal_quality\":\"good\""));
    TEST_ASSERT_NOT_NULL(strstr(buf, "\"ecg_snippet\":[0,10,20,30,40,50,60,70]"));
}

static void test_payload_batch_array(void)
{
    char buf[1024];
    ecg_mqtt_beat_t b[3] = { beat(100, 0), beat(200, 1), beat(300, 0) };
    const size_t n = ecg_mqtt_payload(buf, sizeof buf, b, 3, 1000ULL);
    TEST_ASSERT_TRUE(n > 0);
    TEST_ASSERT_EQUAL('[', buf[0]);
    TEST_ASSERT_EQUAL(']', buf[n - 1]);
    TEST_ASSERT_NOT_NULL(strstr(buf, "\"ts\":1100"));
    TEST_ASSERT_NOT_NULL(strstr(buf, "\"ts\":1200"));
    TEST_ASSERT_NOT_NULL(strstr(buf, "\"ts\":1300"));
}

static void test_payload_buffer_short(void)
{
    char buf[40];
    ecg_mqtt_beat_t b = beat(0, 0);
    TEST_ASSERT_EQUAL_size_t(0, ecg_mqtt_payload(buf, sizeof buf, &b, 1, 0));
}

static void test_queue_fifo(void)
{
    for (uint32_t i = 0; i < 5; i++) { ecg_mqtt_beat_t b = beat(i, 0); ecg_mqtt_queue_fill(&b); }
    TEST_ASSERT_EQUAL_size_t(5, ecg_mqtt_queue_n());

    ecg_mqtt_beat_t out[3];
    TEST_ASSERT_EQUAL_size_t(3, ecg_mqtt_queue_peek(out, 3));
    TEST_ASSERT_EQUAL_UINT32(0, out[0].ms);
    TEST_ASSERT_EQUAL_UINT32(2, out[2].ms);
    TEST_ASSERT_EQUAL_size_t(5, ecg_mqtt_queue_n());

    ecg_mqtt_queue_drop(3);
    TEST_ASSERT_EQUAL_size_t(2, ecg_mqtt_queue_n());
    ecg_mqtt_queue_peek(out, 1);
    TEST_ASSERT_EQUAL_UINT32(3, out[0].ms);
}

static void test_queue_full_drops_oldest(void)
{
    for (uint32_t i = 0; i < TEST_CAP + 5; i++) {
        ecg_mqtt_beat_t b = beat(i, 0);
        ecg_mqtt_queue_fill(&b);
    }
    TEST_ASSERT_EQUAL_size_t(TEST_CAP, ecg_mqtt_queue_n());
    TEST_ASSERT_EQUAL_size_t(5, ecg_mqtt_queue_lost());

    ecg_mqtt_beat_t out[1];
    ecg_mqtt_queue_peek(out, 1);
    TEST_ASSERT_EQUAL_UINT32(5, out[0].ms);
}

static void test_queue_attach_capacity(void)
{
    TEST_ASSERT_EQUAL_size_t(TEST_CAP, ecg_mqtt_queue_capacity());

    static ecg_mqtt_beat_t large[100];
    ecg_mqtt_queue_attach(large, 100);
    TEST_ASSERT_EQUAL_size_t(100, ecg_mqtt_queue_capacity());
    for (uint32_t i = 0; i < 100; i++) { ecg_mqtt_beat_t b = beat(i, 0); ecg_mqtt_queue_fill(&b); }
    TEST_ASSERT_EQUAL_size_t(100, ecg_mqtt_queue_n());
    TEST_ASSERT_EQUAL_size_t(0, ecg_mqtt_queue_lost());

    ecg_mqtt_queue_attach(NULL, 0);
    TEST_ASSERT_EQUAL_size_t(ECG_MQTT_QUEUE_MIN, ecg_mqtt_queue_capacity());
    TEST_ASSERT_EQUAL_size_t(0, ecg_mqtt_queue_n());
}

int main(int, char **)
{
    UNITY_BEGIN();
    RUN_TEST(test_payload_single);
    RUN_TEST(test_payload_batch_array);
    RUN_TEST(test_payload_buffer_short);
    RUN_TEST(test_queue_fifo);
    RUN_TEST(test_queue_full_drops_oldest);
    RUN_TEST(test_queue_attach_capacity);
    return UNITY_END();
}
