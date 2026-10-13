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
        // BRNG 32 V; PGA /8 = +-320 mV / 0,1 ohm = +-3,2 A skala penuh.
        TEST_ASSERT_TRUE_MESSAGE(V >= 0.0f && V <= 32.0f, "tegangan bus di luar 0..32 V");
        TEST_ASSERT_TRUE_MESSAGE(fabsf(mA) <= 3200.0f, "arus di luar skala penuh +-3,2 A");
        delay(100);                     // > 68 ms: satu hasil rata-rata baru
    }
}

// Register mentah, untuk memastikan shunt berada di jalur arus beban. Shunt di
// jalur yang dialiri arus: register bus = tegangan catu (~5 V USB / ~3,7-4,2 V
// baterai) dan register shunt stabil. Bus ~0 V berarti VIN- tidak tersambung ke
// catu yang mengalir; angka arus dari kondisi itu bukan konsumsi alat.
// Tidak dijadikan syarat lulus: test ini juga dipakai saat board dicatu USB.
void test_register_mentah(void)
{
    for (int i = 0; i < 10; i++) {
        uint16_t sh, bus;
        TEST_ASSERT_TRUE(ina219_baca_reg(INA219_REG_SHUNT, &sh) && ina219_baca_reg(INA219_REG_BUS, &bus));
        Serial.printf("mentah: shunt 0x%04X (%d x 10 uV) | bus 0x%04X -> %u x 4 mV, CNVR %d OVF %d\n",
                      sh, (int16_t)sh, bus, bus >> 3, (bus >> 1) & 1, bus & 1);
        delay(100);
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
    RUN_TEST(test_register_mentah);
    UNITY_END();
}

void loop() {}
