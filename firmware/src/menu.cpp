#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "menu.h"

#include <Arduino.h>
#include <WiFi.h>

#include "acquisition.h"
#include "ecg_mqtt.h"
#include "gate.h"
#include "ina219.h"
#include "classifier.h"
#include "app_settings.h"
#include "board.h"
#include "recorder.h"
#include "diagnostics.h"
#include "power.h"
#include "display.h"
#include "buttons.h"

#ifndef GIT_VERSION
#define GIT_VERSION "?"
#endif

typedef char row_t[DISPLAY_COLUMNS + 1];

struct page_t;
struct item_t {
    const char *text;
    const page_t *child;
    void (*action)(void);
    const char *(*value)(void);
};
struct page_t {
    const char *title;
    const item_t *item;
    int n;
    int (*n_dyn)(void);
    void (*text_dyn)(int i, char *out, size_t n);
    void (*choose_dyn)(int i);
    void (*fill)(row_t *b);
};
#define LIST(j, a) {j, a, (int)(sizeof a / sizeof a[0]), nullptr, nullptr, nullptr, nullptr}
#define DYNAMIC(j, n, t, p) {j, nullptr, 0, n, t, p, nullptr}
#define TEXT(j, f) {j, nullptr, 0, nullptr, nullptr, nullptr, f}

static const char *mark(bool active) { return active ? "*" : ""; }
static void to_adc() { acquisition_set_source(SOURCE_ADC, 0, true); }
static void to_reference() { acquisition_set_source(SOURCE_REFERENCE, 0, true); }
static const char *n_adc() { return mark(acquisition_source() == SOURCE_ADC); }
static const char *n_reference() { return mark(acquisition_source() == SOURCE_REFERENCE); }

static int rec_no[64], rec_n;
static int recordings_n() { return rec_n = recorder_list(rec_no, 64); }
static void recordings_text(int i, char *out, size_t n)
{
    const bool active = acquisition_source() == SOURCE_RECORDING && acquisition_source_recording() == rec_no[i];
    snprintf(out, n, "%03d  %6.1f s  %s", rec_no[i], (float)recorder_sample_n(rec_no[i]) / ECG_FS,
             active ? "*" : "");
}
static void recordings_choose(int i) { acquisition_set_source(SOURCE_RECORDING, rec_no[i], true); }
static const page_t H_RECORDINGS = DYNAMIC("Replay rekaman", recordings_n, recordings_text, recordings_choose);
static const char *n_recordings()
{
    static char t[8];
    if (acquisition_source() != SOURCE_RECORDING) return ">";
    snprintf(t, sizeof t, "%03d * >", acquisition_source_recording());
    return t;
}

static const item_t I_SOURCE[] = {
    {"Sensor (ADC)", nullptr, to_adc, n_adc},
    {"REPLAY 208", nullptr, to_reference, n_reference},
    {"Replay rekaman", &H_RECORDINGS, nullptr, n_recordings},
};
static const page_t H_SOURCE = LIST("Sumber sinyal", I_SOURCE);

static const char *on_off(bool on) { return on ? "ON" : "OFF"; }
static void calibration_restart()
{
    gate_begin_session();
    classifier_reset();
    Serial.println("calibration: new session");
}
static void calibration_skip()
{
    gate_set_skip(!gate_skip());
    Serial.printf("skip calibration gate %s\n", on_off(gate_skip()));
}
static const char *n_skip() { return on_off(gate_skip()); }
static void calibration_status(row_t *b)
{
    const gate_quality_t &q = gate_quality();
    const int f = gate_phase();
    snprintf(b[0], sizeof *b, "Fase %s", f == PHASE_CALIBRATION ? "KALIBRASI" : f == PHASE_GOOD ? "BAIK" : "BURUK");
    snprintf(b[1], sizeof *b, "Kontak %lu/%lu s",
             (unsigned long)min<uint32_t>(gate_contact_ms() / 1000, 99999),
             (unsigned long)(WARMUP_MS / 1000));
    snprintf(b[2], sizeof *b, "RR tenang %lu/%lu s",
             (unsigned long)min<uint32_t>(gate_quiet_ms() / 1000, 99999),
             (unsigned long)(RR_QUIET_MS / 1000));
    snprintf(b[3], sizeof *b, "Ayun %d/%d 50Hz %d/%d", q.swing_clean, THRESHOLD_SWING, q.hum50, THRESHOLD_HUM);
    snprintf(b[4], sizeof *b, "Lewati %s  Replay %s", on_off(gate_skip()), on_off(acquisition_replay()));
    snprintf(b[5], sizeof *b, "Sampel hilang %u", (unsigned)acquisition_missed());
}
static const page_t H_CALIBRATION_STATUS = TEXT("Status kalibrasi", calibration_status);
static const item_t I_CALIBRATION[] = {
    {"Mulai ulang", nullptr, calibration_restart, nullptr},
    {"Lewati (bench)", nullptr, calibration_skip, n_skip},
    {"Status", &H_CALIBRATION_STATUS, nullptr, nullptr},
};
static const page_t H_CALIBRATION = LIST("Kalibrasi", I_CALIBRATION);

