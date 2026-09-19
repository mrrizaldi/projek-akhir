#include "ecg_mqtt.h"

#include <stdio.h>
#include <string.h>

// ======================= MURNI =======================

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
    if (antre_isi == antre_kap) {                  // penuh: buang yang tertua
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
#include <sys/time.h>

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
static uint32_t t_coba, t_ping, t_layani, terkirim, gagal;
static uint32_t paket_kirim, paket_ack;   // PDSR bab3.tex: per PAKET
static uint32_t rtt_maks, rtt_lambat;     // diagnosa: RTT PUBACK
// PUBLISH tidak menunggu PUBACK di tempat. Menunggu di sini berarti memblokir
// loop() yang sedang menguras antrean ADC: satu timeout 3 detik = ~1.080 sampel
// hilang dari antrean 256, dan interval RR rusak. Diukur di board 19 Sep 2026:
// sampel hilang 4.493, antrean 255/256 penuh. Jadi PUBACK ditunggu LINTAS
// iterasi loop(), bukan di dalam satu panggilan.
static bool menunggu_ack, menunggu_connack;
static uint32_t t_kirim;
static size_t n_terbang;                   // beat yang sudah dikirim, belum ber-PUBACK
static uint16_t pid;
static uint64_t ts_base_ms;            // epoch ms saat millis() == 0
// Satu buffer saja. Payload dirakit LANGSUNG di dalam paket, di belakang ruang
// header, lalu headernya ditempel mundur tepat sebelum payload. Versi dua-buffer
// (payload + paket) memakan 32 KB RAM internal untuk batch 50; ini setengahnya.
//
// Header tidak bisa dipadding: panjang sisa MQTT harus dikodekan minimal, jadi
// jumlah bytenya ikut berubah dengan ukuran payload. Karena itu headernya dirakit
// di tempat terpisah yang kecil, baru disalin mundur.
#define ECG_HDR_MAKS (1 + 3 + 2 + 64 + 2)
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
    n_terbang = 0;          // backlog TIDAK dibuang: beat dikirim ulang nanti,
                            // dan ts identik membuat ThingsBoard meng-upsert
}

// Menulis sampai habis, dengan batas waktu.
//
// sock.write() bisa menulis lebih pendek dari yang diminta kalau buffer socket
// penuh — dan paket MQTT yang terpotong tidak pernah di-PUBACK (diukur di board:
// PUBACK timeout berulang padahal broker sehat, log broker bersih). Di sini
// sisanya diulang, bukan diabaikan.
//
// Batasnya 200 ms: harus di bawah kedalaman antrean ADC (256 sampel @360 Hz =
// 711 ms) supaya menulis paket besar tidak pernah menghilangkan sampel. Inilah
// yang membuat batch 50 rekaman (~15 KB, target bab3.tex) aman dikirim.
static bool kirim_sampai_habis(const uint8_t *p, size_t n)
{
    const uint32_t t0 = millis();
    size_t p_kirim = 0;
    while (p_kirim < n) {
        const size_t w = sock.write(p + p_kirim, n - p_kirim);
        p_kirim += w;
        if (p_kirim == n) return true;
        if (!sock.connected() || millis() - t0 > 200) return false;
    }
    return true;
}

