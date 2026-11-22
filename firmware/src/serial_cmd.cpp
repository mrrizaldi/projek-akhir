#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "serial_cmd.h"

#include <Arduino.h>
#include <stdio.h>

#include "acquisition.h"
#include "power.h"
#include "ecg_mqtt.h"
#include "gate.h"
#include "classifier.h"
#include "konfig.h"
#include "menu.h"
#include "board.h"
#include "recorder.h"
#include "power.h"
#include "display.h"
#include "buttons.h"

constexpr uint32_t TUNGGU_DIGIT_MS = 500;

static int angka()
{
    int v = -1;
    for (int k = 0; k < 3; k++) {
        const uint32_t t0 = millis();
        while (!Serial.available() && millis() - t0 < TUNGGU_DIGIT_MS) {}
        const int c = Serial.peek();
        if (c < '0' || c > '9') break;
        Serial.read();
        v = (v < 0 ? 0 : v * 10) + (c - '0');
    }
    return v;
}

static void status()
{
    const gate_quality_t &q = gate_quality();
    const classifier_count_t &h = classifier_count();
    Serial.printf("status: rekam=%d n=%u | replay=%d | kualitas %s | beat %d "
                  "(%d aritmia, %d ditahan) | antrean %u | sampel hilang %u (tick %u) | "
                  "LO %d %d | mentah %d..%d ayun %d clipping %d\n"
                  "        mqtt %s | terkirim %u | backlog %u/%u | hilang %u | "
                  "gagal %u | paket %u/%u PDSR %.1f%% | tunda alat rata %u ms "
                  "maks %u ms | RTT maks %u ms (lambat %u) | RSSI %d dBm | epoch_ms %llu\n"
                  "        INA219 %s | bisu %d | beku %d | lewati %d | daya %d | "
                  "sumber %s %d | menu %d | jeda %d\n",
                  (int)recorder_active(), (unsigned)recorder_n(), (int)acquisition_replay(),
                  gate_phase_name(), h.total, h.arrhythmia, h.withheld,
                  (unsigned)acquisition_fill(), (unsigned)acquisition_missed(), (unsigned)acquisition_tick_lost(),
                  digitalRead(PIN_LOP), digitalRead(PIN_LON),
                  q.raw_min, q.raw_max, q.swing_clean, (int)q.clipping,
                  ecg_mqtt_status(), (unsigned)ecg_mqtt_terkirim(),
                  (unsigned)ecg_mqtt_antre_n(), (unsigned)ecg_mqtt_antre_kapasitas(),
                  (unsigned)ecg_mqtt_antre_hilang(), (unsigned)ecg_mqtt_gagal(),
                  (unsigned)ecg_mqtt_paket_ack(), (unsigned)ecg_mqtt_paket_kirim(),
                  ecg_mqtt_paket_kirim()
                      ? 100.0 * ecg_mqtt_paket_ack() / ecg_mqtt_paket_kirim() : 0.0,
                  (unsigned)(h.latency_n ? h.latency_sum / h.latency_n : 0), (unsigned)h.latency_max,
                  (unsigned)ecg_mqtt_rtt_maks(), (unsigned)ecg_mqtt_rtt_lambat(),
                  ecg_mqtt_rssi(), (unsigned long long)ecg_mqtt_epoch_ms(),
                  power_ina_text(), (int)display_mute(), (int)display_freeze(),
                  (int)gate_skip(), power_mode(),
                  acquisition_source() == SOURCE_ADC ? "adc"
                  : acquisition_source() == SOURCE_REFERENCE ? "acuan" : "rekaman",
                  acquisition_source_recording(), (int)menu_terbuka(), (int)recorder_paused());
}

static void daftar_wifi()
{
    for (int i = 0; i < konfig_wifi_n(); i++)
        Serial.printf("wifi %c%d %s\n", i == konfig_wifi() ? '*' : ' ', i, konfig_wifi_nama(i));
}

static void daftar_broker()
{
    for (int i = 0; i < konfig_broker_n(); i++)
        Serial.printf("broker %c%d %s  %s:%d\n", i == konfig_broker() ? '*' : ' ', i,
                      konfig_broker_nama(i), konfig_broker_host(i), konfig_broker_port(i));
}

void serial_cmd_layani(void)
{
    if (!Serial.available()) return;
    const char c = Serial.read();
    if (c == 'r') recorder_toggle();
    else if (c == 'j') recorder_pause();
    else if (c == 'd') {
        const int n = angka();
        if (!recorder_active()) recorder_dump(n);
        else Serial.println("Sedang merekam.");
    }
    else if (c == 'l') recorder_print_list();
    else if (c == 'h') {
        const int n = angka();
        if (n > 0) recorder_delete(n);
        else Serial.println("h<n>: nomor rekaman, lihat 'l'");
    }
    else if (c == 'y') acquisition_switch_source();
    else if (c == 'p') {
        const uint32_t t0 = millis();
        while (!Serial.available() && millis() - t0 < TUNGGU_DIGIT_MS) {}
        const char d = Serial.available() ? Serial.read() : 0;
        power_set_mode(d >= '0' && d <= '5' ? d - '0' : -1);
    }
    else if (c == 'k') {
        gate_set_skip(!gate_skip());
        Serial.printf("lewati gerbang kalibrasi %s (bench saja — bab3 menuntut "
                      "stabilisasi 10-15 menit + RR tenang 30 s)\n",
                      gate_skip() ? "ON" : "OFF");
    }
    else if (c == 'm') konfig_set_wifi_aktif(!konfig_wifi_aktif());
    else if (c == 'q') {
        gate_set_report(!gate_report());
        Serial.printf("laporan kualitas %s\n", gate_report() ? "ON" : "OFF");
    }
    else if (c == 's') status();
    else if (c == 'v' || c == 'V') {
        char b[8];
        const int n = c == 'v' ? angka() : -1;
        snprintf(b, sizeof b, n < 0 ? "%c" : "%c%d", c, n);
        power_serial(b);
    }
    else if (c == 'w') {
        const int n = angka();
        if (n < 0) daftar_wifi();
        else if (!konfig_pilih_wifi(n) && !recorder_active()) Serial.printf("wifi %d tidak ada, lihat 'w'\n", n);
    }
    else if (c == 't' || c == 'T') {
        const uint32_t t0 = millis();
        while (!Serial.available() && millis() - t0 < TUNGGU_DIGIT_MS) {}
        const int n = Serial.peek() - '0';
        if (n < 1 || n > 3) Serial.println("t<1-3> / T<1-3>: B1-B3 pendek / tahan");
        else { Serial.read(); buttons_inject(n - 1, c == 'T' ? BUTTON_LONG : BUTTON_SHORT); }
    }
    else if (c == 'b') {
        const int n = angka();
        if (n < 0) daftar_broker();
        else if (!konfig_pilih_broker(n) && !recorder_active()) Serial.printf("broker %d tidak ada, lihat 'b'\n", n);
    }
}
#endif
