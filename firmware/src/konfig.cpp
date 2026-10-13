// Konfigurasi jaringan + NVS. Kontrak: include/konfig.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "konfig.h"

#include <Arduino.h>
#include <Preferences.h>

#include "ecg_mqtt.h"

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
#define WIFI_DAFTAR {{"", ""}}                 // SSID kosong = MQTT nonaktif
#endif
#ifndef BROKER_DAFTAR
#define BROKER_DAFTAR {{"-", "", 1883, ""}}
#endif

static const wifi_t WIFI[] = WIFI_DAFTAR;
static const broker_t BROKER[] = BROKER_DAFTAR;
constexpr int N_WIFI = sizeof WIFI / sizeof WIFI[0];
constexpr int N_BROKER = sizeof BROKER / sizeof BROKER[0];

constexpr const char *NS = "konfig";
static int i_wifi, i_broker, sumber, sumber_rekam;

static int baca(const char *kunci, int n)
{
    Preferences p;
    p.begin(NS, false);                    // bukan read-only: namespace dibuat bila belum ada
    const int v = p.getUChar(kunci, 0);
    p.end();
    return v < n ? v : 0;                  // daftar di wifi_secrets.h bisa memendek
}

static void tulis(const char *kunci, int v)
{
    Preferences p;
    p.begin(NS, false);
    p.putUChar(kunci, (uint8_t)v);
    p.end();
}

static void terapkan()
{
    const wifi_t &w = WIFI[i_wifi];
    const broker_t &b = BROKER[i_broker];
    ecg_mqtt_atur(w.ssid, w.pass, b.host, b.port, b.token);
    Serial.printf("konfig: wifi %d/%d \"%s\" | broker %d/%d %s (%s:%u)\n",
                  i_wifi, N_WIFI, w.ssid, i_broker, N_BROKER, b.nama, b.host, (unsigned)b.port);
}

void konfig_mulai(void)
{
    i_wifi = baca("wifi", N_WIFI);
    i_broker = baca("broker", N_BROKER);
    sumber = baca("sumber", 3);
    Preferences p;                         // nomor rekaman bisa > 255: kunci terpisah, uint16
    p.begin(NS, false);
    sumber_rekam = p.getUShort("rekam", 0);
    p.end();
    terapkan();
}

int konfig_wifi_n(void) { return N_WIFI; }
const char *konfig_wifi_nama(int i) { return i >= 0 && i < N_WIFI ? WIFI[i].ssid : ""; }
int konfig_wifi(void) { return i_wifi; }

int konfig_broker_n(void) { return N_BROKER; }
const char *konfig_broker_nama(int i) { return i >= 0 && i < N_BROKER ? BROKER[i].nama : ""; }
const char *konfig_broker_host(int i) { return i >= 0 && i < N_BROKER ? BROKER[i].host : ""; }
int konfig_broker_port(int i) { return i >= 0 && i < N_BROKER ? BROKER[i].port : 0; }
int konfig_broker(void) { return i_broker; }

// ecg_mqtt_mulai() ulang: WiFi.begin() dengan SSID yang sama tidak memutus
// sambungan, dengan SSID lain memutus lalu menyambung ke yang baru.
// ponytail: dipanggil saat radio dimatikan tangga daya (p0-p4) ikut
// menyalakan WiFi; pilih jaringan di mode normal.
bool konfig_pilih_wifi(int i)
{
    if (i < 0 || i >= N_WIFI) return false;
    i_wifi = i;
    tulis("wifi", i);
    terapkan();
    ecg_mqtt_mulai();
    return true;
}

bool konfig_pilih_broker(int i)
{
    if (i < 0 || i >= N_BROKER) return false;
    i_broker = i;
    tulis("broker", i);
    terapkan();
    return true;
}

int konfig_sumber(void) { return sumber; }
int konfig_sumber_rekam(void) { return sumber_rekam; }

void konfig_set_sumber(int s, int nomor)
{
    if (s != sumber) tulis("sumber", s);   // NVS hanya ditulis bila berubah
    if (nomor != sumber_rekam) {
        Preferences p;
        p.begin(NS, false);
        p.putUShort("rekam", (uint16_t)nomor);
        p.end();
    }
    sumber = s;
    sumber_rekam = nomor;
}
#endif
