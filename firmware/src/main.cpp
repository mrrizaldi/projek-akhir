#ifndef PIO_UNIT_TESTING
#include <Arduino.h>

#include "acquisition.h"
#include "power.h"
#include "ecg_live.h"
#include "ecg_mqtt.h"
#include "gate.h"
#include "ina219.h"
#include "classifier.h"
#include "konfig.h"
#include "menu.h"
#include "board.h"
#include "recorder.h"
#include "serial_cmd.h"
#include "diagnostics.h"
#include "power.h"
#include "display.h"
#include "buttons.h"

constexpr uint32_t CLICK_MS = 20, BEEP_LONG_MS = 60;

static void service_buttons()
{
    int i, e;
    while ((e = buttons_event(&i)) != BUTTON_NONE) {
        if (e == BUTTON_PRESS) display_sound(CLICK_MS);
        if (e == BUTTON_LONG) display_sound(BEEP_LONG_MS);
        if (e == BUTTON_SHORT || e == BUTTON_LONG)
            Serial.printf("tombol B%d %s\n", i + 1, e == BUTTON_LONG ? "tahan" : "pendek");
        if (menu_is_open()) { menu_button(i, e); continue; }
        if (e == BUTTON_SHORT) {
            if (i == 0) display_set_mute(!display_mute());
            if (i == 1) display_set_freeze(!display_freeze());
            if (i == 2) { if (recorder_active()) recorder_pause(); else recorder_toggle(); }
        }
        if (e == BUTTON_LONG && i == 1) { menu_open(); continue; }
        if (e == BUTTON_LONG && i == 2 && recorder_active()) recorder_toggle();
        display_draw_button(i);
    }
}

void setup()
{
    board_begin();
    Serial.begin(115200);
    delay(1500);
    power_begin();
    display_begin();

    ecg_mqtt_beat_t *ring = (ecg_mqtt_beat_t *)ps_malloc(
        ECG_MQTT_QUEUE_TARGET * sizeof(ecg_mqtt_beat_t));
    if (ring) {
        ecg_mqtt_queue_attach(ring, ECG_MQTT_QUEUE_TARGET);
        Serial.printf("backlog: %u beat di PSRAM (%u KB, %u entri x %u B)\n",
                      ECG_MQTT_QUEUE_TARGET,
                      (unsigned)(ECG_MQTT_QUEUE_TARGET * sizeof(ecg_mqtt_beat_t) / 1024),
                      ECG_MQTT_QUEUE_TARGET, (unsigned)sizeof(ecg_mqtt_beat_t));
    } else {
        Serial.printf("PERINGATAN: PSRAM ring gagal, backlog turun ke %u beat\n",
                      ECG_MQTT_QUEUE_MIN);
    }
    recorder_prepare();

    classifier_begin();
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
                  ECG_FS, (unsigned)QUEUE_N, (unsigned)classifier_arena(),
                  classifier_threshold(), PIN_BTN[0], PIN_BTN[1], PIN_BTN[2],
                  I2C_SDA, I2C_SCL, INA219_ADDRESS, power_ina_present() ? "siap" : "TIDAK TERDETEKSI",
                  TFT_W, TFT_H, PIN_BUZZ, (unsigned)TONE_HZ);
}

void loop()
{
    static ecg_beat_t beat;

    uint16_t s;
    if (acquisition_fetch(&s)) {
        const float sample = (float)s;
        recorder_sample(s);

        const bool dsp = power_stage(2), cnn = power_stage(3), ui = power_stage(4);
        const int has_beat = dsp ? ecg_live_push(sample, &beat) : 0;
        if (dsp) gate_assess_quality(sample);

        bool arrhythmia = false;
        if (has_beat) {
            power_count_beat();
            gate_assess_phase(beat);
            if (gate_phase() == PHASE_CALIBRATION) gate_report_calibration(beat);
            else if (cnn) arrhythmia = classifier_process(beat);
            if (ui) display_beat(beat, arrhythmia);
        }
        if (ui) display_sample();
    }

    recorder_service();
    ecg_mqtt_service();
    power_service();
    power_sweep_tick();
    serial_cmd_service();
    service_buttons();
    menu_service();
    display_service();
}
#endif
