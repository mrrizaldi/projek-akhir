#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "serial_cmd.h"

#include <Arduino.h>
#include <stdio.h>

#include "acquisition.h"
#include "power.h"
#include "ecg_mqtt.h"
#include "gate.h"
#include "classifier.h"
#include "app_settings.h"
#include "menu.h"
#include "board.h"
#include "recorder.h"
#include "power.h"
#include "display.h"
#include "buttons.h"

constexpr uint32_t WAIT_DIGIT_MS = 500;

static int read_number()
{
    int v = -1;
    for (int k = 0; k < 3; k++) {
        const uint32_t t0 = millis();
        while (!Serial.available() && millis() - t0 < WAIT_DIGIT_MS) {}
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
    const classifier_stats_t &h = classifier_stats();
    Serial.printf("status: rec=%d n=%u | replay=%d | quality %s | beat %d "
                  "(%d arrhythmia, %d withheld) | queue %u | missed %u (tick %u) | "
                  "LO %d %d | raw %d..%d swing %d clipping %d\n"
                  "        mqtt %s | sent %u | backlog %u/%u | lost %u | "
                  "failed %u | packets %u/%u PDSR %.1f%% | device delay avg %u ms "
                  "max %u ms | RTT max %u ms (slow %u) | RSSI %d dBm | epoch_ms %llu\n"
                  "        INA219 %s | mute %d | freeze %d | skip %d | power %d | "
                  "source %s %d | menu %d | pause %d\n",
                  (int)recorder_active(), (unsigned)recorder_n(), (int)acquisition_replay(),
                  gate_phase_name(), h.total, h.arrhythmia, h.withheld,
                  (unsigned)acquisition_fill(), (unsigned)acquisition_missed(), (unsigned)acquisition_tick_lost(),
                  digitalRead(PIN_LOP), digitalRead(PIN_LON),
                  q.raw_min, q.raw_max, q.swing_clean, (int)q.clipping,
                  ecg_mqtt_status_serial(), (unsigned)ecg_mqtt_sent(),
                  (unsigned)ecg_mqtt_queue_n(), (unsigned)ecg_mqtt_queue_capacity(),
                  (unsigned)ecg_mqtt_queue_lost(), (unsigned)ecg_mqtt_failed(),
                  (unsigned)ecg_mqtt_packet_ack(), (unsigned)ecg_mqtt_packet_send(),
                  ecg_mqtt_packet_send()
                      ? 100.0 * ecg_mqtt_packet_ack() / ecg_mqtt_packet_send() : 0.0,
                  (unsigned)(h.latency_n ? h.latency_sum / h.latency_n : 0), (unsigned)h.latency_max,
                  (unsigned)ecg_mqtt_rtt_max(), (unsigned)ecg_mqtt_rtt_slow(),
                  ecg_mqtt_rssi(), (unsigned long long)ecg_mqtt_epoch_ms(),
                  power_ina_text(), (int)display_mute(), (int)display_freeze(),
                  (int)gate_skip(), power_mode(),
                  acquisition_source() == SOURCE_ADC ? "adc"
                  : acquisition_source() == SOURCE_REFERENCE ? "reference" : "recording",
                  acquisition_source_recording(), (int)menu_is_open(), (int)recorder_paused());
}

static void list_wifi()
{
    for (int i = 0; i < settings_wifi_n(); i++)
        Serial.printf("wifi %c%d %s\n", i == settings_wifi() ? '*' : ' ', i, settings_wifi_name(i));
}

static void list_brokers()
{
    for (int i = 0; i < settings_broker_n(); i++)
        Serial.printf("broker %c%d %s  %s:%d\n", i == settings_broker() ? '*' : ' ', i,
                      settings_broker_name(i), settings_broker_host(i), settings_broker_port(i));
}

void serial_cmd_service(void)
{
    if (!Serial.available()) return;
    const char c = Serial.read();
    if (c == 'r') recorder_toggle();
    else if (c == 'j') recorder_pause();
    else if (c == 'd') {
        const int n = read_number();
        if (!recorder_active()) recorder_dump(n);
        else Serial.println("Recording in progress.");
    }
    else if (c == 'l') recorder_print_list();
    else if (c == 'h') {
        const int n = read_number();
        if (n > 0) recorder_delete(n);
        else Serial.println("h<n>: recording number, see 'l'");
    }
    else if (c == 'y') acquisition_switch_source();
    else if (c == 'p') {
        const uint32_t t0 = millis();
        while (!Serial.available() && millis() - t0 < WAIT_DIGIT_MS) {}
        const char d = Serial.available() ? Serial.read() : 0;
        power_set_mode(d >= '0' && d <= '5' ? d - '0' : -1);
    }
    else if (c == 'k') {
        gate_set_skip(!gate_skip());
        Serial.printf("skip calibration gate %s (bench only: the method requires "
                      "10-15 min of stabilisation + 30 s of calm RR)\n",
                      gate_skip() ? "ON" : "OFF");
    }
    else if (c == 'm') settings_set_wifi_active(!settings_wifi_active());
    else if (c == 'q') {
        gate_set_report(!gate_report());
        Serial.printf("quality report %s\n", gate_report() ? "ON" : "OFF");
    }
    else if (c == 's') status();
    else if (c == 'v' || c == 'V') {
        char b[8];
        const int n = c == 'v' ? read_number() : -1;
        snprintf(b, sizeof b, n < 0 ? "%c" : "%c%d", c, n);
        power_serial(b);
    }
    else if (c == 'w') {
        const int n = read_number();
        if (n < 0) list_wifi();
        else if (!settings_choose_wifi(n) && !recorder_active()) Serial.printf("wifi %d not found, see 'w'\n", n);
    }
    else if (c == 't' || c == 'T') {
        const uint32_t t0 = millis();
        while (!Serial.available() && millis() - t0 < WAIT_DIGIT_MS) {}
        const int n = Serial.peek() - '0';
        if (n < 1 || n > 3) Serial.println("t<1-3> / T<1-3>: B1-B3 short / hold");
        else { Serial.read(); buttons_inject(n - 1, c == 'T' ? BUTTON_LONG : BUTTON_SHORT); }
    }
    else if (c == 'b') {
        const int n = read_number();
        if (n < 0) list_brokers();
        else if (!settings_choose_broker(n) && !recorder_active()) Serial.printf("broker %d not found, see 'b'\n", n);
    }
}
#endif
