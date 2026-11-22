#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "acquisition.h"

#include <Arduino.h>
#include "driver/adc.h"
#include "esp_cpu.h"

#include "gate.h"
#include "classifier.h"
#include "app_settings.h"
#include "board.h"
#include "recorder.h"
#include "golden_ref.h"

static volatile uint16_t queue[QUEUE_N];
static volatile size_t write_index, read_index;
static volatile uint32_t n_missed, n_tick_lost;
static uint32_t cycles_per_sample, cycles_previous;
constexpr uint32_t HZ_PER_MHZ = 1000000UL;
constexpr uint32_t DIVISOR_HALF_PERIOD = 2;
static hw_timer_t *timer;

static int source, source_recording;
static const uint16_t *volatile rp_data;
static volatile size_t rp_n, replay_i;
static uint16_t *recording_buf;
static bool attach_source(int s, int number);

constexpr float SCALE_REPLAY = 1000.0f;
constexpr float OFFSET_REPLAY = 2048.0f;

static uint16_t sim_counts[GOLDEN_N];

static void IRAM_ATTR count_lost_ticks()
{
    const uint32_t current = esp_cpu_get_ccount();
    const uint32_t interval = current - cycles_previous;
    cycles_previous = current;
    const uint32_t half = cycles_per_sample / DIVISOR_HALF_PERIOD;
    if (interval > cycles_per_sample + half)
        n_tick_lost += (interval + half) / cycles_per_sample - 1;
}

static void IRAM_ATTR on_timer()
{
    count_lost_ticks();
    const size_t next = (write_index + 1) % QUEUE_N;
    if (next == read_index) { n_missed++; return; }
    if (rp_data) {
        queue[write_index] = rp_data[replay_i];
        if (++replay_i >= rp_n) replay_i = 0;
    } else {
        queue[write_index] = (uint16_t)adc1_get_raw(CHANNEL_ECG);
    }
    write_index = next;
}

void acquisition_begin(void)
{
    for (size_t i = 0; i < GOLDEN_N; i++) {
        float v = golden_raw[i] * SCALE_REPLAY + OFFSET_REPLAY;
        if (v < 0.0f) v = 0.0f;
        if (v > 4095.0f) v = 4095.0f;
        sim_counts[i] = (uint16_t)v;
    }
    timer = timerBegin(0, 80, true);
    timerAttachInterrupt(timer, &on_timer, true);
    timerAlarmWrite(timer, 1000000 / ECG_FS, true);
    if (!attach_source(settings_source(), settings_source_recording())) attach_source(SOURCE_ADC, 0);
    cycles_per_sample = getCpuFrequencyMhz() * HZ_PER_MHZ / ECG_FS;
    cycles_previous = esp_cpu_get_ccount();
    timerAlarmEnable(timer);
}

bool acquisition_fetch(uint16_t *sample)
{
    if (read_index == write_index) return false;
    *sample = queue[read_index];
    read_index = (read_index + 1) % QUEUE_N;
    return true;
}

size_t acquisition_fill(void) { return (write_index - read_index + QUEUE_N) % QUEUE_N; }
uint32_t acquisition_missed(void) { return n_missed + n_tick_lost; }
uint32_t acquisition_tick_lost(void) { return n_tick_lost; }
void acquisition_zero_missed(void) { n_missed = n_tick_lost = 0; }
bool acquisition_replay(void) { return source != SOURCE_ADC; }
int acquisition_source(void) { return source; }
int acquisition_source_recording(void) { return source_recording; }

void acquisition_timer(bool running)
{
    if (!running) { timerAlarmDisable(timer); return; }
    cycles_previous = esp_cpu_get_ccount();
    timerAlarmEnable(timer);
}

static bool attach_source(int s, int number)
{
    if (s == SOURCE_RECORDING) {
        if (!recording_buf) recording_buf = (uint16_t *)ps_malloc(RECORDER_SAMPLE_MAX * sizeof(uint16_t));
        const size_t n = recording_buf ? recorder_load(number, recording_buf, RECORDER_SAMPLE_MAX) : 0;
        if (n < ECG_FS) {
            Serial.printf("replay recording %d FAILED to load (%u samples)\n", number, (unsigned)n);
            return false;
        }
        rp_n = n;
        rp_data = recording_buf;
    } else if (s == SOURCE_REFERENCE) {
        rp_n = GOLDEN_N;
        rp_data = sim_counts;
    } else {
        s = SOURCE_ADC;
        rp_data = nullptr;
    }
    replay_i = 0;
    source = s;
    source_recording = s == SOURCE_RECORDING ? number : 0;
    return true;
}

bool acquisition_set_source(int s, int number, bool save)
{
    if (recorder_reject("change source")) return false;
    acquisition_timer(false);
    const bool ok = attach_source(s, number);
    acquisition_timer(true);
    if (!ok) return false;
    if (save) settings_set_source(source, source_recording);
    gate_begin_session();
    classifier_reset();
    if (source == SOURCE_RECORDING)
        Serial.printf("replay ON (recording %03d, %u samples)\n", source_recording, (unsigned)rp_n);
    else
        Serial.printf("replay %s\n", source == SOURCE_REFERENCE ? "ON (golden_raw)" : "OFF (ADC)");
    return true;
}

void acquisition_switch_source(void)
{
    acquisition_set_source(source == SOURCE_ADC ? SOURCE_REFERENCE : SOURCE_ADC, 0, true);
}
#endif
