#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "power.h"

#include <Arduino.h>
#include <LittleFS.h>
#include <time.h>
#include "esp_wifi.h"

#include "acquisition.h"
#include "ecg_mqtt.h"
#include "ina219.h"
#include "konfig.h"
#include "board.h"
#include "recorder.h"

#ifndef POWER_WINDOW_MS
#define POWER_WINDOW_MS 10000
#endif
#ifndef POWER_BLOCK
#define POWER_BLOCK 6
#endif
constexpr uint32_t WINDOW_POWER_MS = POWER_WINDOW_MS;
constexpr int SWEEP_N = 6;
constexpr uint32_t PERIOD_READ_INA219_MS = 100;

static bool ina_present;
static int mode_power = -1;
static uint32_t beat_dsp;
static bool restart_window;
static void sweep_record(int n, double i, double sd, double v, unsigned beat, unsigned missed);

void power_begin(void) { ina_present = ina219_begin(I2C_SDA, I2C_SCL); }
bool power_ina_present(void) { return ina_present; }
int power_mode(void) { return mode_power; }
bool power_stage(int t) { return mode_power < 0 || mode_power >= t; }
void power_count_beat(void) { beat_dsp++; }

const char *power_ina_text(void)
{
    static char text[48];
    float mA, V;
    if (ina_present && ina219_read(R_SHUNT, &mA, &V))
        snprintf(text, sizeof text, "I=%.1f mA V=%.3f V P=%.0f mW", mA, V, mA * V);
    else
        snprintf(text, sizeof text, "tidak menjawab");
    return text;
}

void power_set_mode(int m)
{
    static bool wifi_off;
    if (recorder_reject("mode daya")) return;
    mode_power = m;
    acquisition_timer(m != 0);
    if (m >= 0 && m < 5) {
        if (!wifi_off) { ecg_mqtt_set_active(0); esp_wifi_stop(); }
        wifi_off = true;
    } else if (wifi_off) {
        if (konfig_wifi_aktif()) {
            esp_wifi_start();
            ecg_mqtt_begin();
            ecg_mqtt_set_active(1);
        }
        wifi_off = false;
    }
    restart_window = true;
    if (m < 0) Serial.println("daya: mode normal");
    else       Serial.printf("daya: mode p%d, jendela %lu s\n", m, (unsigned long)(WINDOW_POWER_MS / 1000));
}

void power_service(void)
{
    static uint32_t t_read, t_window, beat0, missed0;
    static double sum, sum2, sum_v;
    static int n;
    if (mode_power < 0 || !ina_present || millis() - t_read < PERIOD_READ_INA219_MS) return;
    t_read = millis();
    if (restart_window) {
        restart_window = false;
        sum = sum2 = sum_v = 0; n = 0;
        t_window = millis(); beat0 = beat_dsp; missed0 = acquisition_missed();
    }
    float mA, V;
    if (ina219_read(R_SHUNT, &mA, &V)) { sum += mA; sum2 += (double)mA * mA; sum_v += V; n++; }
    if (millis() - t_window < WINDOW_POWER_MS || n == 0) return;
    const double i = sum / n, v = sum_v / n;
    const double sd = sqrt(fmax(sum2 / n - i * i, 0.0));
    const unsigned beat = beat_dsp - beat0, missed = acquisition_missed() - missed0;
    Serial.printf("DAYA p%d n=%d I=%.2f sd=%.2f mA V=%.3f P=%.1f mW beat=%u lewat=%u replay=%d\n",
                  mode_power, n, i, sd, v, i * v, beat, missed, (int)acquisition_replay());
    sweep_record(n, i, sd, v, beat, missed);
    restart_window = true;
}

struct window_t {
    char time[24];
    int8_t mode;
    uint16_t n;
    float i, sd, v;
    uint32_t beat, missed;
    bool replay;
};
static window_t windows[SWEEP_N * POWER_BLOCK];
static int windows_n;
static int step = -1;
static int step_window;
static uint32_t t_step;
static int source_start, recording_start;
static power_row_t results[SWEEP_N];
static int results_n;
static int file_last = -1;

