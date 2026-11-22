#ifndef PIO_UNIT_TESTING
#include <Arduino.h>

#include "acquisition.h"
#include "daya.h"
#include "ecg_live.h"
#include "ecg_mqtt.h"
#include "gate.h"
#include "ina219.h"
#include "klasifikasi.h"
#include "konfig.h"
#include "menu.h"
#include "board.h"
#include "rekam.h"
#include "serial_cmd.h"
#include "diagnosa.h"
#include "daya.h"
#include "tampilan.h"
#include "buttons.h"

constexpr uint32_t KLIK_MS = 20, BIP_LAMA_MS = 60;

static void layani_tombol()
{
    int i, e;
    while ((e = buttons_event(&i)) != BUTTON_NONE) {
        if (e == BUTTON_PRESS) tampilan_bunyi(KLIK_MS);
        if (e == BUTTON_LONG) tampilan_bunyi(BIP_LAMA_MS);
        if (e == BUTTON_SHORT || e == BUTTON_LONG)
            Serial.printf("tombol B%d %s\n", i + 1, e == BUTTON_LONG ? "tahan" : "pendek");
        if (menu_terbuka()) { menu_tombol(i, e); continue; }
        if (e == BUTTON_SHORT) {
            if (i == 0) tampilan_set_bisu(!tampilan_bisu());
            if (i == 1) tampilan_set_beku(!tampilan_beku());
            if (i == 2) { if (rekam_aktif()) rekam_jeda(); else rekam_toggle(); }
        }
        if (e == BUTTON_LONG && i == 1) { menu_buka(); continue; }
        if (e == BUTTON_LONG && i == 2 && rekam_aktif()) rekam_toggle();
        tampilan_gambar_tombol(i);
    }
}

void setup()
{
    board_begin();
    Serial.begin(115200);
    delay(1500);
    daya_mulai();
    tampilan_mulai();

    ecg_mqtt_beat_t *ring = (ecg_mqtt_beat_t *)ps_malloc(
        ECG_MQTT_ANTRE_TARGET * sizeof(ecg_mqtt_beat_t));
    if (ring) {
        ecg_mqtt_antre_pasang(ring, ECG_MQTT_ANTRE_TARGET);
        Serial.printf("backlog: %u beat di PSRAM (%u KB, %u entri x %u B)\n",
                      ECG_MQTT_ANTRE_TARGET,
                      (unsigned)(ECG_MQTT_ANTRE_TARGET * sizeof(ecg_mqtt_beat_t) / 1024),
                      ECG_MQTT_ANTRE_TARGET, (unsigned)sizeof(ecg_mqtt_beat_t));
    } else {
        Serial.printf("PERINGATAN: PSRAM ring gagal, backlog turun ke %u beat\n",
                      ECG_MQTT_ANTRE_MIN);
    }
    rekam_siapkan();

    klasifikasi_mulai();
    gate_begin_session();
    konfig_mulai();
    setenv("TZ", "WIB-7", 1);
    tzset();
    acquisition_begin();

    Serial.printf("\n=== MONITOR ARITMIA SIAP ===\n"
                  "fs=%u Hz  antrean=%u  arena=%u B  threshold=%.2f\n"
                  "tombol B1/B2/B3 = GPIO%d/%d/%d (bisu, beku, rekam/jeda/lanjut; tahan B3 = simpan, "
                  "tahan B2 = menu)  |  serial: r/j/d/l/h/s/q/y/m/k/p/w/b/v/V/t/T\n"
                  "INA219 (SDA %d, SCL %d, 0x%02X): %s  |  TFT ST7789 %dx%d  |  buzzer GPIO%d @%u Hz\n",
                  ECG_FS, (unsigned)QUEUE_N, (unsigned)klasifikasi_arena(),
                  klasifikasi_ambang(), PIN_BTN[0], PIN_BTN[1], PIN_BTN[2],
                  I2C_SDA, I2C_SCL, INA219_ALAMAT, daya_ina_ada() ? "siap" : "TIDAK TERDETEKSI",
                  TFT_W, TFT_H, PIN_BUZZ, (unsigned)TONE_HZ);
}

void loop()
{
    static ecg_beat_t beat;

    uint16_t s;
    if (acquisition_fetch(&s)) {
        const float sampel = (float)s;
        rekam_sampel(s);

        const bool dsp = daya_tahap(2), cnn = daya_tahap(3), ui = daya_tahap(4);
        const int ada_beat = dsp ? ecg_live_push(sampel, &beat) : 0;
        if (dsp) gate_assess_quality(sampel);

        bool aritmia = false;
        if (ada_beat) {
            daya_hitung_beat();
            gate_assess_phase(beat);
            if (gate_phase() == PHASE_CALIBRATION) gate_report_calibration(beat);
            else if (cnn) aritmia = klasifikasi_proses(beat);
            if (ui) tampilan_beat(beat, aritmia);
        }
        if (ui) tampilan_sampel();
    }

    rekam_layani();
    ecg_mqtt_layani();
    daya_layani();
    daya_tangga_tick();
    serial_cmd_layani();
    layani_tombol();
    menu_layani();
    tampilan_layani();
}
#endif
