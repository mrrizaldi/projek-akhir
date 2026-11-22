#include "ecg_mqtt.h"

#include <stdio.h>
#include <string.h>

static ecg_mqtt_beat_t queue_fallback[ECG_MQTT_QUEUE_MIN];
static ecg_mqtt_beat_t *queue = queue_fallback;
static size_t queue_cap = ECG_MQTT_QUEUE_MIN;
static size_t queue_head, queue_fill;
static size_t queue_lost;

void ecg_mqtt_queue_attach(ecg_mqtt_beat_t *mem, size_t capacity)
{
    queue = (mem && capacity) ? mem : queue_fallback;
    queue_cap = (mem && capacity) ? capacity : ECG_MQTT_QUEUE_MIN;
    queue_head = queue_fill = queue_lost = 0;
}

size_t ecg_mqtt_queue_capacity(void) { return queue_cap; }

size_t ecg_mqtt_queue_n(void) { return queue_fill; }
size_t ecg_mqtt_queue_lost(void) { return queue_lost; }

void ecg_mqtt_queue_fill(const ecg_mqtt_beat_t *b)
{
    if (queue_fill == queue_cap) {
        queue_head = (queue_head + 1) % queue_cap;
        queue_fill--;
        queue_lost++;
    }
    queue[(queue_head + queue_fill) % queue_cap] = *b;
    queue_fill++;
}

size_t ecg_mqtt_queue_peek(ecg_mqtt_beat_t *beats_out, size_t max_count)
{
    const size_t n = queue_fill < max_count ? queue_fill : max_count;
    for (size_t i = 0; i < n; i++)
        beats_out[i] = queue[(queue_head + i) % queue_cap];
    return n;
}

void ecg_mqtt_queue_drop(size_t n)
{
    if (n > queue_fill) n = queue_fill;
    queue_head = (queue_head + n) % queue_cap;
    queue_fill -= n;
}