// Menulis CONNECT lalu selesai. CONNACK dipungut pungut_connack() di iterasi
// berikutnya — tidak ada satu pun panggilan yang menunggu jaringan di tempat.
static void kirim_connect()
{
    const char *cid = "esp32-ecg", *user = TB_TOKEN;
    const size_t lc = strlen(cid), lu = strlen(user);
    uint8_t var[16];
    size_t v = 0;
    memcpy(var + v, "\x00\x04MQTT\x04", 7); v = 7;
    var[v++] = 0x80;                                   // flags: username saja
    var[v++] = 0; var[v++] = 60;                       // keepalive 60 s
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

// Menulis PUBLISH QoS 1 lalu SELESAI. PUBACK-nya dipungut ecg_mqtt_layani()
// di iterasi berikutnya; backlog baru digeser di sana.
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
    h[q++] = 0x32;                                      // PUBLISH, QoS 1
    q += varlen(h + q, rem);
    h[q++] = (uint8_t)(lt >> 8); h[q++] = (uint8_t)(lt & 0xFF);
    memcpy(h + q, TOPIK, lt); q += lt;
    h[q++] = (uint8_t)(pid >> 8); h[q++] = (uint8_t)(pid & 0xFF);

    uint8_t *awal = paket_buf + ECG_HDR_MAKS - q;       // tempel mundur
    memcpy(awal, h, q);

    if (!kirim_sampai_habis(awal, q + n)) { gagal++; putus("write tidak habis"); return false; }

    paket_kirim++;
    t_ping = t_kirim = millis();
    menunggu_ack = true;
    return true;
}

// Memungut SEMUA paket masuk tanpa memblokir, dan membuang yang tidak diminta.
//
// Versi pertama cuma membaca 4 byte begitu `available() >= 4` dan menganggapnya
// PUBACK. Itu salah: kita mengirim PINGREQ tiap 30 detik dan broker membalas
// PINGRESP (2 byte, 0xD0 0x00) yang tidak pernah dibaca. Dua byte nyasar itu
// mengendap di socket, lalu terbaca sebagai DUA BYTE PERTAMA "PUBACK"
// berikutnya — aliran baca desync permanen sampai reconnect.
//
// Gejalanya di board: `PUBACK timeout` acak tiap ~30 detik walau broker sehat,
// dan latensi end-to-end berekor panjang (p95 10,4 detik, maks 19,5 detik)
// karena setiap desync memakan 5 detik timeout + reconnect. Diukur 19 Sep 2026.
static void pungut_masuk()
{
    while (sock.available() >= 2) {
        uint8_t h[2];
        if (sock.readBytes(h, 2) != 2) return;
        if (h[1] & 0x80) { putus("panjang sisa > 127"); return; }   // tak diharapkan
        size_t rem = h[1];

        if ((h[0] & 0xF0) == 0x40 && rem == 2) {                    // PUBACK
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
                ecg_mqtt_antre_buang(n_terbang);        // HANYA setelah PUBACK
                terkirim += n_terbang;
                n_terbang = 0;
            }
            continue;
        }
        // PINGRESP (0xD0) dan apa pun yang tidak kita minta: buang isinya utuh
        // supaya byte berikutnya tetap jatuh di batas paket.
        while (rem--) { if (sock.read() < 0) return; }
    }
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
    // Power save WiFi DIMATIKAN. Bawaan ESP32 (WIFI_PS_MIN_MODEM) menidurkan
    // radio antar-beacon; paket masuk yang datang saat tidur bisa hilang, dan
    // TCP menggantinya dengan retransmisi ber-RTO 1-2-4 detik. Itu persis pola
    // RTT PUBACK yang terukur di board (1.236 / 2.037 / 4.235 ms), dan bukan
    // broker yang lambat: dari laptop ke broker yang SAMA, RTT-nya 1,1 ms
    // median dengan nol kejadian >1 detik.
    //
    // ONGKOSNYA DAYA (~+30 mA). Pengukuran daya mode WiFi (HW-7) belum
    // dijalankan, jadi angkanya harus diambil DENGAN setelan ini, bukan tanpa.
    WiFi.setSleep(false);
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
    // gettimeofday, BUKAN time(): time() beresolusi 1 detik, jadi memakainya
    // menanam galat sistematis sampai 1.000 ms pada SETIAP ts yang dikirim —
    // dan galat itu menyamar sebagai latensi saat dibandingkan dengan jam
    // laptop. Terukur: latensi minimum bergeser 934/1.045/1.286/1.347 ms
    // antar-boot tanpa ada yang berubah di sistemnya.
    struct timeval tv;
    if (gettimeofday(&tv, NULL) != 0) return;
    if (tv.tv_sec < 1700000000) return;                // SNTP belum masuk
    const uint64_t kini_ms = (uint64_t)tv.tv_sec * 1000ULL + (uint64_t)(tv.tv_usec / 1000);
    ts_base_ms = kini_ms - (uint64_t)millis();
    Serial.printf("mqtt: jam tersinkron, epoch_ms %llu\n", (unsigned long long)kini_ms);
}

