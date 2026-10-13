#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "daya.h"

#include <Arduino.h>
#include <LittleFS.h>
#include <time.h>
#include "esp_wifi.h"

#include "akuisisi.h"
#include "ecg_mqtt.h"
#include "ina219.h"
#include "perangkat.h"
#include "rekam.h"

#ifndef DAYA_JENDELA_MS
#define DAYA_JENDELA_MS 10000
#endif
#ifndef DAYA_BLOK
#define DAYA_BLOK 6
#endif
constexpr uint32_t JENDELA_DAYA_MS = DAYA_JENDELA_MS;
constexpr int TANGGA_N = 6;
constexpr uint32_t PERIODE_BACA_INA219_MS = 100;

static bool ina_ada;
static int mode_daya = -1;
static uint32_t beat_dsp;
static bool mulai_ulang;
static void tangga_catat(int n, double i, double sd, double v, unsigned beat, unsigned lewat);

void daya_mulai(void) { ina_ada = ina219_mulai(I2C_SDA, I2C_SCL); }
bool daya_ina_ada(void) { return ina_ada; }
int daya_mode(void) { return mode_daya; }
bool daya_tahap(int t) { return mode_daya < 0 || mode_daya >= t; }
void daya_hitung_beat(void) { beat_dsp++; }

const char *daya_ina_teks(void)
{
    static char teks[48];
    float mA, V;
    if (ina_ada && ina219_baca(R_SHUNT, &mA, &V))
        snprintf(teks, sizeof teks, "I=%.1f mA V=%.3f V P=%.0f mW", mA, V, mA * V);
    else
        snprintf(teks, sizeof teks, "tidak menjawab");
    return teks;
}

void daya_set_mode(int m)
{
    static bool wifi_mati;
    if (rekam_tolak("mode daya")) return;
    mode_daya = m;
    akuisisi_timer(m != 0);
    if (m >= 0 && m < 5) {
        if (!wifi_mati) { ecg_mqtt_set_aktif(0); esp_wifi_stop(); }
        wifi_mati = true;
    } else if (wifi_mati) {
        esp_wifi_start();
        ecg_mqtt_mulai();
        ecg_mqtt_set_aktif(1);
        wifi_mati = false;
    }
    mulai_ulang = true;
    if (m < 0) Serial.println("daya: mode normal");
    else       Serial.printf("daya: mode p%d, jendela %lu s\n", m, (unsigned long)(JENDELA_DAYA_MS / 1000));
}

void daya_layani(void)
{
    static uint32_t t_baca, t_jendela, beat0, lewat0;
    static double jml, jml2, jml_v;
    static int n;
    if (mode_daya < 0 || !ina_ada || millis() - t_baca < PERIODE_BACA_INA219_MS) return;
    t_baca = millis();
    if (mulai_ulang) {
        mulai_ulang = false;
        jml = jml2 = jml_v = 0; n = 0;
        t_jendela = millis(); beat0 = beat_dsp; lewat0 = akuisisi_lewat();
    }
    float mA, V;
    if (ina219_baca(R_SHUNT, &mA, &V)) { jml += mA; jml2 += (double)mA * mA; jml_v += V; n++; }
    if (millis() - t_jendela < JENDELA_DAYA_MS || n == 0) return;
    const double i = jml / n, v = jml_v / n;
    const double sd = sqrt(fmax(jml2 / n - i * i, 0.0));
    const unsigned beat = beat_dsp - beat0, lewat = akuisisi_lewat() - lewat0;
    Serial.printf("DAYA p%d n=%d I=%.2f sd=%.2f mA V=%.3f P=%.1f mW beat=%u lewat=%u replay=%d\n",
                  mode_daya, n, i, sd, v, i * v, beat, lewat, (int)akuisisi_replay());
    tangga_catat(n, i, sd, v, beat, lewat);
    mulai_ulang = true;
}

struct jendela_t {
    char waktu[24];
    int8_t mode;
    uint16_t n;
    float i, sd, v;
    uint32_t beat, lewat;
    bool replay;
};
static jendela_t jd[TANGGA_N * DAYA_BLOK];
static int jd_n;
static int langkah = -1;
static int jendela_langkah;
static uint32_t t_langkah;
static int sumber_awal, rekam_awal;
static daya_baris_t hasil[TANGGA_N];
static int hasil_n;
static int berkas_akhir = -1;