static const char *test_name;
static diag_result_t test_result;
static void test_run(const char *name, diag_result_t (*f)(void))
{
    test_name = name;
    acquisition_timer(false);
    test_result = f();
    acquisition_timer(power_mode() != 0);
    int i;
    while (buttons_event(&i) != BUTTON_NONE) {}
    Serial.printf("test %s: %s | %s\n", name, test_result.pass ? "PASS" : "FAIL", test_result.summary);
}
static diag_result_t button_10s()
{
    display_menu_frame("Tes tombol", "B2 yang masih ditahan: lepas dulu", "");
    display_menu_row(1, "Tekan B1, B2, B3", false);
    display_menu_row(2, "batas 10 detik", false);
    return diag_button(10000);
}
static void test_buzzer() { test_run("Buzzer", diag_buzzer); }
static void test_screen() { test_run("Layar", diag_screen); }
static void test_adc() { test_run("ADC & lead-off", diag_adc); }
static void test_ina() { test_run("INA219", diag_ina219); }
static void test_button() { test_run("Tombol", button_10s); }
static void test_fill(row_t *b)
{
    snprintf(b[0], sizeof *b, "%s", test_name ? test_name : "-");
    snprintf(b[1], sizeof *b, "%s", test_result.pass ? "LULUS" : "GAGAL");
    const char *r = test_result.summary;
    for (int k = 2; k < DISPLAY_ROWS && *r; k++, r += min<size_t>(strlen(r), DISPLAY_COLUMNS))
        snprintf(b[k], sizeof *b, "%.*s", DISPLAY_COLUMNS, r);
}
static const page_t H_TEST_RESULT = TEXT("Hasil tes", test_fill);
static const item_t I_TEST[] = {
    {"Buzzer", &H_TEST_RESULT, test_buzzer, nullptr},
    {"Layar (pola warna)", &H_TEST_RESULT, test_screen, nullptr},
    {"ADC & lead-off", &H_TEST_RESULT, test_adc, nullptr},
    {"INA219", &H_TEST_RESULT, test_ina, nullptr},
    {"Tombol (10 s)", &H_TEST_RESULT, test_button, nullptr},
};
static const page_t H_TEST = LIST("Tes perangkat", I_TEST);

static void power_fill(row_t *b)
{
    if (power_sweep_active()) {
        snprintf(b[0], sizeof *b, "Mengukur, jangan disentuh");
        snprintf(b[1], sizeof *b, "Langkah p%d (%d/6)", power_sweep_step(), power_sweep_step() + 1);
        return;
    }
    power_row_t h[DISPLAY_ROWS];
    const int n = power_sweep_result(h, DISPLAY_ROWS);
    if (!n) { snprintf(b[0], sizeof *b, "Belum ada hasil"); return; }
    for (int k = 0; k < n; k++)
        snprintf(b[k], sizeof *b, "%-3s%6.1fmA %5.0fmW", h[k].mode, h[k].i_ma, h[k].p_mw);
    char *e = b[0] + strlen(b[0]);
    snprintf(e, sizeof *b - (e - b[0]), " #%03d", power_sweep_file());
}
static const page_t H_POWER = TEXT("Ukur daya", power_fill);
static void close_menu();
static void begin_sweep()
{
    power_sweep_begin();
    if (power_sweep_active()) close_menu();
}
static const item_t I_POWER[] = {
    {"Mulai tangga p0-p5", nullptr, begin_sweep, nullptr},
    {"Hasil terakhir", &H_POWER, nullptr, nullptr},
};
static const page_t H_POWER_MENU = LIST("Ukur daya", I_POWER);

