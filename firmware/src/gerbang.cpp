#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "gerbang.h"

#include <Arduino.h>

#include "akuisisi.h"
#include "perangkat.h"
#include "rekam.h"
#include "tampilan.h"

constexpr int ADC_ATAS = 4090, ADC_BAWAH = 5;

constexpr float RR_MIN_S = 0.300f, RR_MAKS_S = 1.500f;
constexpr float DRR_MAKS_S = 0.200f;
constexpr uint32_t BIP_KALIB_MS = 600;

static int fase;
static uint32_t t_rr_langgar;
static uint32_t t_sesi_ms;
static uint32_t t_kontak;
static bool lewati_kalibrasi;
static bool lapor_kualitas;
static gerbang_kualitas_t q;

constexpr float GAIN_50HZ = 0.342f;
constexpr float FREK_JALA_HZ = 50.0f;

const gerbang_kualitas_t &gerbang_kualitas(void) { return q; }
uint32_t gerbang_t_sesi_ms(void) { return t_sesi_ms; }
uint32_t gerbang_tenang_ms(void) { return millis() - t_rr_langgar; }
uint32_t gerbang_kontak_ms(void) { return q.kontak ? millis() - t_kontak : 0; }
int gerbang_fase(void) { return fase; }
bool gerbang_lewati(void) { return lewati_kalibrasi; }
bool gerbang_lapor(void) { return lapor_kualitas; }
void gerbang_set_lapor(bool on) { lapor_kualitas = on; }

void gerbang_mulai_sesi(void)
{
    tampilan_bunyi(BIP_KALIB_MS);
    ecg_live_reset();
    t_sesi_ms = millis();
    fase = FASE_KALIBRASI;
    t_rr_langgar = millis();
    q.kontak = false;
    tampilan_hapus_jadwal();
}

void gerbang_set_lewati(bool on)
{
    if (rekam_tolak("lewati kalibrasi")) return;
    lewati_kalibrasi = on;
    if (!on) gerbang_mulai_sesi();
}

const char *gerbang_nama_fase(void)
{
    return fase == FASE_KALIBRASI ? "calibrating" : (fase == FASE_BAIK ? "good" : "poor");
}

void gerbang_nilai_fase(const ecg_beat_t &beat)
{
    const float rr = beat.rr[0];
    const float drr = fabsf(beat.rr[2]);
    const bool rr_wajar = rr >= RR_MIN_S && rr <= RR_MAKS_S && drr <= DRR_MAKS_S;
    if (!rr_wajar) t_rr_langgar = millis();

    const bool replay = akuisisi_replay();

    if (fase != FASE_KALIBRASI) return;
    const bool hangat = gerbang_kontak_ms() >= PEMANASAN_MS;
    const bool rr_tenang = millis() - t_rr_langgar >= RR_TENANG_MS;
    if ((lewati_kalibrasi || replay || (hangat && rr_tenang)) && q.kontak) {
        fase = FASE_BAIK;
        tampilan_bunyi(BIP_KALIB_MS);
        Serial.printf("kualitas: calibrating -> good (%s, kontak %lu s, RR tenang %lu s, ayun %d, dengung %d)\n",
                      replay ? "GERBANG DILEWATI (replay)"
                      : lewati_kalibrasi ? "GERBANG DILEWATI (bench)" : "gerbang penuh",
                      (unsigned long)(gerbang_kontak_ms() / 1000),
                      (unsigned long)((millis() - t_rr_langgar) / 1000), q.ayun_bersih, q.hum50);
    }
}

static void nilai_kontak(void)
{
    const bool baik = (akuisisi_replay() || !q.lepas) && q.ayun_bersih >= AMBANG_AYUN
                      && q.hum50 <= AMBANG_DENGUNG;
    if (baik && !q.kontak) t_kontak = millis();
    q.kontak = baik;
    if (fase == FASE_KALIBRASI) return;
    const int baru = baik ? FASE_BAIK : FASE_BURUK;
    if (baru != fase)
        Serial.printf("kualitas: %s -> %s (lepas %d, ayun %d, dengung %d)\n", gerbang_nama_fase(),
                      baik ? "good" : "poor", (int)q.lepas, q.ayun_bersih, q.hum50);
    fase = baru;
}

void gerbang_lapor_kalibrasi(const ecg_beat_t &beat)
{
    static uint32_t t_lapor;
    if (millis() - t_lapor <= 5000) return;
    t_lapor = millis();
    Serial.printf("calibrating | RR=%.3fs dRR=%+.3fs | tenang %lu/%lu s | "
                  "ayun %d (ambang %d) | dengung %d (ambang %d) | lepas %d | kontak %lu/%lu s | "
                  "lewati=%d replay=%d\n",
                  beat.rr[0], beat.rr[2],
                  (unsigned long)((millis() - t_rr_langgar) / 1000),
                  (unsigned long)(RR_TENANG_MS / 1000), q.ayun_bersih, AMBANG_AYUN,
                  q.hum50, AMBANG_DENGUNG, (int)q.lepas,
                  (unsigned long)(gerbang_kontak_ms() / 1000),
                  (unsigned long)(PEMANASAN_MS / 1000), (int)lewati_kalibrasi,
                  (int)akuisisi_replay());
}

void gerbang_nilai_kualitas(float mentah)
{
    static size_t n, n_lepas;
    static float f_min, f_maks;
    static int m_min, m_maks;

    static float g1, g2;
    static const float koef = 2.0f * cosf(2.0f * (float)M_PI * FREK_JALA_HZ / ECG_FS);

    const float f = ecg_live_tersaring_terakhir();
    const int m = (int)mentah;
    if (n == 0) { f_min = f_maks = f; m_min = m_maks = m; g1 = g2 = 0.0f; n_lepas = 0; }
    if (digitalRead(PIN_LOP) || digitalRead(PIN_LON)) n_lepas++;

    const float g0 = koef * g1 - g2 + mentah;
    g2 = g1; g1 = g0;

    if (f < f_min) f_min = f;
    if (f > f_maks) f_maks = f;
    if (m < m_min) m_min = m;
    if (m > m_maks) m_maks = m;

    if (++n < ECG_FS) return;
    n = 0;
    q.ayun = (int)(f_maks - f_min);
    const float amp50 = 2.0f * sqrtf(fmaxf(g1 * g1 + g2 * g2 - koef * g1 * g2, 0.0f)) / ECG_FS;
    q.hum50 = (int)(2.0f * amp50);
    q.ayun_bersih = (int)fmaxf(q.ayun - GAIN_50HZ * 2.0f * amp50, 0.0f);
    q.mentah_min = m_min;
    q.mentah_maks = m_maks;
    q.clipping = (m_maks >= ADC_ATAS || m_min <= ADC_BAWAH);
    q.lepas = n_lepas > 0;
    nilai_kontak();
    if (lapor_kualitas)
        Serial.printf("kualitas | mentah %4d..%4d | ayun %4d - dengung50 %4d = "
                      "BERSIH %4d (ambang %d) | clipping %d | LO %d %d\n",
                      q.mentah_min, q.mentah_maks, q.ayun, q.hum50,
                      q.ayun_bersih, AMBANG_AYUN,
                      (int)q.clipping, digitalRead(PIN_LOP), digitalRead(PIN_LON));
}
#endif
