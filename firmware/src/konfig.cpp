#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "konfig.h"

#include <Arduino.h>
#include <Preferences.h>
#include "esp_wifi.h"

#include "ecg_mqtt.h"
#include "rekam.h"

struct wifi_t { const char *ssid, *pass; };
struct broker_t { const char *nama, *host; uint16_t port; const char *token; };

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
constexpr bool BUKAN_READ_ONLY = false;
static int i_wifi, i_broker, sumber, sumber_rekam;
static bool wifi_aktif = true;

static int baca(const char *kunci, int n)
{
    Preferences p;
    p.begin(NS, BUKAN_READ_ONLY);
    const int v = p.getUChar(kunci, 0);
    p.end();
    return v < n ? v : 0;
}

static void tulis(const char *kunci, int v)
{
    Preferences p;
    p.begin(NS, BUKAN_READ_ONLY);
    p.putUChar(kunci, (uint8_t)v);
    p.end();
}

static void terapkan()
{
    const wifi_t &w = WIFI[i_wifi];
    const broker_t &b = BROKER[i_broker];
    ecg_mqtt_atur(w.ssid, w.pass, b.host, b.port, b.token);
    Serial.printf("konfig: wifi %d/%d \"%s\" %s | broker %d/%d %s (%s:%u)\n",
                  i_wifi, N_WIFI, w.ssid, wifi_aktif ? "ON" : "OFF", i_broker, N_BROKER, b.nama,
                  b.host, (unsigned)b.port);
}

void konfig_mulai(void)
{
    i_wifi = baca("wifi", N_WIFI);
    i_broker = baca("broker", N_BROKER);
    sumber = baca("sumber", 3);
    wifi_aktif = !baca("wifimati", 2);
    Preferences p;
    p.begin(NS, BUKAN_READ_ONLY);
    sumber_rekam = p.getUShort("rekam", 0);
    p.end();
    terapkan();
    if (wifi_aktif) ecg_mqtt_mulai();
    else ecg_mqtt_set_aktif(0);
}

int konfig_wifi_n(void) { return N_WIFI; }
const char *konfig_wifi_nama(int i) { return i >= 0 && i < N_WIFI ? WIFI[i].ssid : ""; }
int konfig_wifi(void) { return i_wifi; }

int konfig_broker_n(void) { return N_BROKER; }
const char *konfig_broker_nama(int i) { return i >= 0 && i < N_BROKER ? BROKER[i].nama : ""; }
const char *konfig_broker_host(int i) { return i >= 0 && i < N_BROKER ? BROKER[i].host : ""; }
int konfig_broker_port(int i) { return i >= 0 && i < N_BROKER ? BROKER[i].port : 0; }
int konfig_broker(void) { return i_broker; }

bool konfig_pilih_wifi(int i)
{
    if (i < 0 || i >= N_WIFI || rekam_tolak("ganti WiFi")) return false;
    i_wifi = i;
    tulis("wifi", i);
    terapkan();
    if (wifi_aktif) ecg_mqtt_mulai();
    return true;
}

bool konfig_wifi_aktif(void) { return wifi_aktif; }

bool konfig_set_wifi_aktif(bool on)
{
    if (rekam_tolak("WiFi")) return false;
    wifi_aktif = on;
    tulis("wifimati", !on);
    if (on) {
        esp_wifi_start();
        ecg_mqtt_mulai();
        ecg_mqtt_set_aktif(1);
    } else {
        ecg_mqtt_set_aktif(0);
        esp_wifi_stop();
    }
    Serial.printf("wifi %s (tersimpan)\n", on ? "ON" : "OFF");
    return true;
}

bool konfig_pilih_broker(int i)
{
    if (i < 0 || i >= N_BROKER || rekam_tolak("ganti broker")) return false;
    i_broker = i;
    tulis("broker", i);
    terapkan();
    return true;
}

int konfig_sumber(void) { return sumber; }
int konfig_sumber_rekam(void) { return sumber_rekam; }

void konfig_set_sumber(int s, int nomor)
{
    if (s != sumber) tulis("sumber", s);
    if (nomor != sumber_rekam) {
        Preferences p;
        p.begin(NS, BUKAN_READ_ONLY);
        p.putUShort("rekam", (uint16_t)nomor);
        p.end();
    }
    sumber = s;
    sumber_rekam = nomor;
}
#endif