static File open_dir(void)
{
    LittleFS.mkdir("/daya");
    return LittleFS.open("/daya");
}

bool power_sweep_active(void) { return step >= 0; }
int power_sweep_step(void) { return step; }

int power_sweep_result(power_row_t *out, int max_count)
{
    const int k = min(results_n, max_count);
    memcpy(out, results, k * sizeof *out);
    return k;
}

int power_sweep_file(void)
{
    if (file_last >= 0) return file_last;
    file_last = 0;
    File d = open_dir();
    if (d && d.isDirectory())
        for (File f = d.openNextFile(); f; f = d.openNextFile())
            file_last = max(file_last, atoi(f.name()));
    return file_last;
}

static void sweep_record(int n, double i, double sd, double v, unsigned beat, unsigned missed)
{
    if (step < 0 || mode_power != step) return;
    const int k = step_window++;
    Serial.printf("tangga: p%d jendela %d/%d%s\n", step, k + 1, POWER_BLOCK + 1,
                  k ? "" : " (transien, dibuang)");
    if (!k || windows_n >= SWEEP_N * POWER_BLOCK) return;
    window_t &j = windows[windows_n++];
    const uint64_t ep = ecg_mqtt_epoch_ms();
    if (ep) {
        const time_t t = ep / 1000;
        struct tm tm;
        gmtime_r(&t, &tm);
        strftime(j.time, sizeof j.time, "%Y-%m-%dT%H:%M:%SZ", &tm);
    } else {
        snprintf(j.time, sizeof j.time, "+%lus", (unsigned long)(millis() / 1000));
    }
    j.mode = step; j.n = n; j.i = i; j.sd = sd; j.v = v;
    j.beat = beat; j.missed = missed; j.replay = acquisition_replay();
}

static void begin_step(int m)
{
    step = m;
    step_window = 0;
    t_step = millis();
    Serial.printf("tangga: langkah %d/%d (p%d), buang 1 + ambil %d jendela %lu s\n", m + 1,
                  SWEEP_N, m, POWER_BLOCK, (unsigned long)(WINDOW_POWER_MS / 1000));
    power_set_mode(m);
}

void power_sweep_begin(void)
{
    if (recorder_reject("tangga daya")) return;
    if (step >= 0) { Serial.println("tangga: sudah berjalan"); return; }
    if (!ina_present) { Serial.println("tangga: INA219 tidak terdeteksi, batal"); return; }
    windows_n = results_n = 0;
    source_start = acquisition_source();
    recording_start = acquisition_source_recording();
    if (source_start != SOURCE_REFERENCE) acquisition_set_source(SOURCE_REFERENCE, 0, false);
    Serial.printf("tangga: mulai, perkiraan %lu s\n",
                  (unsigned long)(SWEEP_N * (POWER_BLOCK + 1) * WINDOW_POWER_MS / 1000));
    begin_step(0);
}

