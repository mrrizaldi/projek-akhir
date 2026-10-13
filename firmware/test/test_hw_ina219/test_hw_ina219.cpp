// INA219 di board lewat I2C (SDA 17, SCL 18, alamat 0x40).
//
//   pio test -e esp32-s3 -f test_hw_ina219
//
// Konversi register sudah diuji di PC (test_ina219); di sini yang diuji
// sambungannya: modul menjawab, konfigurasi tertulis, dan bacaan berada di
// rentang fisik chip. Nilai tegangan tergantung catu (USB atau baterai), jadi
// dicetak untuk dicocokkan dengan multimeter, tidak dijadikan syarat lulus.
#include <Arduino.h>
#include <unity.h>
#include "ina219.h"
#include "perangkat.h"

void test_modul_terdeteksi(void)
{
    TEST_ASSERT_TRUE_MESSAGE(ina219_mulai(I2C_SDA, I2C_SCL),
        "INA219 tidak menjawab: cek SDA 17, SCL 18, VCC modul 3V3");
}

void test_bacaan_dalam_rentang(void)
{
    for (int i = 0; i < 5; i++) {
        float mA = 0, V = 0;
        TEST_ASSERT_TRUE_MESSAGE(ina219_baca(R_SHUNT, &mA, &V), "pembacaan register gagal");
        Serial.printf("INA219: I = %.1f mA, V = %.3f V, P = %.0f mW\n", mA, V, mA * V);
        // BRNG 16 V; PGA /1 = +-40 mV / 0,1 ohm = +-400 mA skala penuh.
        TEST_ASSERT_TRUE_MESSAGE(V >= 0.0f && V <= 16.0f, "tegangan bus di luar 0..16 V");
        TEST_ASSERT_TRUE_MESSAGE(fabsf(mA) <= 400.0f, "arus di luar skala penuh +-400 mA");
        delay(100);                     // > 68 ms: satu hasil rata-rata baru
    }
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    perangkat_mulai();                  // buzzer diam, pin lain dalam keadaan firmware utama
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_modul_terdeteksi);
    RUN_TEST(test_bacaan_dalam_rentang);
    UNITY_END();
}

void loop() {}
