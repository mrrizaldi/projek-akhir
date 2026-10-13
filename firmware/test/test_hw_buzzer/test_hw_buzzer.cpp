// Buzzer di board: pin, polaritas aktif-LOW, dan LEDC yang tetap memegang
// GPIO 13 setelah SPI + TFT terpasang.
//
//   pio test -e esp32-s3 -f test_hw_buzzer
//
// Yang diuji adalah register GPIO matrix dan level pin, bukan bunyi. Bunyi
// dinilai telinga: test terakhir membunyikan tiga bip. Bila semua test lulus
// tetapi bip tidak terdengar, periksa rangkaian (VCC modul 3V3, I/O ke GPIO 13).
#include <Arduino.h>
#include <unity.h>
#include "soc/gpio_struct.h"
#include "soc/gpio_sig_map.h"
#include "soc/gpio_periph.h"
#include "soc/io_mux_reg.h"

#include "perangkat.h"

static int level() { return (GPIO.in >> PIN_BUZZ) & 1; }

// Hitung sampel LOW selama `us` mikrodetik.
static int hitung_low(uint32_t us, int *total)
{
    int low = 0, n = 0;
    const uint32_t t0 = micros();
    while (micros() - t0 < us) {
        low += !level();
        n++;
    }
    *total = n;
    return low;
}

// Jebakan SPI: SPI.begin(9, -1, 8) menjadikan GPIO 13 MISO (INPUT). Bila
// itu terjadi sesudah LEDC terpasang, pin lepas dari LEDC dan buzzer bisu.
void test_pin_dipegang_ledc_setelah_spi_dan_tft(void)
{
    const auto &cfg = GPIO.func_out_sel_cfg[PIN_BUZZ];
    TEST_ASSERT_EQUAL_MESSAGE(LEDC_LS_SIG_OUT0_IDX + KANAL_BUZZ, cfg.func_sel,
        "GPIO 13 tidak tersambung ke LEDC: SPI.begin dipanggil sesudah pemasangan buzzer?");
    TEST_ASSERT_EQUAL_MESSAGE(1, cfg.inv_sel, "keluaran LEDC tidak dibalik (output_invert)");
    TEST_ASSERT_TRUE_MESSAGE((GPIO.enable >> PIN_BUZZ) & 1, "output GPIO 13 nonaktif (pin dijadikan INPUT)");
}

// Modul aktif LOW: diam harus HIGH terus, tanpa satu sampel LOW pun.
void test_diam_berarti_high(void)
{
    buzzer(false);
    delay(5);
    int n;
    const int low = hitung_low(5000, &n);
    TEST_ASSERT_EQUAL_MESSAGE(0, low, "pin LOW saat diam: modul aktif-LOW akan berbunyi terus");
}

// Bunyi = gelombang kotak NADA_HZ, kira-kira separuh LOW separuh HIGH.
void test_bunyi_gelombang_kotak(void)
{
    buzzer(true);
    delay(5);
    int n;
    const int low = hitung_low(5000, &n);
    buzzer(false);
    const float porsi = (float)low / n;
    char pesan[64];
    snprintf(pesan, sizeof pesan, "porsi LOW %.2f dari %d sampel", porsi, n);
    TEST_ASSERT_FLOAT_WITHIN_MESSAGE(0.15f, 0.5f, porsi, pesan);
}

void test_bip_untuk_didengar(void)
{
    Serial.println("DENGARKAN: tiga bip pendek 2 kHz.");
    for (int i = 0; i < 3; i++) {
        buzzer(true);
        delay(80);
        buzzer(false);
        delay(250);
    }
    TEST_ASSERT_EQUAL(1, level());
}

void setUp(void) {}
void tearDown(void) {}

void setup()
{
    perangkat_mulai();            // urutan yang sama dengan firmware utama
    PIN_INPUT_ENABLE(GPIO_PIN_MUX_REG[PIN_BUZZ]);   // supaya level pin bisa dibaca balik
    Serial.begin(115200);
    delay(2000);
    UNITY_BEGIN();
    RUN_TEST(test_pin_dipegang_ledc_setelah_spi_dan_tft);
    RUN_TEST(test_diam_berarti_high);
    RUN_TEST(test_bunyi_gelombang_kotak);
    RUN_TEST(test_bip_untuk_didengar);
    UNITY_END();
}

void loop() {}