static void finish(const char *cancel)
{
    step = -1;
    power_set_mode(-1);
    if (acquisition_source() != source_start) acquisition_set_source(source_start, recording_start, false);
    if (cancel) Serial.printf("tangga: BATAL, %s\n", cancel);

    bool valid[SWEEP_N] = {};
    int failed = 0;
    results_n = 0;
    for (int m = 0; m < SWEEP_N; m++) {
        double si = 0, si2 = 0, sv = 0, vmin = 1e9;
        unsigned beat = 0, missed = 0;
        int k = 0;
        for (int r = 0; r < windows_n; r++) {
            if (windows[r].mode != m) continue;
            si += windows[r].i; si2 += (double)windows[r].i * windows[r].i; sv += windows[r].v;
            vmin = fmin(vmin, windows[r].v); beat += windows[r].beat; missed += windows[r].missed; k++;
        }
        if (!k) { valid[m] = false; break; }
        power_row_t &h = results[results_n++];
        h.i_ma = si / k;
        h.sd_ma = k > 1 ? sqrt(fmax((si2 - k * (double)h.i_ma * h.i_ma) / (k - 1), 0.0)) : 0;
        h.v = sv / k;
        h.p_mw = h.i_ma * h.v;
        valid[m] = !cancel;
        char reasons[4][72];
        int n_reasons = 0;
        if (vmin < 1.0)
            snprintf(reasons[n_reasons++], 72, "V bus %.3f V < 1 V, INA219 tidak di jalur catu", vmin);
        if (m >= 1 && missed) snprintf(reasons[n_reasons++], 72, "%u sampel hilang, beban tidak mewakili", missed);
        if (m >= 2 && !beat) snprintf(reasons[n_reasons++], 72, "tidak ada beat, replay tidak berjalan");
        if (m >= 1) {
            const power_row_t &l = results[m - 1];
            const double dI = h.i_ma - l.i_ma, sd = fmax(h.sd_ma, l.sd_ma);
            if (dI < 0) snprintf(reasons[n_reasons++], 72, "arus turun %+.2f mA dari p%d", dI, m - 1);
            else if (dI <= 2 * sd)
                snprintf(reasons[n_reasons++], 72, "selisih %+.2f mA dari p%d <= 2 x sd %.2f", dI, m - 1, sd);
        }
        for (int a = 0; a < n_reasons; a++) Serial.printf("tangga: TIDAK SAH p%d: %s\n", m, reasons[a]);
        if (n_reasons) { valid[m] = false; failed++; }
        snprintf(h.mode, sizeof h.mode, valid[m] ? "p%d" : "p%d!", m);
        Serial.printf("tangga: p%d I=%.2f sd=%.2f mA V=%.3f P=%.1f mW %s\n", m, h.i_ma, h.sd_ma,
                      h.v, h.p_mw, valid[m] ? "sah" : "TIDAK SAH");
    }
    if (!windows_n) return;

    const int number = power_sweep_file() + 1;
    char p[24];
    snprintf(p, sizeof p, "/daya/%03d.csv", number);
    File f = LittleFS.open(p, "w");
    if (!f) { Serial.printf("tangga: GAGAL membuka %s\n", p); return; }
    f.println("waktu,mode,n,I_mA,sd_mA,V,P_mW,beat,lewat,replay,sah");
    for (int r = 0; r < windows_n; r++) {
        const window_t &j = windows[r];
        f.printf("%s,%d,%u,%.2f,%.2f,%.3f,%.1f,%u,%u,%d,%d\n", j.time, j.mode, j.n, j.i,
                 j.sd, j.v, j.i * j.v, (unsigned)j.beat, (unsigned)j.missed, (int)j.replay,
                 (int)valid[j.mode]);
    }
    f.close();
    file_last = number;
    const bool all_valid = !cancel && !failed && results_n == SWEEP_N;
    Serial.printf("tangga: %s -> %s\n", all_valid ? "SAH" : "TIDAK SAH", p);
}

void power_sweep_tick(void)
{
    if (step < 0) return;
    if (mode_power != step) { finish("mode diubah dari luar tangga"); return; }
    if (step_window > POWER_BLOCK) {
        if (step < SWEEP_N - 1) begin_step(step + 1);
        else finish(nullptr);
    } else if (millis() - t_step > 2 * (POWER_BLOCK + 1) * WINDOW_POWER_MS + 5000) {
        finish("jendela tidak datang (INA219 tidak menjawab?)");
    }
}

static void list_files(void)
{
    File d = open_dir();
    Serial.println("daya: berkas tangga");
    if (d && d.isDirectory())
        for (File f = d.openNextFile(); f; f = d.openNextFile())
            Serial.printf("  %3d  %5u B\n", atoi(f.name()), (unsigned)f.size());
    Serial.println("daya: akhir daftar");
}

bool power_serial(const char *c)
{
    if (c[0] == 'V') { power_sweep_begin(); return true; }
    if (c[0] != 'v') return false;
    if (!c[1]) { list_files(); return true; }
    char p[24];
    snprintf(p, sizeof p, "/daya/%03d.csv", atoi(c + 1));
    File f = LittleFS.open(p, "r");
    if (!f) { Serial.printf("daya: %s tidak ada, lihat 'v'\n", p); return true; }
    Serial.println("---MULAI---");
    while (f.available()) Serial.write(f.read());
    Serial.println("---SELESAI---");
    f.close();
    return true;
}
#endif
