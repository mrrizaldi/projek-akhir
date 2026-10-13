#include "ecg_mqtt.h"

#include <stdio.h>
#include <string.h>

static ecg_mqtt_beat_t antre_cadangan[ECG_MQTT_ANTRE_MIN];
static ecg_mqtt_beat_t *antre = antre_cadangan;
static size_t antre_kap = ECG_MQTT_ANTRE_MIN;
static size_t antre_kepala, antre_isi;
static size_t antre_hilang;

void ecg_mqtt_antre_pasang(ecg_mqtt_beat_t *mem, size_t kapasitas)
{
    antre = (mem && kapasitas) ? mem : antre_cadangan;
    antre_kap = (mem && kapasitas) ? kapasitas : ECG_MQTT_ANTRE_MIN;
    antre_kepala = antre_isi = antre_hilang = 0;
}

size_t ecg_mqtt_antre_kapasitas(void) { return antre_kap; }

void ecg_mqtt_antre_reset(void) { antre_kepala = antre_isi = antre_hilang = 0; }
size_t ecg_mqtt_antre_n(void) { return antre_isi; }
size_t ecg_mqtt_antre_hilang(void) { return antre_hilang; }

void ecg_mqtt_antre_isi(const ecg_mqtt_beat_t *b)
{
    if (antre_isi == antre_kap) {
        antre_kepala = (antre_kepala + 1) % antre_kap;
        antre_isi--;
        antre_hilang++;
    }
    antre[(antre_kepala + antre_isi) % antre_kap] = *b;
    antre_isi++;
}

size_t ecg_mqtt_antre_intip(ecg_mqtt_beat_t *keluar, size_t maks)
{
    const size_t n = antre_isi < maks ? antre_isi : maks;
    for (size_t i = 0; i < n; i++)
        keluar[i] = antre[(antre_kepala + i) % antre_kap];
    return n;
}

void ecg_mqtt_antre_buang(size_t n)
{
    if (n > antre_isi) n = antre_isi;
    antre_kepala = (antre_kepala + n) % antre_kap;
    antre_isi -= n;
}

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

#ifdef ARDUINO
#include <Arduino.h>
#include <WiFi.h>
#include <time.h>
#include <sys/time.h>

#define TOPIK "v1/devices/me/telemetry"

static const char *w_ssid = "", *w_pass = "", *b_host = "", *b_token = "";
static uint16_t b_port = 1883;

static WiFiClient sock;
static bool aktif = true, tersambung;
static uint32_t t_coba, t_ping, t_layani, terkirim, gagal;
static uint32_t paket_kirim, paket_ack;
static uint32_t rtt_maks, rtt_lambat;
static bool menunggu_ack, menunggu_connack;
static uint32_t t_kirim;
static size_t n_terbang;
static uint16_t pid;
static uint64_t ts_base_ms;
#define ECG_HDR_MAKS (1 + 3 + 2 + 64 + 2)
constexpr uint8_t MQTT_FLAG_USERNAME = 0x80, MQTT_KEEPALIVE_S = 60;
constexpr uint8_t MQTT_PUBLISH_QOS1 = 0x32, MQTT_PUBACK = 0x40, MQTT_PANJANG_LANJUT = 0x80;
constexpr uint32_t BATAS_TULIS_MS = 200, CONNECT_TIMEOUT_MS = 300, PERIODE_LAYANI_MS = 20;
constexpr uint32_t JEDA_COBA_MS = 5000, PERIODE_PING_MS = 30000;
constexpr time_t EPOCH_SNTP_MIN = 1700000000;
static uint8_t paket_buf[ECG_HDR_MAKS + ECG_MQTT_BATCH_N * 320 + 8];

static size_t varlen(uint8_t *out, size_t n)
{
    size_t i = 0;
    do { uint8_t b = n % 128; n /= 128; out[i++] = b | (n ? 0x80 : 0); } while (n);
    return i;
}

static void putus(const char *sebab)
{
    if (tersambung) Serial.printf("mqtt putus (%s)\n", sebab);
    sock.stop();
    tersambung = false;
    menunggu_ack = menunggu_connack = false;
    n_terbang = 0;
}

