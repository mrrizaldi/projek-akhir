// Ukur daya. Kontrak: include/daya.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "daya.h"

#include <Arduino.h>
#include "esp_wifi.h"

#include "akuisisi.h"
#include "ecg_mqtt.h"
#include "ina219.h"
#include "perangkat.h"

constexpr uint32_t JENDELA_DAYA_MS = 10000;

static bool ina_ada;
static int mode_daya = -1;
static uint32_t beat_dsp;          // beat keluar dari ecg_live, termasuk saat kalibrasi
static bool mulai_ulang;

void daya_mulai(void) { ina_ada = ina219_mulai(I2C_SDA, I2C_SCL); }
bool daya_ina_ada(void) { return ina_ada; }
int daya_mode(void) { return mode_daya; }
bool daya_tahap(int t) { return mode_daya < 0 || mode_daya >= t; }
void daya_hitung_beat(void) { beat_dsp++; }

const char *daya_ina_teks(void)
{
    static char teks[48];
    float mA, V;
    if (ina_ada && ina219_baca(R_SHUNT, &mA, &V))
        snprintf(teks, sizeof teks, "I=%.1f mA V=%.3f V P=%.0f mW", mA, V, mA * V);
    else
        snprintf(teks, sizeof teks, "tidak menjawab");
    return teks;
}

void daya_set_mode(int m)
{
    static bool wifi_mati;
    mode_daya = m;
    akuisisi_timer(m != 0);
    // esp_wifi_stop/start, bukan WiFi.mode(WIFI_OFF): yang terakhir ikut
    // men-deinit driver dan berebut dengan task WiFi (panic LoadProhibited di core 0).
    if (m >= 0 && m < 5) {
        if (!wifi_mati) { ecg_mqtt_set_aktif(0); esp_wifi_stop(); }
        wifi_mati = true;
    } else if (wifi_mati) {        // p5 / normal: radio kembali dengan setelan ecg_mqtt_mulai()
        esp_wifi_start();
        ecg_mqtt_mulai();
        ecg_mqtt_set_aktif(1);
        wifi_mati = false;
    }
    mulai_ulang = true;
    if (m < 0) Serial.println("daya: mode normal");
    else       Serial.printf("daya: mode p%d, jendela %lu s\n", m, (unsigned long)(JENDELA_DAYA_MS / 1000));
}

// Rata-rata INA219 per jendela tetap. Dibaca tiap 100 ms (> 68 ms konversi 128
// sampel), jadi tiap bacaan adalah rata-rata baru. Baris pertama sesudah ganti
// mode memuat transien; pencatat (model/scripts/measure_power.py) membuangnya.
// Format baris 'DAYA' di-parse pencatat itu: jangan diubah.
void daya_layani(void)
{
    static uint32_t t_baca, t_jendela, beat0, lewat0;
    static double jml, jml2, jml_v;
    static int n;
    if (mode_daya < 0 || !ina_ada || millis() - t_baca < 100) return;
    t_baca = millis();
    if (mulai_ulang) {
        mulai_ulang = false;
        jml = jml2 = jml_v = 0; n = 0;
        t_jendela = millis(); beat0 = beat_dsp; lewat0 = akuisisi_lewat();
    }
    float mA, V;
    if (ina219_baca(R_SHUNT, &mA, &V)) { jml += mA; jml2 += (double)mA * mA; jml_v += V; n++; }
    if (millis() - t_jendela < JENDELA_DAYA_MS || n == 0) return;
    const double i = jml / n, v = jml_v / n;
    Serial.printf("DAYA p%d n=%d I=%.2f sd=%.2f mA V=%.3f P=%.1f mW beat=%u lewat=%u replay=%d\n",
                  mode_daya, n, i, sqrt(fmax(jml2 / n - i * i, 0.0)), v, i * v,
                  (unsigned)(beat_dsp - beat0), (unsigned)(akuisisi_lewat() - lewat0),
                  (int)akuisisi_replay());
    mulai_ulang = true;
}
#endif