static size_t one(char *buf, size_t n, const ecg_mqtt_beat_t *b, uint64_t ts)
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
    if (nb == 1) return one(buf, n, b, ts_base_ms + b[0].ms);

    size_t p = 0;
    if (p + 1 >= n) return 0;
    buf[p++] = '[';
    for (size_t i = 0; i < nb; i++) {
        if (i) { if (p + 1 >= n) return 0; buf[p++] = ','; }
        const size_t w = one(buf + p, n - p, &b[i], ts_base_ms + b[i].ms);
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

#define TOPIC "v1/devices/me/telemetry"

static const char *w_ssid = "", *w_pass = "", *b_host = "", *b_token = "";
static uint16_t b_port = 1883;

static WiFiClient sock;
static bool active = true, is_connected;
static uint32_t t_try, t_ping, t_service, sent, failed;
static uint32_t packet_send, packet_ack;
static uint32_t rtt_max, rtt_slow;
static bool waiting_ack, waiting_connack;
static uint32_t t_send;
static size_t n_in_flight;
static uint16_t pid;
static uint64_t ts_base_ms;
#define ECG_HDR_MAX (1 + 3 + 2 + 64 + 2)
constexpr uint8_t MQTT_FLAG_USERNAME = 0x80, MQTT_KEEPALIVE_S = 60;
constexpr uint8_t MQTT_PUBLISH_QOS1 = 0x32, MQTT_PUBACK = 0x40, MQTT_LENGTH_CONTINUE = 0x80;
constexpr uint32_t WRITE_LIMIT_MS = 200, CONNECT_TIMEOUT_MS = 300, PERIOD_SERVICE_MS = 20;
constexpr uint32_t RETRY_PAUSE_MS = 5000, PERIOD_PING_MS = 30000;
constexpr time_t EPOCH_SNTP_MIN = 1700000000;
static uint8_t packet_buf[ECG_HDR_MAX + ECG_MQTT_BATCH_N * 320 + 8];

static size_t varlen(uint8_t *out, size_t n)
{
    size_t i = 0;
    do { uint8_t b = n % 128; n /= 128; out[i++] = b | (n ? 0x80 : 0); } while (n);
    return i;
}

static void disconnect(const char *reason)
{
    if (is_connected) Serial.printf("mqtt disconnected (%s)\n", reason);
    sock.stop();
    is_connected = false;
    waiting_ack = waiting_connack = false;
    n_in_flight = 0;
}

static bool send_all(const uint8_t *p, size_t n)
{
    const uint32_t t0 = millis();
    size_t p_sent = 0;
    while (p_sent < n) {
        const size_t w = sock.write(p + p_sent, n - p_sent);
        p_sent += w;
        if (p_sent == n) return true;
        if (!sock.connected() || millis() - t0 > WRITE_LIMIT_MS) return false;
    }
    return true;
}

static void send_connect()
{
    const char *cid = "esp32-ecg", *user = b_token;
    const size_t lc = strlen(cid), lu = strlen(user);
    uint8_t var[16];
    size_t v = 0;
    memcpy(var + v, "\x00\x04MQTT\x04", 7); v = 7;
    var[v++] = MQTT_FLAG_USERNAME;
    var[v++] = 0; var[v++] = MQTT_KEEPALIVE_S;
    const size_t rem = v + 2 + lc + 2 + lu;

    uint8_t packet[5 + sizeof var + 2 + 32 + 2 + 64];
    size_t q = 0;
    packet[q++] = 0x10;
    q += varlen(packet + q, rem);
    memcpy(packet + q, var, v); q += v;
    packet[q++] = (uint8_t)(lc >> 8); packet[q++] = (uint8_t)(lc & 0xFF);
    memcpy(packet + q, cid, lc); q += lc;
    packet[q++] = (uint8_t)(lu >> 8); packet[q++] = (uint8_t)(lu & 0xFF);
    memcpy(packet + q, user, lu); q += lu;
    if (!send_all(packet, q)) { disconnect("CONNECT write incomplete"); return; }

    t_send = millis();
    waiting_connack = true;
}

static void poll_connack()
{
    if (sock.available() >= 4) {
        uint8_t ack[4];
        sock.readBytes(ack, 4);
        waiting_connack = false;
        if (ack[0] != 0x20 || ack[3] != 0x00) {
            Serial.printf("mqtt CONNACK rejected, code %u\n", ack[3]);
            disconnect("CONNACK");
            return;
        }
        is_connected = true;
        t_ping = millis();
        Serial.printf("mqtt connected, backlog %u beats\n", (unsigned)ecg_mqtt_queue_n());
        return;
    }
    if (millis() - t_send > 2000) disconnect("CONNACK timeout");
}

static bool send_batch(const ecg_mqtt_beat_t *b, size_t nb, uint64_t base)
{
    char *payload = (char *)packet_buf + ECG_HDR_MAX;
    const size_t n = ecg_mqtt_payload(payload, sizeof packet_buf - ECG_HDR_MAX, b, nb, base);
    if (!n) { failed++; disconnect("payload does not fit"); return false; }

    const size_t lt = strlen(TOPIC);
    pid = (uint16_t)(pid % 65535) + 1;
    const size_t rem = 2 + lt + 2 + n;

    uint8_t h[ECG_HDR_MAX];
    size_t q = 0;
    h[q++] = MQTT_PUBLISH_QOS1;
    q += varlen(h + q, rem);
    h[q++] = (uint8_t)(lt >> 8); h[q++] = (uint8_t)(lt & 0xFF);
    memcpy(h + q, TOPIC, lt); q += lt;
    h[q++] = (uint8_t)(pid >> 8); h[q++] = (uint8_t)(pid & 0xFF);

    uint8_t *start = packet_buf + ECG_HDR_MAX - q;
    memcpy(start, h, q);

    if (!send_all(start, q + n)) { failed++; disconnect("write incomplete"); return false; }

    packet_send++;
    t_ping = t_send = millis();
    waiting_ack = true;
    return true;
}

static void poll_incoming()
{
    while (sock.available() >= 2) {
        uint8_t h[2];
        if (sock.readBytes(h, 2) != 2) return;
        if (h[1] & MQTT_LENGTH_CONTINUE) { disconnect("remaining length > 127"); return; }
        size_t rem = h[1];

        if ((h[0] & 0xF0) == MQTT_PUBACK && rem == 2) {
            uint8_t b[2];
            if (sock.readBytes(b, 2) != 2) { disconnect("short PUBACK"); return; }
            const uint16_t got = (uint16_t)((b[0] << 8) | b[1]);
            if (waiting_ack && got == pid) {
                const uint32_t rtt = millis() - t_send;
                if (rtt > rtt_max) rtt_max = rtt;
                if (rtt > 1000) {
                    rtt_slow++;
                    Serial.printf("mqtt: slow PUBACK %lu ms (%u beats)\n",
                                  (unsigned long)rtt, (unsigned)n_in_flight);
                }
                waiting_ack = false;
                packet_ack++;
                ecg_mqtt_queue_drop(n_in_flight);
                sent += n_in_flight;
                n_in_flight = 0;
            }
            continue;
        }
        while (rem--) { if (sock.read() < 0) return; }
    }
}

void ecg_mqtt_configure(const char *ssid, const char *pass, const char *host, uint16_t port,
                   const char *token)
{
    w_ssid = ssid; w_pass = pass; b_host = host; b_port = port; b_token = token;
    disconnect("target changed");
    t_try = 0;
}

void ecg_mqtt_begin(void)
{
    if (!strlen(w_ssid)) {
        Serial.println("mqtt DISABLED: include/wifi_secrets.h is missing "
                       "(copy it from wifi_secrets.example.h)");
        active = false;
        return;
    }
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.begin(w_ssid, w_pass);
    configTzTime("WIB-7", "pool.ntp.org", "time.google.com");
    Serial.printf("mqtt: WiFi \"%s\" -> %s:%u\n", w_ssid, b_host, (unsigned)b_port);
}

static void sync_clock()
{
    if (ts_base_ms) return;
    struct timeval tv;
    if (gettimeofday(&tv, NULL) != 0) return;
    if (tv.tv_sec < EPOCH_SNTP_MIN) return;
    const uint64_t now_ms = (uint64_t)tv.tv_sec * 1000ULL + (uint64_t)(tv.tv_usec / 1000);
    ts_base_ms = now_ms - (uint64_t)millis();
    Serial.printf("mqtt: clock synced, epoch_ms %llu\n", (unsigned long long)now_ms);
}

uint64_t ecg_mqtt_epoch_ms(void)
{
    return ts_base_ms ? ts_base_ms + (uint64_t)millis() : 0;
}

void ecg_mqtt_service(void)
{
    if (!active) return;
    if (millis() - t_service < PERIOD_SERVICE_MS) return;
    t_service = millis();

    sync_clock();

    if (!sock.connected()) {
        is_connected = false;
        waiting_ack = waiting_connack = false;
        n_in_flight = 0;
        if (WiFi.status() != WL_CONNECTED) return;
        if (millis() - t_try < RETRY_PAUSE_MS) return;
        t_try = millis();
        IPAddress ip;
        if (!ip.fromString(b_host)) {
            Serial.printf("mqtt: broker host \"%s\" is not an IP address\n", b_host);
            active = false;
            return;
        }
        if (!sock.connect(ip, b_port, CONNECT_TIMEOUT_MS)) return;
        sock.setNoDelay(true);
        send_connect();
        return;
    }

    if (!is_connected) { poll_connack(); return; }

    poll_incoming();
    if (waiting_ack) {
        if (millis() - t_send > 5000) {
            failed++;
            Serial.printf("mqtt: PUBACK timeout, %u beats in flight, %d bytes waiting to be read\n",
                          (unsigned)n_in_flight, sock.available());
            disconnect("PUBACK timeout");
        }
        return;
    }

    if (ecg_mqtt_queue_n() && ts_base_ms) {
        static ecg_mqtt_beat_t chunk[ECG_MQTT_BATCH_N];
        const size_t n = ecg_mqtt_queue_peek(chunk, ECG_MQTT_BATCH_N);
        if (send_batch(chunk, n, ts_base_ms)) n_in_flight = n;
        return;
    }

    if (millis() - t_ping > PERIOD_PING_MS) {
        const uint8_t ping[2] = { 0xC0, 0x00 };
        sock.write(ping, 2);
        t_ping = millis();
    }
}

int ecg_mqtt_active(void) { return active ? 1 : 0; }
void ecg_mqtt_set_active(int on) { active = on != 0; if (!on) disconnect("switched off"); }
uint32_t ecg_mqtt_sent(void) { return sent; }
uint32_t ecg_mqtt_failed(void) { return failed; }
uint32_t ecg_mqtt_packet_send(void) { return packet_send; }
uint32_t ecg_mqtt_packet_ack(void) { return packet_ack; }

uint32_t ecg_mqtt_rtt_max(void) { return rtt_max; }
uint32_t ecg_mqtt_rtt_slow(void) { return rtt_slow; }

int ecg_mqtt_rssi(void) { return WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : 0; }

static const char *status_name(const char *off, const char *no_clock)
{
    if (!active) return off;
    if (WiFi.status() != WL_CONNECTED) return "no-wifi";
    if (!is_connected) return "no-broker";
    if (!ts_base_ms) return no_clock;
    return "online";
}

const char *ecg_mqtt_status(void) { return status_name("mati", "tunggu-jam"); }
const char *ecg_mqtt_status_serial(void) { return status_name("off", "no-clock"); }
#endif
