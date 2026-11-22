#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "app_settings.h"

#include <Arduino.h>
#include <Preferences.h>
#include "esp_wifi.h"

#include "ecg_mqtt.h"
#include "recorder.h"

struct wifi_t { const char *ssid, *pass; };
struct broker_t { const char *name, *host; uint16_t port; const char *token; };

#if __has_include("wifi_secrets.h")
#include "wifi_secrets.h"
#endif
#if !defined(WIFI_DAFTAR) && defined(WIFI_SSID)
#define WIFI_DAFTAR {{WIFI_SSID, WIFI_PASS}}
#endif
#if !defined(BROKER_DAFTAR) && defined(TB_HOST)
#define BROKER_DAFTAR {{"utama", TB_HOST, TB_PORT, TB_TOKEN}}
#endif
#ifndef WIFI_DAFTAR
#define WIFI_DAFTAR {{"", ""}}
#endif
#ifndef BROKER_DAFTAR
#define BROKER_DAFTAR {{"-", "", 1883, ""}}
#endif

static const wifi_t WIFI[] = WIFI_DAFTAR;
static const broker_t BROKER[] = BROKER_DAFTAR;
constexpr int N_WIFI = sizeof WIFI / sizeof WIFI[0];
constexpr int N_BROKER = sizeof BROKER / sizeof BROKER[0];

constexpr const char *NS = "konfig";
constexpr bool NOT_READ_ONLY = false;
static int i_wifi, i_broker, source, source_recording;
static bool wifi_active = true;

static int read_stored(const char *key, int n)
{
    Preferences p;
    p.begin(NS, NOT_READ_ONLY);
    const int v = p.getUChar(key, 0);
    p.end();
    return v < n ? v : 0;
}

static void write_stored(const char *key, int v)
{
    Preferences p;
    p.begin(NS, NOT_READ_ONLY);
    p.putUChar(key, (uint8_t)v);
    p.end();
}

static void apply_selection()
{
    const wifi_t &w = WIFI[i_wifi];
    const broker_t &b = BROKER[i_broker];
    ecg_mqtt_configure(w.ssid, w.pass, b.host, b.port, b.token);
    Serial.printf("config: wifi %d/%d \"%s\" %s | broker %d/%d %s (%s:%u)\n",
                  i_wifi, N_WIFI, w.ssid, wifi_active ? "ON" : "OFF", i_broker, N_BROKER, b.name,
                  b.host, (unsigned)b.port);
}

void settings_begin(void)
{
    i_wifi = read_stored("wifi", N_WIFI);
    i_broker = read_stored("broker", N_BROKER);
    source = read_stored("sumber", 3);
    wifi_active = !read_stored("wifimati", 2);
    Preferences p;
    p.begin(NS, NOT_READ_ONLY);
    source_recording = p.getUShort("rekam", 0);
    p.end();
    apply_selection();
    if (wifi_active) ecg_mqtt_begin();
    else ecg_mqtt_set_active(0);
}

int settings_wifi_n(void) { return N_WIFI; }
const char *settings_wifi_name(int i) { return i >= 0 && i < N_WIFI ? WIFI[i].ssid : ""; }
int settings_wifi(void) { return i_wifi; }

int settings_broker_n(void) { return N_BROKER; }
const char *settings_broker_name(int i) { return i >= 0 && i < N_BROKER ? BROKER[i].name : ""; }
const char *settings_broker_host(int i) { return i >= 0 && i < N_BROKER ? BROKER[i].host : ""; }
int settings_broker_port(int i) { return i >= 0 && i < N_BROKER ? BROKER[i].port : 0; }
int settings_broker(void) { return i_broker; }

bool settings_choose_wifi(int i)
{
    if (i < 0 || i >= N_WIFI || recorder_reject("change WiFi")) return false;
    i_wifi = i;
    write_stored("wifi", i);
    apply_selection();
    if (wifi_active) ecg_mqtt_begin();
    return true;
}

bool settings_wifi_active(void) { return wifi_active; }

bool settings_set_wifi_active(bool on)
{
    if (recorder_reject("WiFi")) return false;
    wifi_active = on;
    write_stored("wifimati", !on);
    if (on) {
        esp_wifi_start();
        ecg_mqtt_begin();
        ecg_mqtt_set_active(1);
    } else {
        ecg_mqtt_set_active(0);
        esp_wifi_stop();
    }
    Serial.printf("wifi %s (saved)\n", on ? "ON" : "OFF");
    return true;
}

bool settings_choose_broker(int i)
{
    if (i < 0 || i >= N_BROKER || recorder_reject("change broker")) return false;
    i_broker = i;
    write_stored("broker", i);
    apply_selection();
    return true;
}

int settings_source(void) { return source; }
int settings_source_recording(void) { return source_recording; }

void settings_set_source(int s, int number)
{
    if (s != source) write_stored("sumber", s);
    if (number != source_recording) {
        Preferences p;
        p.begin(NS, NOT_READ_ONLY);
        p.putUShort("rekam", (uint16_t)number);
        p.end();
    }
    source = s;
    source_recording = number;
}
#endif
