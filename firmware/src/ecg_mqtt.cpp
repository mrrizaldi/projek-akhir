#include "ecg_mqtt.h"

#include <stdio.h>
#include <string.h>

// ======================= MURNI =======================

static ecg_mqtt_beat_t antre[ECG_MQTT_ANTRE_N];
static size_t antre_kepala, antre_isi;
static size_t antre_hilang;

void ecg_mqtt_antre_reset(void) { antre_kepala = antre_isi = antre_hilang = 0; }
size_t ecg_mqtt_antre_n(void) { return antre_isi; }
size_t ecg_mqtt_antre_hilang(void) { return antre_hilang; }

void ecg_mqtt_antre_isi(const ecg_mqtt_beat_t *b)
{
    if (antre_isi == ECG_MQTT_ANTRE_N) {           // penuh: buang yang tertua
        antre_kepala = (antre_kepala + 1) % ECG_MQTT_ANTRE_N;
        antre_isi--;
        antre_hilang++;
    }
    antre[(antre_kepala + antre_isi) % ECG_MQTT_ANTRE_N] = *b;
    antre_isi++;
}

size_t ecg_mqtt_antre_intip(ecg_mqtt_beat_t *keluar, size_t maks)
{
    const size_t n = antre_isi < maks ? antre_isi : maks;
    for (size_t i = 0; i < n; i++)
        keluar[i] = antre[(antre_kepala + i) % ECG_MQTT_ANTRE_N];
    return n;
}

void ecg_mqtt_antre_buang(size_t n)
{
    if (n > antre_isi) n = antre_isi;
    antre_kepala = (antre_kepala + n) % ECG_MQTT_ANTRE_N;
    antre_isi -= n;
}

// Satu record. Nama field ikut dashboard/README.md — snake_case, bukan
// camelCase yang disarankan docs ThingsBoard: proposal sudah terlanjur menulis
// snake_case dan snake_case tetap jalan normal.
static size_t satu(char *buf, size_t n, const ecg_mqtt_beat_t *b, uint64_t ts)
{
    int w = snprintf(buf, n,
        "{\"ts\":%llu,\"values\":{\"bpm\":%.1f,\"rr_interval_ms\":%.1f,"
        "\"label\":%d,\"label_str\":\"%s\",\"confidence\":%.4f,"
        "\"signal_quality\":\"%s\",\"ecg_snippet\":[",
        (unsigned long long)ts, b->bpm, b->rr_ms, b->label,
        b->label ? "Aritmia" : "Normal", b->confidence,
        b->quality_ok ? "good" : "poor");
    if (w < 0 || (size_t)w >= n) return 0;
    size_t p = (size_t)w;
    for (int i = 0; i < ECG_SNIPPET_N; i++) {
        w = snprintf(buf + p, n - p, "%s%d", i ? "," : "", b->snippet[i]);
        if (w < 0 || (size_t)w >= n - p) return 0;
        p += (size_t)w;
    }
    w = snprintf(buf + p, n - p, "]}}");
    if (w < 0 || (size_t)w >= n - p) return 0;
    return p + (size_t)w;
}

size_t ecg_mqtt_payload(char *buf, size_t n, const ecg_mqtt_beat_t *b, size_t nb,
                        uint64_t ts_base_ms)
{
    if (!buf || !b || nb == 0 || n == 0) return 0;
    if (nb == 1) return satu(buf, n, b, ts_base_ms + b[0].ms);

    size_t p = 0;
    if (p + 1 >= n) return 0;
    buf[p++] = '[';
    for (size_t i = 0; i < nb; i++) {
        if (i) { if (p + 1 >= n) return 0; buf[p++] = ','; }
        const size_t w = satu(buf + p, n - p, &b[i], ts_base_ms + b[i].ms);
        if (w == 0) return 0;
        p += w;
    }
    if (p + 2 > n) return 0;
    buf[p++] = ']';
    buf[p] = '\0';
    return p;
}

// ======================= JARINGAN =======================
#ifdef ARDUINO
#include <Arduino.h>
#include <WiFi.h>
#include <time.h>