// Epoch ms menurut JAM BOARD. Dipakai alat ukur di laptop untuk menghitung
// selisih jam kedua sisi, supaya selisih itu tidak terbaca sebagai latensi.
uint64_t ecg_mqtt_epoch_ms(void)
{
    return ts_base_ms ? ts_base_ms + (uint64_t)millis() : 0;
}

void ecg_mqtt_layani(void)
{
    if (!aktif) return;
    // Dipanggil sekali per sampel (360 Hz). WiFi.status() + time() sebanyak itu
    // ikut memakan anggaran 2.778 us/sampel, jadi dilayani tiap 20 ms saja —
    // masih 50x lebih sering daripada laju beat.
    if (millis() - t_layani < 20) return;
    t_layani = millis();

    sinkron_jam();

    if (!sock.connected()) {
        tersambung = false;
        menunggu_ack = menunggu_connack = false;
        n_terbang = 0;
        if (WiFi.status() != WL_CONNECTED) return;
        if (millis() - t_coba < 5000) return;          // jangan banjiri broker
        t_coba = millis();
        // Batas waktu WAJIB, dan harus di bawah kedalaman antrean ADC: 256
        // sampel @360 Hz = 711 ms, jadi blokir yang lebih lama dari itu mulai
        // menghilangkan sampel dan merusak RR. Terukur di board 19 Sep: tanpa
        // batas, `docker start` (port terbuka tapi broker belum menerima)
        // memblokir ~7,7 detik -> 2.788 sampel hilang.
        //
        // IPAddress, bukan hostname: resolusi DNS itu panggilan blocking
        // TERPISAH yang tidak ikut dibatasi argumen timeout ini.
        static IPAddress ip;
        static bool ip_siap;
        if (!ip_siap) ip_siap = ip.fromString(TB_HOST);
        if (!ip_siap) { Serial.println("mqtt: TB_HOST bukan alamat IP"); aktif = false; return; }
        if (!sock.connect(ip, TB_PORT, 300)) return;
        // TCP_NODELAY. Tanpa ini algoritma Nagle menahan segmen kecil sampai
        // ACK segmen sebelumnya datang; berpasangan dengan delayed-ACK broker,
        // PUBACK jadi terlambat 1,0-4,8 detik dengan nilai yang berulang di
        // ~1.250 ms (diukur di board: 27 kejadian >1 s dalam 130 detik, dan saat
        // timeout socket-nya KOSONG — jadi bukan desync, memang belum dijawab).
        // Payload kita ~330 B untuk satu beat = segmen kecil, tepat kasus Nagle.
        sock.setNoDelay(true);
        kirim_connect();
        return;
    }

    if (!tersambung) { pungut_connack(); return; }   // TCP hidup, MQTT belum

    pungut_masuk();                                 // termasuk membuang PINGRESP
    if (menunggu_ack) {
        if (millis() - t_kirim > 5000) {
            gagal++;
            Serial.printf("mqtt: PUBACK timeout, %u beat terbang, %d byte menunggu dibaca\n",
                          (unsigned)n_terbang, sock.available());
            putus("PUBACK timeout");
        }
        return;                                     // satu PUBLISH beredar saja
    }

    // Kirim apa pun yang tertahan. Satu batch per panggilan supaya loop tetap
    // responsif terhadap sampel ADC — antrean ISR cuma 256 dalam.
    if (ecg_mqtt_antre_n() && ts_base_ms) {
        static ecg_mqtt_beat_t petak[ECG_MQTT_BATCH_N];
        const size_t n = ecg_mqtt_antre_intip(petak, ECG_MQTT_BATCH_N);
        if (kirim_batch(petak, n, ts_base_ms)) n_terbang = n;
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
#endif  // ARDUINO