static int wifi_n() { return settings_wifi_n(); }
static void wifi_text(int i, char *out, size_t n)
{
    snprintf(out, n, "%c %s", i == settings_wifi() ? '*' : ' ', settings_wifi_name(i));
}
static void wifi_choose(int i) { settings_choose_wifi(i); }
static int broker_n() { return settings_broker_n(); }
static void broker_text(int i, char *out, size_t n)
{
    snprintf(out, n, "%c %s %s", i == settings_broker() ? '*' : ' ', settings_broker_name(i),
             settings_broker_host(i));
}
static void broker_choose(int i) { settings_choose_broker(i); }
static const page_t H_WIFI = DYNAMIC("WiFi", wifi_n, wifi_text, wifi_choose);
static const page_t H_BROKER = DYNAMIC("Broker", broker_n, broker_text, broker_choose);

static void wifi_switch() { settings_set_wifi_active(!settings_wifi_active()); }
static const char *n_wifi_active() { return on_off(settings_wifi_active()); }
static const char *n_wifi() { return settings_wifi_name(settings_wifi()); }
static const char *n_broker() { return settings_broker_name(settings_broker()); }
static const char *ip_text()
{
    static char t[16];
    if (WiFi.status() != WL_CONNECTED) return "-";
    snprintf(t, sizeof t, "%s", WiFi.localIP().toString().c_str());
    return t;
}
static void net_status(row_t *b)
{
    const int k = settings_broker();
    snprintf(b[0], sizeof *b, "MQTT %s (%s)", on_off(ecg_mqtt_active()), ecg_mqtt_status());
    snprintf(b[1], sizeof *b, "WiFi %s", settings_wifi_name(settings_wifi()));
    snprintf(b[2], sizeof *b, "IP %s", ip_text());
    snprintf(b[3], sizeof *b, "RSSI %d dBm", ecg_mqtt_rssi());
    snprintf(b[4], sizeof *b, "%s:%d", settings_broker_host(k), settings_broker_port(k));
    snprintf(b[5], sizeof *b, "Kirim %u backlog %u", (unsigned)ecg_mqtt_sent(),
             (unsigned)ecg_mqtt_queue_n());
}
static const page_t H_NET_STATUS = TEXT("Status jaringan", net_status);
static const item_t I_NETWORK[] = {
    {"WiFi aktif", nullptr, wifi_switch, n_wifi_active},
    {"WiFi", &H_WIFI, nullptr, n_wifi},
    {"Broker", &H_BROKER, nullptr, n_broker},
    {"Status", &H_NET_STATUS, nullptr, nullptr},
};
static const page_t H_NETWORK = LIST("Jaringan", I_NETWORK);

static void info_fill(row_t *b)
{
    const int k = settings_broker();
    snprintf(b[0], sizeof *b, "IP %s  %d dBm", ip_text(), ecg_mqtt_rssi());
    snprintf(b[1], sizeof *b, "Broker %s %s", settings_broker_name(k), settings_broker_host(k));
    float mA, V;
    if (power_ina_present() && ina219_read(R_SHUNT, &mA, &V))
        snprintf(b[2], sizeof *b, "INA %.2f V %.1f mA", V, mA);
    else
        snprintf(b[2], sizeof *b, "INA219 tidak menjawab");
    const uint32_t d = millis() / 1000;
    snprintf(b[3], sizeof *b, "Uptime %lu:%02lu:%02lu", (unsigned long)(d / 3600),
             (unsigned long)(d / 60 % 60), (unsigned long)(d % 60));
    snprintf(b[4], sizeof *b, "Versi %s", GIT_VERSION);
    snprintf(b[5], sizeof *b, "Build %s %.5s", __DATE__, __TIME__);
}
static const page_t H_INFO = TEXT("Info", info_fill);

static const item_t I_ROOT[] = {
    {"Sumber sinyal", &H_SOURCE, nullptr, nullptr},
    {"Kalibrasi", &H_CALIBRATION, nullptr, nullptr},
    {"Tes perangkat", &H_TEST, nullptr, nullptr},
    {"Ukur daya", &H_POWER_MENU, nullptr, nullptr},
    {"Jaringan", &H_NETWORK, nullptr, nullptr},
    {"Info", &H_INFO, nullptr, nullptr},
};
static const page_t H_ROOT = LIST("MENU", I_ROOT);

constexpr int DEPTH_MAX = 4;
static struct { const page_t *h; int sel, top; } stack[DEPTH_MAX];
static int depth = -1;
static uint32_t t_fill;