static bool kirim_sampai_habis(const uint8_t *p, size_t n)
{
    const uint32_t t0 = millis();
    size_t p_kirim = 0;
    while (p_kirim < n) {
        const size_t w = sock.write(p + p_kirim, n - p_kirim);
        p_kirim += w;
        if (p_kirim == n) return true;
        if (!sock.connected() || millis() - t0 > BATAS_TULIS_MS) return false;
    }
    return true;
}

static void kirim_connect()
{
    const char *cid = "esp32-ecg", *user = b_token;
    const size_t lc = strlen(cid), lu = strlen(user);
    uint8_t var[16];
    size_t v = 0;
    memcpy(var + v, "\x00\x04MQTT\x04", 7); v = 7;
    var[v++] = MQTT_FLAG_USERNAME;
    var[v++] = 0; var[v++] = MQTT_KEEPALIVE_S;
    const size_t rem = v + 2 + lc + 2 + lu;

    uint8_t paket[5 + sizeof var + 2 + 32 + 2 + 64];
    size_t q = 0;
    paket[q++] = 0x10;
    q += varlen(paket + q, rem);
    memcpy(paket + q, var, v); q += v;
    paket[q++] = (uint8_t)(lc >> 8); paket[q++] = (uint8_t)(lc & 0xFF);
    memcpy(paket + q, cid, lc); q += lc;
    paket[q++] = (uint8_t)(lu >> 8); paket[q++] = (uint8_t)(lu & 0xFF);
    memcpy(paket + q, user, lu); q += lu;
    if (!kirim_sampai_habis(paket, q)) { putus("write CONNECT tidak habis"); return; }

    t_kirim = millis();
    menunggu_connack = true;
}

static void pungut_connack()
{
    if (sock.available() >= 4) {
        uint8_t ack[4];
        sock.readBytes(ack, 4);
        menunggu_connack = false;
        if (ack[0] != 0x20 || ack[3] != 0x00) {
            Serial.printf("mqtt CONNACK ditolak kode %u\n", ack[3]);
            putus("CONNACK");
            return;
        }
        tersambung = true;
        t_ping = millis();
        Serial.printf("mqtt tersambung, backlog %u beat\n", (unsigned)ecg_mqtt_antre_n());
        return;
    }
    if (millis() - t_kirim > 2000) putus("CONNACK timeout");
}

static bool kirim_batch(const ecg_mqtt_beat_t *b, size_t nb, uint64_t base)
{
    char *muatan = (char *)paket_buf + ECG_HDR_MAKS;
    const size_t n = ecg_mqtt_payload(muatan, sizeof paket_buf - ECG_HDR_MAKS, b, nb, base);
    if (!n) { gagal++; putus("payload tidak muat"); return false; }

    const size_t lt = strlen(TOPIK);
    pid = (uint16_t)(pid % 65535) + 1;
    const size_t rem = 2 + lt + 2 + n;

    uint8_t h[ECG_HDR_MAKS];
    size_t q = 0;
    h[q++] = MQTT_PUBLISH_QOS1;
    q += varlen(h + q, rem);
    h[q++] = (uint8_t)(lt >> 8); h[q++] = (uint8_t)(lt & 0xFF);
    memcpy(h + q, TOPIK, lt); q += lt;
    h[q++] = (uint8_t)(pid >> 8); h[q++] = (uint8_t)(pid & 0xFF);

    uint8_t *awal = paket_buf + ECG_HDR_MAKS - q;
    memcpy(awal, h, q);

    if (!kirim_sampai_habis(awal, q + n)) { gagal++; putus("write tidak habis"); return false; }

    paket_kirim++;
    t_ping = t_kirim = millis();
    menunggu_ack = true;
    return true;
}

static void pungut_masuk()
{
    while (sock.available() >= 2) {
        uint8_t h[2];
        if (sock.readBytes(h, 2) != 2) return;
        if (h[1] & MQTT_PANJANG_LANJUT) { putus("panjang sisa > 127"); return; }
        size_t rem = h[1];

        if ((h[0] & 0xF0) == MQTT_PUBACK && rem == 2) {
            uint8_t b[2];
            if (sock.readBytes(b, 2) != 2) { putus("PUBACK pendek"); return; }
            const uint16_t got = (uint16_t)((b[0] << 8) | b[1]);
            if (menunggu_ack && got == pid) {
                const uint32_t rtt = millis() - t_kirim;
                if (rtt > rtt_maks) rtt_maks = rtt;
                if (rtt > 1000) {
                    rtt_lambat++;
                    Serial.printf("mqtt: PUBACK lambat %lu ms (%u beat)\n",
                                  (unsigned long)rtt, (unsigned)n_terbang);
                }
                menunggu_ack = false;
                paket_ack++;
                ecg_mqtt_antre_buang(n_terbang);
                terkirim += n_terbang;
                n_terbang = 0;
            }
            continue;
        }
        while (rem--) { if (sock.read() < 0) return; }
    }
}

