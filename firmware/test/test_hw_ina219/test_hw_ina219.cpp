// INA219 di board lewat diag_ina219() (src/diagnosa.cpp, sama dengan menu Tes):
// modul menjawab di I2C (SDA 17, SCL 18, 0x40), konfigurasi tertulis, bacaan
// dalam rentang chip.
//
//   pio test -e esp32-s3 -f test_hw_ina219
//
// Konversi register diuji di PC (test_ina219). Tegangan tergantung catu (USB
// atau baterai), jadi dicetak untuk dicocokkan dengan multimeter; V bus < 1 V
// hanya ditandai di ringkas, tidak menggagalkan.
#include <Arduino.h>
#include <unity.h>
#include "diagnosa.h"
#include "perangkat.h"

void test_diag_ina219(void)
{
    for (int i = 0; i < 3; i++) {
        const diag_hasil_t h = diag_ina219();
        TEST_ASSERT_TRUE_MESSAGE(h.lulus, h.ringkas);
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
    RUN_TEST(test_diag_ina219);
    UNITY_END();
}

void loop() {}
