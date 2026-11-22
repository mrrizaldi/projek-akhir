#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "display.h"

#include <Arduino.h>
#include <time.h>

#include "acquisition.h"
#include "power.h"
#include "gate.h"
#include "ina219.h"
#include "board.h"
#include "recorder.h"
#include "buttons.h"

constexpr int GY = 30, GH = 112;
constexpr int DECIMATION = 3;
constexpr uint16_t GRAY = 0x4208;
constexpr uint32_t BEEP_MS = 50, BEEP_ARRHYTHMIA_MS = 250;
constexpr uint32_t HR_STALE_MS = 3000;
constexpr uint32_t PERIOD_LED_MS = 250;
constexpr int X_MIDDLE = 116, X_RIGHT = 220;

static bool mute, freeze;
static bool monitor = true;
static int hr_shown;
static bool hr_arrhythmia;
static uint32_t t_hr;
static uint32_t buzz_until;

bool display_mute(void) { return mute; }
void display_set_mute(bool on) { mute = on; }
bool display_freeze(void) { return freeze; }
void display_set_freeze(bool on) { freeze = on; }

void display_led(uint8_t r, uint8_t g, uint8_t b) { neopixelWrite(PIN_LED, r, g, b); }

void display_sound(uint32_t ms)
{
    buzzer(true);
    buzz_until = millis() + ms;
}

constexpr uint32_t BEEP_DELAY = ECG_LIVE_EVERY + ECG_WIN_POST + ECG_FS / 10;
constexpr int SCHEDULE_N = 8;
static struct { uint32_t sample; uint16_t ms; } schedule[SCHEDULE_N];
static int j_head, j_fill;

void display_clear_schedule(void) { j_fill = 0; }

static void schedule_beep(const ecg_beat_t &b, bool arrhythmia)
{
    if (mute || j_fill == SCHEDULE_N) return;
    auto &j = schedule[(j_head + j_fill++) % SCHEDULE_N];
    j.sample = (uint32_t)b.r_abs + BEEP_DELAY;
    j.ms = arrhythmia ? BEEP_ARRHYTHMIA_MS : BEEP_MS;
}

static void run_schedule()
{
    const uint32_t current = (uint32_t)ecg_live_total_sample();
    while (j_fill && (int32_t)(current - schedule[j_head].sample) >= 0) {
        const uint16_t ms = schedule[j_head].ms;
        j_head = (j_head + 1) % SCHEDULE_N;
        j_fill--;
        if (!freeze) display_sound(ms);
    }
}

static float plot_delay[BEEP_DELAY];
static size_t i_plot;

static float delayed(float f)
{
    const float previous = plot_delay[i_plot];
    plot_delay[i_plot] = f;
    i_plot = (i_plot + 1) % BEEP_DELAY;
    return previous;
}

static void plot(float f)
{
    static int n, x, y_previous = GY + GH / 2;
    static float lo = -300, hi = 300, mn = 1e9f, mx = -1e9f;

    mn = fminf(mn, f);
    mx = fmaxf(mx, f);
    if (++n < DECIMATION || freeze) return;
    n = 0;

    int y = GY + GH - 1 - (int)((f - lo) * (GH - 1) / (hi - lo));
    y = constrain(y, GY, GY + GH - 1);
    if (monitor) {
        tft.fillRect(x, GY, min(4, TFT_W - x), GH, ST77XX_BLACK);
        tft.drawFastVLine(x, min(y, y_previous), abs(y - y_previous) + 1, ST77XX_GREEN);
    }
    y_previous = y;

    if (++x < TFT_W) return;
    x = 0;
    const float span = fmaxf(mx - mn, 50.0f);
    lo = mn - 0.1f * span;
    hi = lo + 1.2f * span;
    mn = 1e9f;
    mx = -1e9f;
}

void display_sample(void)
{
    run_schedule();
    plot(delayed(ecg_live_filtered_last()));
}

void display_beat(const ecg_beat_t &beat, bool arrhythmia)
{
    if (gate_quality().swing_clean < THRESHOLD_SWING) return;
    hr_shown = (beat.rr[0] > 0.05f) ? (int)lroundf(60.0f / beat.rr[0]) : 0;
    hr_arrhythmia = arrhythmia;
    t_hr = millis();
    if (gate_phase() != PHASE_CALIBRATION) schedule_beep(beat, arrhythmia);
}

void display_draw_button(int i)
{
    if (!monitor) return;
    static const char *const label[2][2] = {{"B1 BUNYI", "B1 BISU"}, {"B2 JALAN", "B2 BEKU"}};
    const bool down = buttons_pressed(i);
    const int x = i * 107;
    const uint16_t bg = down ? ST77XX_YELLOW : GRAY;
    tft.fillRect(x, 148, 105, 24, bg);
    tft.setTextColor(down ? ST77XX_BLACK : ST77XX_WHITE, bg);
    tft.setTextSize(2);
    if (i < 2) {
        tft.setCursor(x + 6, 153);
        tft.print(label[i][i == 0 ? mute : freeze]);
    } else if (!recorder_active()) {
        tft.setCursor(x + 6, 153);
        tft.print("B3 REC");
    } else {
        tft.setCursor(x, 149);
        tft.print(recorder_paused() ? "B3 LANJUT" : "B3 JEDA");
        tft.setTextSize(1);
        tft.setCursor(x + 6, 165);
        tft.print("tahan=SIMPAN");
    }
}

