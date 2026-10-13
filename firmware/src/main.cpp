// Firmware utama: akuisisi + klasifikasi aritmia langsung di alat, dengan
// tampilan TFT, bip buzzer per detak, tiga tombol, rekaman LittleFS, dan
// publikasi MQTT. File ini hanya merangkai modul; pin map PCB ada di
// include/perangkat.h.
//
//   akuisisi    ISR 360 Hz -> antrean, sumber ADC / replay
//   gerbang     kualitas sinyal + fase kalibrasi
//   klasifikasi TFLM INT8 + publikasi ke antrean MQTT
//   tampilan    TFT, NeoPixel, buzzer        tombol  debounce + event
//   rekam       rekaman bernomor LittleFS    daya    INA219 + tangga p0-p5
//   konfig      daftar WiFi/broker + NVS     serial_cmd  perintah serial
#ifndef PIO_UNIT_TESTING
#include <Arduino.h>

#include "akuisisi.h"
#include "daya.h"
#include "ecg_live.h"
#include "ecg_mqtt.h"
#include "gerbang.h"
#include "ina219.h"
#include "klasifikasi.h"
#include "konfig.h"
#include "perangkat.h"
#include "rekam.h"
#include "serial_cmd.h"
#include "tampilan.h"
#include "tombol.h"

// B1 bisu/bunyi bip detak (aksi saat DILEPAS, karena tahan punya arti lain),
// B1 tahan = ganti sumber seperti 'y', B2 bekukan gelombang + bip, B3 mulai /
// simpan rekaman seperti 'r'. Tiap tekanan berbunyi klik.
static void layani_tombol()
{
    int i, e;
    while ((e = tombol_event(&i)) != TOMBOL_TIDAK) {
        if (e == TOMBOL_TEKAN) {
            tampilan_bunyi(20);
            if (i == 1) tampilan_set_beku(!tampilan_beku());
            if (i == 2) rekam_toggle();
            Serial.printf("tombol B%d (GPIO%d)\n", i + 1, PIN_BTN[i]);
        }
        if (e == TOMBOL_PENDEK && i == 0) tampilan_set_bisu(!tampilan_bisu());
        if (e == TOMBOL_LAMA) { if (i == 0) akuisisi_ganti_sumber(); }
        else tampilan_gambar_tombol(i);
    }
}

void setup()
{
    perangkat_mulai();              // PERTAMA: buzzer diam secepatnya, urutan SPI di dalamnya
    Serial.begin(115200);
    delay(1500);
    daya_mulai();
    tampilan_mulai();

    // Ring backlog MQTT di PSRAM, target bab3.tex: +-27.000 rekaman (4-7 jam).
    // Satu entri 40 byte -> ~1,08 MB dari 8 MB. Kalau gagal, ecg_mqtt jatuh ke
    // cadangan statis 64 beat: backlog pendek jauh lebih baik daripada mati.
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
    gerbang_mulai_sesi();
    konfig_mulai();
    ecg_mqtt_mulai();               // non-blocking: sambungan diurus di loop()
    akuisisi_mulai();               // terakhir: ISR mulai mengisi antrean

    Serial.printf("\n=== MONITOR ARITMIA SIAP ===\n"
                  "fs=%u Hz  antrean=%u  arena=%u B  threshold=%.2f\n"
                  "tombol B1/B2/B3 = GPIO%d/%d/%d (bisu, beku, rekam)  |  "
                  "serial: r/d/l/h/s/q/y/m/k/p/w/b\n"
                  "INA219 (SDA %d, SCL %d, 0x%02X): %s  |  TFT ST7789 %dx%d  |  buzzer GPIO%d @%u Hz\n",
                  ECG_FS, (unsigned)ANTRE_N, (unsigned)klasifikasi_arena(),
                  klasifikasi_ambang(), PIN_BTN[0], PIN_BTN[1], PIN_BTN[2],
                  I2C_SDA, I2C_SCL, INA219_ALAMAT, daya_ina_ada() ? "siap" : "TIDAK TERDETEKSI",
                  TFT_W, TFT_H, PIN_BUZZ, (unsigned)NADA_HZ);
}

void loop()
{
    static ecg_beat_t beat;

    // Kuras antrean ISR. Satu sampel per iterasi supaya tombol & serial tetap
    // responsif; beban 3% membuat antrean selalu terkejar.
    uint16_t s;
    if (akuisisi_ambil(&s)) {
        const float sampel = (float)s;
        rekam_sampel(s);

        const bool dsp = daya_tahap(2), cnn = daya_tahap(3), ui = daya_tahap(4);
        const int ada_beat = dsp ? ecg_live_push(sampel, &beat) : 0;
        if (dsp) gerbang_nilai_kualitas(sampel);   // SETELAH push: baca sampel tersaring terbaru

        bool aritmia = false;
        if (ada_beat) {
            daya_hitung_beat();
            gerbang_nilai_fase(beat);
            // Selama kalibrasi detektor tetap jalan (RR-nya menilai kelayakan
            // sinyal); yang dilewati cuma CNN-nya.
            if (gerbang_fase() == FASE_KALIBRASI) gerbang_lapor_kalibrasi(beat);
            else if (cnn) aritmia = klasifikasi_proses(beat);
            if (ui) tampilan_beat(beat, aritmia);
        }
        if (ui) tampilan_sampel();
    }

    // Di luar cabang "ada sampel": sambung ulang & kuras backlog harus jalan
    // walau antrean ADC sedang kosong.
    ecg_mqtt_layani();
    daya_layani();
    daya_tangga_tick();
    serial_cmd_layani();
    layani_tombol();
    tampilan_layani();
}
#endif