static File buka_dir(void)
{
    LittleFS.mkdir("/daya");
    return LittleFS.open("/daya");
}

bool daya_tangga_aktif(void) { return langkah >= 0; }
int daya_tangga_langkah(void) { return langkah; }

int daya_tangga_hasil(daya_baris_t *keluar, int maks)
{
    const int k = min(hasil_n, maks);
    memcpy(keluar, hasil, k * sizeof *keluar);
    return k;
}

int daya_tangga_berkas(void)
{
    if (berkas_akhir >= 0) return berkas_akhir;
    berkas_akhir = 0;
    File d = buka_dir();
    if (d && d.isDirectory())
        for (File f = d.openNextFile(); f; f = d.openNextFile())
            berkas_akhir = max(berkas_akhir, atoi(f.name()));
    return berkas_akhir;
}

static void tangga_catat(int n, double i, double sd, double v, unsigned beat, unsigned lewat)
{
    if (langkah < 0 || mode_daya != langkah) return;
    const int k = jendela_langkah++;
    Serial.printf("tangga: p%d jendela %d/%d%s\n", langkah, k + 1, DAYA_BLOK + 1,
                  k ? "" : " (transien, dibuang)");
    if (!k || jd_n >= TANGGA_N * DAYA_BLOK) return;
    jendela_t &j = jd[jd_n++];
    const uint64_t ep = ecg_mqtt_epoch_ms();
    if (ep) {
        const time_t t = ep / 1000;
        struct tm tm;
        gmtime_r(&t, &tm);
        strftime(j.waktu, sizeof j.waktu, "%Y-%m-%dT%H:%M:%SZ", &tm);
    } else {
        snprintf(j.waktu, sizeof j.waktu, "+%lus", (unsigned long)(millis() / 1000));
    }
    j.mode = langkah; j.n = n; j.i = i; j.sd = sd; j.v = v;
    j.beat = beat; j.lewat = lewat; j.replay = akuisisi_replay();
}

static void mulai_langkah(int m)
{
    langkah = m;
    jendela_langkah = 0;
    t_langkah = millis();
    Serial.printf("tangga: langkah %d/%d (p%d), buang 1 + ambil %d jendela %lu s\n", m + 1,
                  TANGGA_N, m, DAYA_BLOK, (unsigned long)(JENDELA_DAYA_MS / 1000));
    daya_set_mode(m);
}

void daya_tangga_mulai(void)
{
    if (rekam_tolak("tangga daya")) return;
    if (langkah >= 0) { Serial.println("tangga: sudah berjalan"); return; }
    if (!ina_ada) { Serial.println("tangga: INA219 tidak terdeteksi, batal"); return; }
    jd_n = hasil_n = 0;
    sumber_awal = akuisisi_sumber();
    rekam_awal = akuisisi_sumber_rekam();
    if (sumber_awal != SUMBER_ACUAN) akuisisi_set_sumber(SUMBER_ACUAN, 0, false);
    Serial.printf("tangga: mulai, perkiraan %lu s\n",
                  (unsigned long)(TANGGA_N * (DAYA_BLOK + 1) * JENDELA_DAYA_MS / 1000));
    mulai_langkah(0);
}

