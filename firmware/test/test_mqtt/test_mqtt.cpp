// Dua hal yang bisa diam-diam salah dan merusak klaim di laporan:
//   1. format payload  -> dashboard sepi, tanpa error di board
//   2. ring backlog    -> klaim "beat hilang = seharusnya - sampai" jadi bohong
// Keduanya murni (tanpa WiFi), jadi diuji di PC.
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

void setUp(void) { ecg_mqtt_antre_reset(); }
void tearDown(void) {}

static void test_payload_tunggal(void)
{
    char buf[512];
    ecg_mqtt_beat_t b = beat(500, 1);
    const size_t n = ecg_mqtt_payload(buf, sizeof buf, &b, 1, 1700000000000ULL);
    TEST_ASSERT_TRUE(n > 0);
    TEST_ASSERT_EQUAL_size_t(n, strlen(buf));
    TEST_ASSERT_EQUAL('{', buf[0]);
    // ts = base + ms, bukan base: inilah yang menjaga waktu KEJADIAN.
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

// Buffer kekecilan harus mengembalikan 0, bukan payload terpotong: JSON
// separuh diterima broker sebagai sampah dan gagalnya tidak kelihatan.
static void test_payload_buffer_kurang(void)
{
    char buf[40];
    ecg_mqtt_beat_t b = beat(0, 0);
    TEST_ASSERT_EQUAL_size_t(0, ecg_mqtt_payload(buf, sizeof buf, &b, 1, 0));
}

static void test_antre_fifo(void)
{
    for (uint32_t i = 0; i < 5; i++) { ecg_mqtt_beat_t b = beat(i, 0); ecg_mqtt_antre_isi(&b); }
    TEST_ASSERT_EQUAL_size_t(5, ecg_mqtt_antre_n());

    ecg_mqtt_beat_t keluar[3];
    TEST_ASSERT_EQUAL_size_t(3, ecg_mqtt_antre_intip(keluar, 3));
    TEST_ASSERT_EQUAL_UINT32(0, keluar[0].ms);
    TEST_ASSERT_EQUAL_UINT32(2, keluar[2].ms);
    // Mengintip TIDAK membuang: PUBACK belum datang.
    TEST_ASSERT_EQUAL_size_t(5, ecg_mqtt_antre_n());

    ecg_mqtt_antre_buang(3);
    TEST_ASSERT_EQUAL_size_t(2, ecg_mqtt_antre_n());
    ecg_mqtt_antre_intip(keluar, 1);
    TEST_ASSERT_EQUAL_UINT32(3, keluar[0].ms);
}

// Ring penuh membuang yang TERTUA dan mencatatnya. Kalau yang dibuang malah
// yang terbaru, alat kehilangan justru menit yang paling ingin dilihat.
static void test_antre_penuh_buang_tertua(void)
{
    for (uint32_t i = 0; i < ECG_MQTT_ANTRE_N + 5; i++) {
        ecg_mqtt_beat_t b = beat(i, 0);
        ecg_mqtt_antre_isi(&b);
    }
    TEST_ASSERT_EQUAL_size_t(ECG_MQTT_ANTRE_N, ecg_mqtt_antre_n());
    TEST_ASSERT_EQUAL_size_t(5, ecg_mqtt_antre_hilang());

    ecg_mqtt_beat_t keluar[1];
    ecg_mqtt_antre_intip(keluar, 1);
    TEST_ASSERT_EQUAL_UINT32(5, keluar[0].ms);          // 0..4 terbuang
}

int main(int, char **)
{
    UNITY_BEGIN();
    RUN_TEST(test_payload_tunggal);
    RUN_TEST(test_payload_batch_array);
    RUN_TEST(test_payload_buffer_kurang);
    RUN_TEST(test_antre_fifo);
    RUN_TEST(test_antre_penuh_buang_tertua);
    return UNITY_END();
}