#if __has_include("wifi_secrets.h")
#include "wifi_secrets.h"
#endif
#ifndef WIFI_SSID
#define WIFI_SSID ""
#define WIFI_PASS ""
#define TB_HOST   ""
#define TB_PORT   1883
#define TB_TOKEN  ""
#endif

#define TOPIK "v1/devices/me/telemetry"

// Klien MQTT ditulis langsung di atas WiFiClient, bukan menambah PubSubClient.
// Yang dipakai cuma CONNECT / PUBLISH QoS1 / PUBACK / PINGREQ — empat paket,
// dan kawatnya sudah terbukti: dashboard/smoke_test.py bicara ke broker yang
// SAMA dengan byte yang sama. Sejalan dgn gate point CLAUDE.md (jangan tambah
// dependency untuk yang beberapa baris sudah selesai) dan dengan preseden
// ina219.cpp yang juga tanpa library.
static WiFiClient sock;
static bool aktif = true, tersambung;
static uint32_t t_coba, t_ping, terkirim, gagal;
static uint16_t pid;
static uint64_t ts_base_ms;            // epoch ms saat millis() == 0
static char buf[ECG_MQTT_BATCH_N * 320 + 8];

static size_t varlen(uint8_t *out, size_t n)
{
    size_t i = 0;
    do { uint8_t b = n % 128; n /= 128; out[i++] = b | (n ? 0x80 : 0); } while (n);
    return i;
}

static bool tunggu(size_t n, uint32_t batas_ms)
{
    const uint32_t t0 = millis();
    while (sock.available() < (int)n) {
        if (millis() - t0 > batas_ms || !sock.connected()) return false;
        delay(1);
    }
    return true;
}

static void putus(const char *sebab)
{
    if (tersambung) Serial.printf("mqtt putus (%s)\n", sebab);
    sock.stop();
    tersambung = false;
}

static bool connect_mqtt()
{
    const char *cid = "esp32-ecg", *user = TB_TOKEN;
    const size_t lc = strlen(cid), lu = strlen(user);
    uint8_t var[16];
    size_t v = 0;
    memcpy(var + v, "\x00\x04MQTT\x04", 7); v = 7;
    var[v++] = 0x80;                                   // flags: username saja
    var[v++] = 0; var[v++] = 60;                       // keepalive 60 s
    const size_t rem = v + 2 + lc + 2 + lu;

    uint8_t hdr[5]; hdr[0] = 0x10;
    const size_t lh = 1 + varlen(hdr + 1, rem);
    sock.write(hdr, lh);
    sock.write(var, v);
    uint8_t l2[2];
    l2[0] = lc >> 8; l2[1] = lc & 0xFF; sock.write(l2, 2); sock.write((const uint8_t *)cid, lc);
    l2[0] = lu >> 8; l2[1] = lu & 0xFF; sock.write(l2, 2); sock.write((const uint8_t *)user, lu);

    if (!tunggu(4, 3000)) { putus("CONNACK timeout"); return false; }
    uint8_t ack[4];
    sock.readBytes(ack, 4);
    if (ack[0] != 0x20 || ack[3] != 0x00) {
        Serial.printf("mqtt CONNACK ditolak kode %u\n", ack[3]);
        putus("CONNACK");
        return false;
    }
    return true;
}

// PUBLISH QoS 1 + tunggu PUBACK. Return true HANYA kalau PUBACK cocok — itu
// syarat sebelum backlog digeser.
static bool publish(const char *payload, size_t n)
{
    const size_t lt = strlen(TOPIK);
    pid = (uint16_t)(pid % 65535) + 1;
    const size_t rem = 2 + lt + 2 + n;

    uint8_t hdr[5]; hdr[0] = 0x32;                      // PUBLISH, QoS 1
    const size_t lh = 1 + varlen(hdr + 1, rem);
    sock.write(hdr, lh);
    uint8_t l2[2] = { (uint8_t)(lt >> 8), (uint8_t)(lt & 0xFF) };
    sock.write(l2, 2); sock.write((const uint8_t *)TOPIK, lt);
    l2[0] = pid >> 8; l2[1] = pid & 0xFF; sock.write(l2, 2);
    sock.write((const uint8_t *)payload, n);

    if (!tunggu(4, 3000)) { putus("PUBACK timeout"); gagal++; return false; }
    uint8_t ack[4];
    sock.readBytes(ack, 4);
    const uint16_t got = (uint16_t)((ack[2] << 8) | ack[3]);
    if (ack[0] != 0x40 || got != pid) { putus("PUBACK tak cocok"); gagal++; return false; }
    t_ping = millis();
    return true;
}