static void selesai(const char *batal)
{
    langkah = -1;
    daya_set_mode(-1);
    if (akuisisi_sumber() != sumber_awal) akuisisi_set_sumber(sumber_awal, rekam_awal, false);
    if (batal) Serial.printf("tangga: BATAL, %s\n", batal);

    bool sah[TANGGA_N] = {};
    int gagal = 0;
    hasil_n = 0;
    for (int m = 0; m < TANGGA_N; m++) {
        double si = 0, si2 = 0, sv = 0, vmin = 1e9;
        unsigned beat = 0, lewat = 0;
        int k = 0;
        for (int r = 0; r < jd_n; r++) {
            if (jd[r].mode != m) continue;
            si += jd[r].i; si2 += (double)jd[r].i * jd[r].i; sv += jd[r].v;
            vmin = fmin(vmin, jd[r].v); beat += jd[r].beat; lewat += jd[r].lewat; k++;
        }
        if (!k) { sah[m] = false; break; }
        daya_baris_t &h = hasil[hasil_n++];
        h.i_ma = si / k;
        h.sd_ma = k > 1 ? sqrt(fmax((si2 - k * (double)h.i_ma * h.i_ma) / (k - 1), 0.0)) : 0;
        h.v = sv / k;
        h.p_mw = h.i_ma * h.v;
        sah[m] = !batal;
        char alasan[4][72];
        int na = 0;
        if (vmin < 1.0)
            snprintf(alasan[na++], 72, "V bus %.3f V < 1 V, INA219 tidak di jalur catu", vmin);
        if (m >= 1 && lewat) snprintf(alasan[na++], 72, "%u sampel hilang, beban tidak mewakili", lewat);
        if (m >= 2 && !beat) snprintf(alasan[na++], 72, "tidak ada beat, replay tidak berjalan");
        if (m >= 1) {
            const daya_baris_t &l = hasil[m - 1];
            const double dI = h.i_ma - l.i_ma, sd = fmax(h.sd_ma, l.sd_ma);
            if (dI < 0) snprintf(alasan[na++], 72, "arus turun %+.2f mA dari p%d", dI, m - 1);
            else if (dI <= 2 * sd)
                snprintf(alasan[na++], 72, "selisih %+.2f mA dari p%d <= 2 x sd %.2f", dI, m - 1, sd);
        }
        for (int a = 0; a < na; a++) Serial.printf("tangga: TIDAK SAH p%d: %s\n", m, alasan[a]);
        if (na) { sah[m] = false; gagal++; }
        snprintf(h.mode, sizeof h.mode, sah[m] ? "p%d" : "p%d!", m);
        Serial.printf("tangga: p%d I=%.2f sd=%.2f mA V=%.3f P=%.1f mW %s\n", m, h.i_ma, h.sd_ma,
                      h.v, h.p_mw, sah[m] ? "sah" : "TIDAK SAH");
    }
    if (!jd_n) return;

    const int nomor = daya_tangga_berkas() + 1;
    char p[24];
    snprintf(p, sizeof p, "/daya/%03d.csv", nomor);
    File f = LittleFS.open(p, "w");
    if (!f) { Serial.printf("tangga: GAGAL membuka %s\n", p); return; }
    f.println("waktu,mode,n,I_mA,sd_mA,V,P_mW,beat,lewat,replay,sah");
    for (int r = 0; r < jd_n; r++) {
        const jendela_t &j = jd[r];
        f.printf("%s,%d,%u,%.2f,%.2f,%.3f,%.1f,%u,%u,%d,%d\n", j.waktu, j.mode, j.n, j.i,
                 j.sd, j.v, j.i * j.v, (unsigned)j.beat, (unsigned)j.lewat, (int)j.replay,
                 (int)sah[j.mode]);
    }
    f.close();
    berkas_akhir = nomor;
    const bool semua = !batal && !gagal && hasil_n == TANGGA_N;
    Serial.printf("tangga: %s -> %s\n", semua ? "SAH" : "TIDAK SAH", p);
}

void daya_tangga_tick(void)
{
    if (langkah < 0) return;
    if (mode_daya != langkah) { selesai("mode diubah dari luar tangga"); return; }
    if (jendela_langkah > DAYA_BLOK) {
        if (langkah < TANGGA_N - 1) mulai_langkah(langkah + 1);
        else selesai(nullptr);
    } else if (millis() - t_langkah > 2 * (DAYA_BLOK + 1) * JENDELA_DAYA_MS + 5000) {
        selesai("jendela tidak datang (INA219 tidak menjawab?)");
    }
}

static void daftar(void)
{
    File d = buka_dir();
    Serial.println("daya: berkas tangga");
    if (d && d.isDirectory())
        for (File f = d.openNextFile(); f; f = d.openNextFile())
            Serial.printf("  %3d  %5u B\n", atoi(f.name()), (unsigned)f.size());
    Serial.println("daya: akhir daftar");
}

bool daya_serial(const char *c)
{
    if (c[0] == 'V') { daya_tangga_mulai(); return true; }
    if (c[0] != 'v') return false;
    if (!c[1]) { daftar(); return true; }
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