void ecg_mqtt_atur(const char *ssid, const char *pass, const char *host, uint16_t port,
                   const char *token)
{
    w_ssid = ssid; w_pass = pass; b_host = host; b_port = port; b_token = token;
    putus("ganti target");
    t_coba = 0;
}

void ecg_mqtt_mulai(void)
{
    if (!strlen(w_ssid)) {
        Serial.println("mqtt NONAKTIF: include/wifi_secrets.h belum ada "
                       "(salin dari wifi_secrets.example.h)");
        aktif = false;
        return;
    }
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.begin(w_ssid, w_pass);
    configTzTime("WIB-7", "pool.ntp.org", "time.google.com");
    Serial.printf("mqtt: WiFi \"%s\" -> %s:%u\n", w_ssid, b_host, (unsigned)b_port);
}

static void sinkron_jam()
{
    if (ts_base_ms) return;
    struct timeval tv;
    if (gettimeofday(&tv, NULL) != 0) return;
    if (tv.tv_sec < EPOCH_SNTP_MIN) return;
    const uint64_t kini_ms = (uint64_t)tv.tv_sec * 1000ULL + (uint64_t)(tv.tv_usec / 1000);
    ts_base_ms = kini_ms - (uint64_t)millis();
    Serial.printf("mqtt: jam tersinkron, epoch_ms %llu\n", (unsigned long long)kini_ms);
}

uint64_t ecg_mqtt_epoch_ms(void)
{
    return ts_base_ms ? ts_base_ms + (uint64_t)millis() : 0;
}

void ecg_mqtt_layani(void)
{
    if (!aktif) return;
    if (millis() - t_layani < PERIODE_LAYANI_MS) return;
    t_layani = millis();

    sinkron_jam();

    if (!sock.connected()) {
        tersambung = false;
        menunggu_ack = menunggu_connack = false;
        n_terbang = 0;
        if (WiFi.status() != WL_CONNECTED) return;
        if (millis() - t_coba < JEDA_COBA_MS) return;
        t_coba = millis();
        IPAddress ip;
        if (!ip.fromString(b_host)) {
            Serial.printf("mqtt: host broker \"%s\" bukan alamat IP\n", b_host);
            aktif = false;
            return;
        }
        if (!sock.connect(ip, b_port, CONNECT_TIMEOUT_MS)) return;
        sock.setNoDelay(true);
        kirim_connect();
        return;
    }

    if (!tersambung) { pungut_connack(); return; }

    pungut_masuk();
    if (menunggu_ack) {
        if (millis() - t_kirim > 5000) {
            gagal++;
            Serial.printf("mqtt: PUBACK timeout, %u beat terbang, %d byte menunggu dibaca\n",
                          (unsigned)n_terbang, sock.available());
            putus("PUBACK timeout");
        }
        return;
    }

    if (ecg_mqtt_antre_n() && ts_base_ms) {
        static ecg_mqtt_beat_t petak[ECG_MQTT_BATCH_N];
        const size_t n = ecg_mqtt_antre_intip(petak, ECG_MQTT_BATCH_N);
        if (kirim_batch(petak, n, ts_base_ms)) n_terbang = n;
        return;
    }

    if (millis() - t_ping > PERIODE_PING_MS) {
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
uint32_t ecg_mqtt_paket_kirim(void) { return paket_kirim; }
uint32_t ecg_mqtt_paket_ack(void) { return paket_ack; }

uint32_t ecg_mqtt_rtt_maks(void) { return rtt_maks; }
uint32_t ecg_mqtt_rtt_lambat(void) { return rtt_lambat; }

int ecg_mqtt_rssi(void) { return WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : 0; }

const char *ecg_mqtt_status(void)
{
    if (!aktif) return "mati";
    if (WiFi.status() != WL_CONNECTED) return "no-wifi";
    if (!tersambung) return "no-broker";
    if (!ts_base_ms) return "tunggu-jam";
    return "online";
}
#endif