void ecg_mqtt_mulai(void)
{
    if (!strlen(WIFI_SSID)) {
        Serial.println("mqtt NONAKTIF: include/wifi_secrets.h belum ada "
                       "(salin dari wifi_secrets.example.h)");
        aktif = false;
        return;
    }
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    // SNTP dipakai supaya ts tiap beat adalah waktu KEJADIAN. Tanpa jam benar,
    // beat hasil flush backlog akan menumpuk di detik yang sama dan grafik
    // dashboard berbohong.
    configTime(0, 0, "pool.ntp.org", "time.google.com");
    Serial.printf("mqtt: WiFi \"%s\" -> %s:%d\n", WIFI_SSID, TB_HOST, TB_PORT);
}

static void sinkron_jam()
{
    if (ts_base_ms) return;
    time_t t = time(NULL);
    if (t < 1700000000) return;                        // SNTP belum masuk
    ts_base_ms = (uint64_t)t * 1000ULL - (uint64_t)millis();
    Serial.printf("mqtt: jam tersinkron, epoch %llu\n", (unsigned long long)t);
}

void ecg_mqtt_layani(void)
{
    if (!aktif) return;
    sinkron_jam();

    if (!sock.connected()) {
        tersambung = false;
        if (WiFi.status() != WL_CONNECTED) return;
        if (millis() - t_coba < 5000) return;          // jangan banjiri broker
        t_coba = millis();
        if (!sock.connect(TB_HOST, TB_PORT)) return;
        if (!connect_mqtt()) return;
        tersambung = true;
        t_ping = millis();
        Serial.printf("mqtt tersambung, backlog %u beat\n", (unsigned)ecg_mqtt_antre_n());
    }

    // Kirim apa pun yang tertahan. Satu batch per panggilan supaya loop tetap
    // responsif terhadap sampel ADC — antrean ISR cuma 256 dalam.
    if (ecg_mqtt_antre_n() && ts_base_ms) {
        static ecg_mqtt_beat_t petak[ECG_MQTT_BATCH_N];
        const size_t n = ecg_mqtt_antre_intip(petak, ECG_MQTT_BATCH_N);
        const size_t w = ecg_mqtt_payload(buf, sizeof buf, petak, n, ts_base_ms);
        if (w && publish(buf, w)) {
            ecg_mqtt_antre_buang(n);                   // HANYA setelah PUBACK
            terkirim += n;
        }
        return;
    }

    if (millis() - t_ping > 30000) {                   // PINGREQ < keepalive 60 s
        const uint8_t ping[2] = { 0xC0, 0x00 };
        sock.write(ping, 2);
        t_ping = millis();
    }
}

int ecg_mqtt_tersambung(void) { return tersambung ? 1 : 0; }
int ecg_mqtt_aktif(void) { return aktif ? 1 : 0; }
void ecg_mqtt_set_aktif(int on) { aktif = on != 0; if (!on) putus("dimatikan"); }
uint32_t ecg_mqtt_terkirim(void) { return terkirim; }
uint32_t ecg_mqtt_gagal(void) { return gagal; }

const char *ecg_mqtt_status(void)
{
    if (!aktif) return "mati";
    if (WiFi.status() != WL_CONNECTED) return "no-wifi";
    if (!tersambung) return "no-broker";
    if (!ts_base_ms) return "tunggu-jam";
    return "online";
}
#endif  // ARDUINO