bool menu_is_open(void) { return depth >= 0; }

static int count(const page_t *h) { return h->item ? h->n : h->n_dyn ? h->n_dyn() : 0; }

static void label(const page_t *h, int i, char *out, size_t n)
{
    if (!h->item) { h->text_dyn(i, out, n); return; }
    const item_t &it = h->item[i];
    const char *v = it.value ? it.value() : it.child ? ">" : "";
    const int pad = DISPLAY_COLUMNS - (int)strlen(it.text);
    snprintf(out, n, "%s%*s", it.text, pad > 0 ? pad : 1, v);
}

static void draw(bool frame)
{
    auto &t = stack[depth];
    if (frame)
        display_menu_frame(t.h->title,
                              t.h->fill ? "B2 kembali" : "B3 naik   B1 turun   tahan B2 pilih",
                              t.h->fill ? "tahan B1/B3 keluar ke monitor"
                                       : "B2 kembali   tahan B1/B3 keluar ke monitor");
    if (t.h->fill) {
        row_t b[DISPLAY_ROWS] = {};
        t.h->fill(b);
        for (int r = 0; r < DISPLAY_ROWS; r++) display_menu_row(r, b[r], false);
        return;
    }
    const int n = count(t.h);
    if (t.sel >= n) t.sel = n ? n - 1 : 0;
    if (t.sel < t.top) t.top = t.sel;
    if (t.sel >= t.top + DISPLAY_ROWS) t.top = t.sel - DISPLAY_ROWS + 1;
    for (int r = 0; r < DISPLAY_ROWS; r++) {
        const int i = t.top + r;
        row_t s = "";
        if (i < n) label(t.h, i, s, sizeof s);
        else if (n == 0 && r == 0) strcpy(s, "(kosong)");
        display_menu_row(r, s, i < n && i == t.sel);
    }
}

static void report()
{
    auto &t = stack[depth];
    if (t.h->fill) {
        row_t b[DISPLAY_ROWS] = {};
        t.h->fill(b);
        Serial.printf("menu: %s\n", t.h->title);
        for (auto &s : b) if (s[0]) Serial.printf("menu:   %s\n", s);
        return;
    }
    const int n = count(t.h);
    row_t s = "(empty)";
    if (n) label(t.h, t.sel, s, sizeof s);
    Serial.printf("menu: %s [%d/%d] %s\n", t.h->title, n ? t.sel + 1 : 0, n, s);
}

static void enter(const page_t *h)
{
    if (depth + 1 >= DEPTH_MAX) return;
    stack[++depth] = {h, 0, 0};
    t_fill = millis();
    draw(true);
    report();
}

void menu_open(void)
{
    if (depth >= 0) return;
    if (recorder_reject("menu")) { display_message("TERKUNCI", "tahan B3=simpan"); return; }
    display_set_monitor(false);
    enter(&H_ROOT);
}

static void close_menu()
{
    depth = -1;
    display_set_monitor(true);
    Serial.println("menu: close");
}

static void back()
{
    if (depth == 0) { close_menu(); return; }
    depth--;
    draw(true);
    report();
}

static void choose()
{
    auto &t = stack[depth];
    if (t.h->fill || !count(t.h)) return;
    if (!t.h->item) {
        t.h->choose_dyn(t.sel);
        back();
        return;
    }
    const item_t &it = t.h->item[t.sel];
    if (it.action) it.action();
    if (depth < 0) return;
    if (it.child) { enter(it.child); return; }
    draw(false);
    report();
}

void menu_button(int i, int e)
{
    if (depth < 0) return;
    if (e == BUTTON_LONG) {
        if (i == 1) choose();
        else close_menu();
    } else if (e == BUTTON_SHORT) {
        auto &t = stack[depth];
        const int n = t.h->fill ? 0 : count(t.h);
        if (i == 1) back();
        else if (n) {
            t.sel = (t.sel + (i == 2 ? n - 1 : 1)) % n;
            draw(false);
            report();
        }
    }
}

void menu_service(void)
{
    static bool power_previous;
    const bool d = power_sweep_active();
    if (power_previous && !d && (depth < 0 || stack[depth].h != &H_POWER)) {
        if (depth < 0) display_set_monitor(false);
        enter(&H_POWER);
    }
    power_previous = d;
    if (depth < 0 || !stack[depth].h->fill || millis() - t_fill < 1000) return;
    t_fill = millis();
    draw(false);
}
#endif