void display_begin(void)
{
    tft.drawFastHLine(0, GY - 2, TFT_W, GRAY);
    for (int i = 0; i < 3; i++) display_draw_button(i);
}

static void update_led()
{
    static uint32_t t_led = 0;

    if (millis() - t_led < PERIOD_LED_MS) return;
    t_led = millis();

    if (!power_stage(4))                    display_led(0, 0, 0);
    else if (gate_phase() == PHASE_CALIBRATION) display_led(0, 16, 64);
    else if (gate_phase() == PHASE_BAD) display_led(64, 24, 0);
    else                                   display_led(0, 48, 0);
}

static uint32_t t_1hz;
static char right_previous[32];
constexpr uint32_t MESSAGE_MS = 2000, BEEP_REJECT_MS = 150;
static char message_large[9], message_small[17];
static uint32_t t_message;

void display_message(const char *large, const char *small)
{
    snprintf(message_large, sizeof message_large, "%s", large);
    snprintf(message_small, sizeof message_small, "%s", small);
    t_message = millis() | 1;
    t_1hz = millis() - 1000;
    display_sound(BEEP_REJECT_MS);
}

static void draw_middle()
{
    static const char *const MONTHS[12] = {"Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                                          "Jul", "Agu", "Sep", "Okt", "Nov", "Des"};
    static bool clock_logged;
    char large[16], small[24];
    uint16_t w = ST77XX_WHITE;

    const time_t current = time(nullptr);
    struct tm t;
    localtime_r(&current, &t);
    const bool synced = t.tm_year + 1900 > 2020;
    if (synced && !clock_logged) {
        clock_logged = true;
        Serial.printf("clock: %02d:%02d:%02d WIB %d %s %d\n", t.tm_hour, t.tm_min, t.tm_sec,
                      t.tm_mday, MONTHS[t.tm_mon], t.tm_year + 1900);
    }

    if ((millis() / 3000) % 2 == 0) {
        float mA = 0, V = 0;
        const bool ok = power_ina_present() && ina219_read(R_SHUNT, &mA, &V);
        w = ok ? ST77XX_CYAN : ST77XX_RED;
        if (ok) {
            snprintf(large, sizeof large, "%4.0fmA", mA);
            snprintf(small, sizeof small, "%4.2fV %5.0fmW", V, mA * V);
        } else {
            snprintf(large, sizeof large, "INA --");
            snprintf(small, sizeof small, "cek SDA%d SCL%d", I2C_SDA, I2C_SCL);
        }
    } else if (synced) {
        snprintf(large, sizeof large, "%02d:%02d:%02d", t.tm_hour, t.tm_min, t.tm_sec);
        snprintf(small, sizeof small, "%d %s %d", t.tm_mday, MONTHS[t.tm_mon], t.tm_year + 1900);
    } else {
        const uint32_t d = millis() / 1000;
        snprintf(large, sizeof large, "%02u:%02u:%02u", (unsigned)(d / 3600 % 100),
                 (unsigned)(d / 60 % 60), (unsigned)(d % 60));
        snprintf(small, sizeof small, "up (belum NTP)");
    }
    tft.setTextColor(w, ST77XX_BLACK);
    tft.setTextSize(2);
    tft.setCursor(X_MIDDLE, 2);
    tft.printf("%-8.8s", large);
    tft.setTextSize(1);
    tft.setCursor(X_MIDDLE, 20);
    tft.printf("%-16.16s", small);
}

static void draw_right()
{
    char t[16] = "", small[24] = "";
    uint16_t w = ST77XX_YELLOW;
    const unsigned d = (unsigned)(recorder_n_session() / ECG_FS);
    const int saved = recorder_newly_saved();
    if (t_message && millis() - t_message < MESSAGE_MS) {
        w = ST77XX_ORANGE;
        snprintf(t, sizeof t, "%s", message_large);
        snprintf(small, sizeof small, "%s", message_small);
    } else if (recorder_active() && !recorder_paused() && acquisition_missed()) {
        w = ST77XX_RED;
        snprintf(t, sizeof t, "HILANG");
        snprintf(small, sizeof small, "%u sampel", (unsigned)acquisition_missed());
    } else if (recorder_active() && !recorder_paused()) {
        w = ST77XX_RED;
        snprintf(t, sizeof t, "REC%02u:%02u", d / 60 % 100, d % 60);
        if (recorder_part() > 1) snprintf(small, sizeof small, "bagian %d", recorder_part());
    } else if (recorder_active()) {
        snprintf(t, sizeof t, "JEDA%u:%02u", d / 60 % 10, d % 60);
    } else if (recorder_writing()) {
        snprintf(t, sizeof t, "SIMPAN..");
    } else if (saved) {
        w = ST77XX_GREEN;
        snprintf(t, sizeof t, "SIMPAN");
        snprintf(small, sizeof small, RECORDER_PATTERN, saved);
    } else if (acquisition_source() == SOURCE_RECORDING) {
        snprintf(t, sizeof t, "RP#%03d", acquisition_source_recording());
    } else if (acquisition_source() == SOURCE_REFERENCE) {
        snprintf(t, sizeof t, "RP 208");
    }

    char key[sizeof right_previous];
    snprintf(key, sizeof key, "%s|%s|%u", t, small, (unsigned)w);
    if (strcmp(key, right_previous) == 0) return;
    strcpy(right_previous, key);
    tft.fillRect(X_RIGHT, 0, TFT_W - X_RIGHT, GY - 3, ST77XX_BLACK);
    tft.setTextColor(w, ST77XX_BLACK);
    tft.setTextSize(2);
    tft.setCursor(X_RIGHT, small[0] ? 2 : 8);
    tft.print(t);
    if (small[0]) {
        tft.setTextSize(1);
        tft.setCursor(X_RIGHT, 20);
        tft.print(small);
    }
}

static void screen_1hz()
{
    uint32_t &t = t_1hz;
    if (!monitor || millis() - t < 1000) return;
    t = millis();

    const bool hr_present = hr_shown > 0 && millis() - t_hr < HR_STALE_MS;
    tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
    tft.setTextSize(2);
    tft.setCursor(4, 8);
    tft.print("HR");
    tft.setTextSize(3);
    tft.setCursor(32, 3);
    tft.setTextColor(hr_present && hr_arrhythmia ? ST77XX_RED : ST77XX_WHITE, ST77XX_BLACK);
    if (hr_present) tft.printf("%3d", hr_shown);
    else        tft.print(" --");
    tft.setTextSize(1);
    tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
    tft.setCursor(90, 17);
    tft.print("bpm");

    draw_middle();
    draw_right();

    for (int i = 0; i < 3; i++) display_draw_button(i);
}

void display_set_monitor(bool on)
{
    monitor = on;
    if (!on) return;
    tft.fillScreen(ST77XX_BLACK);
    display_begin();
    t_1hz = millis() - 1000;
    right_previous[0] = 0;
}


constexpr int MY = 26, MH = 20;
constexpr uint16_t DARK_BLUE = 0x0010;
static char row_text[DISPLAY_ROWS][DISPLAY_COLUMNS + 1];
static int8_t row_highlight[DISPLAY_ROWS];

void display_menu_frame(const char *title, const char *hint1, const char *hint2)
{
    tft.fillScreen(ST77XX_BLACK);
    tft.fillRect(0, 0, TFT_W, 22, DARK_BLUE);
    tft.setTextSize(2);
    tft.setTextColor(ST77XX_WHITE, DARK_BLUE);
    tft.setCursor(4, 3);
    tft.print(title);
    tft.drawFastHLine(0, 148, TFT_W, GRAY);
    tft.setTextSize(1);
    tft.setTextColor(ST77XX_CYAN, ST77XX_BLACK);
    tft.setCursor(4, 152);
    tft.print(hint1);
    tft.setCursor(4, 162);
    tft.print(hint2);
    for (int r = 0; r < DISPLAY_ROWS; r++) { row_text[r][0] = 0; row_highlight[r] = 0; }
}

void display_menu_row(int r, const char *text, bool highlight, uint16_t color)
{
    if (r < 0 || r >= DISPLAY_ROWS) return;
    char t[DISPLAY_COLUMNS + 1];
    snprintf(t, sizeof t, "%-*.*s", DISPLAY_COLUMNS, DISPLAY_COLUMNS, text);
    if (row_highlight[r] == highlight && strcmp(row_text[r], t) == 0) return;
    strcpy(row_text[r], t);
    row_highlight[r] = highlight;
    const uint16_t bg = highlight ? ST77XX_YELLOW : ST77XX_BLACK;
    const int y = MY + r * MH;
    tft.fillRect(0, y, 4, 16, bg);
    tft.fillRect(4 + DISPLAY_COLUMNS * 12, y, TFT_W - 4 - DISPLAY_COLUMNS * 12, 16, bg);
    tft.setTextSize(2);
    tft.setTextColor(highlight ? ST77XX_BLACK : color, bg);
    tft.setCursor(4, y + 1);
    tft.print(t);
}

void display_service(void)
{
    update_led();
    screen_1hz();
    if (buzz_until && (int32_t)(millis() - buzz_until) >= 0) {
        buzzer(false);
        buzz_until = 0;
    }
}
#endif
