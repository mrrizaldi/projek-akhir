// Gerbang kualitas sinyal. Kontrak: include/gerbang.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "gerbang.h"

#include <Arduino.h>

#include "akuisisi.h"
#include "perangkat.h"
#include "rekam.h"
#include "tampilan.h"

constexpr int ADC_ATAS = 4090, ADC_BAWAH = 5;

// KALIBRASI -> BAIK: butuh TIGA hal sekaligus — elektroda sudah stabil (waktu),
// RR masuk rentang fisiologis dan tenang (30 detik), dan ayunan cukup. Selama
// KALIBRASI inferensi TIDAK dijalankan dan tidak ada yang dipublikasikan.
//
// PENTING: kriteria RR di bawah adalah gerbang MASUK, bukan gerbang per detak.
// Setelah fase pemantauan dimulai, dRR TIDAK lagi dibatasi — beat ventrikular
// memang datang dengan dRR besar, jadi menegakkan dRR <= 200 ms terus-menerus
// akan membungkam justru aritmia yang ingin dideteksi. bab3.tex juga
// menuliskannya sebagai syarat "layak untuk fase pemantauan", sekali saja.
// STABIL_MS (bab3: 10-15 menit; ambil 10) dan RR_TENANG_MS (bab3: >= 30 detik)
// ada di gerbang.h untuk halaman status kalibrasi.
constexpr float RR_MIN_S = 0.300f, RR_MAKS_S = 1.500f;   // bab3: 300-1500 ms
constexpr float DRR_MAKS_S = 0.200f;                     // bab3: <= 200 ms
constexpr uint32_t BIP_KALIB_MS = 600;     // tanda kalibrasi mulai & selesai

static int fase;
static uint32_t t_rr_langgar;      // millis() pelanggaran RR terakhir
// millis() saat sesi ecg_live dimulai. Dipakai mengubah indeks sampel jadi waktu
// dinding, lihat klasifikasi.cpp publikasi().
static uint32_t t_sesi_ms;
// Override manual gerbang masuk (waktu stabilisasi DAN kriteria RR) untuk bench,
// toggle 'k'. Mematikannya memulai sesi baru sehingga gerbang penuh berlaku lagi.
//
// Replay melewati gerbang yang sama, tetapi lewat kondisi replay di
// gerbang_nilai_fase(), bukan lewat flag ini: bypass-nya melekat pada sumber
// sinyal dan berhenti bersama replay. golden_raw adalah record 208 yang penuh
// beat ventrikular (dRR terukur -0,364 / +0,478 s), jadi kriteria "dRR <= 200 ms
// konsisten 30 detik", yang dirancang untuk subjek sehat yang duduk diam, tidak
// akan pernah lulus.
static bool lewati_kalibrasi;
static bool lapor_kualitas;                // toggle 'q': cetak tiap detik
static gerbang_kualitas_t q;

// Bandpass 0,5-40 Hz TIDAK membunuh 50 Hz, cuma meredamnya -9,3 dB (diukur dari
// ecg_sos dengan sosfreqz). Jadi dengung jala-jala tetap masuk hitungan ayunan
// dan bisa memalsukan LED hijau. Kontribusinya diukur dengan Goertzel lalu
// dikurangkan. 50 Hz x 1 detik = 50 siklus bulat, jadi binnya tepat.
constexpr float GAIN_50HZ = 0.342f;

const gerbang_kualitas_t &gerbang_kualitas(void) { return q; }
uint32_t gerbang_t_sesi_ms(void) { return t_sesi_ms; }
uint32_t gerbang_tenang_ms(void) { return millis() - t_rr_langgar; }
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
    t_rr_langgar = millis();       // hitungan 30 detik mulai dari nol
    tampilan_hapus_jadwal();       // jam sampel ecg_live mulai dari nol lagi
}

void gerbang_set_lewati(bool on)
{
    if (rekam_tolak("lewati kalibrasi")) return;
    lewati_kalibrasi = on;
    if (!on) gerbang_mulai_sesi();         // gerbang penuh dari nol
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

    const bool ayun_ok = q.ayun_bersih >= AMBANG_AYUN;
    const bool replay = akuisisi_replay();

    if (fase == FASE_KALIBRASI) {
        const bool stabil = millis() - t_sesi_ms >= STABIL_MS;
        const bool rr_tenang = millis() - t_rr_langgar >= RR_TENANG_MS;
        if ((lewati_kalibrasi || replay || (stabil && rr_tenang)) && ayun_ok) {
            fase = FASE_BAIK;
            tampilan_bunyi(BIP_KALIB_MS);
            Serial.printf("kualitas: calibrating -> good (%s, RR tenang %lu s, ayun %d)\n",
                          replay ? "GERBANG DILEWATI (replay)"
                          : lewati_kalibrasi ? "GERBANG DILEWATI (bench)" : "gerbang penuh",
                          (unsigned long)((millis() - t_rr_langgar) / 1000), q.ayun_bersih);
        }
        return;                    // masih kalibrasi: tidak ada inferensi
    }
    // Sesudah fase pemantauan dimulai, yang menggerbangi cuma ayunan sinyal.
    fase = ayun_ok ? FASE_BAIK : FASE_BURUK;
}

// bab3.tex: "inferensi CNN belum dijalankan" selama calibrating. Detektor tetap
// jalan — RR-nya justru yang dipakai menilai kelayakan sinyal.
void gerbang_lapor_kalibrasi(const ecg_beat_t &beat)
{
    static uint32_t t_lapor;
    if (millis() - t_lapor <= 5000) return;
    t_lapor = millis();
    Serial.printf("calibrating | RR=%.3fs dRR=%+.3fs | tenang %lu/%lu s | "
                  "ayun %d (ambang %d) | stabil %lu/%lu s | lewati=%d replay=%d\n",
                  beat.rr[0], beat.rr[2],
                  (unsigned long)((millis() - t_rr_langgar) / 1000),
                  (unsigned long)(RR_TENANG_MS / 1000), q.ayun_bersih, AMBANG_AYUN,
                  (unsigned long)((millis() - t_sesi_ms) / 1000),
                  (unsigned long)(STABIL_MS / 1000), (int)lewati_kalibrasi,
                  (int)akuisisi_replay());
}

// Ayunan diukur pada sinyal SETELAH bandpass 0,5-40 Hz, bukan ADC mentah:
// dengung 50 Hz ada di luar pita, jadi kabel yang dipenuhi jala-jala tidak
// lagi terbaca "kuat". Clipping tetap dinilai dari ADC mentah — begitu
// terpotong di rail, informasinya sudah hilang sebelum filter.
void gerbang_nilai_kualitas(float mentah)
{
    static size_t n;
    static float f_min, f_maks;
    static int m_min, m_maks;

    static float g1, g2;
    static const float koef = 2.0f * cosf(2.0f * (float)M_PI * 50.0f / ECG_FS);

    const float f = ecg_live_tersaring_terakhir();
    const int m = (int)mentah;
    if (n == 0) { f_min = f_maks = f; m_min = m_maks = m; g1 = g2 = 0.0f; }

    const float g0 = koef * g1 - g2 + mentah;   // Goertzel bin 50 Hz
    g2 = g1; g1 = g0;

    if (f < f_min) f_min = f;
    if (f > f_maks) f_maks = f;
    if (m < m_min) m_min = m;
    if (m > m_maks) m_maks = m;

    if (++n < ECG_FS) return;              // satu jendela = 1 detik
    n = 0;
    q.ayun = (int)(f_maks - f_min);
    // Amplitudo puncak 50 Hz -> puncak-ke-puncak -> porsinya yang lolos filter.
    const float amp50 = 2.0f * sqrtf(fmaxf(g1 * g1 + g2 * g2 - koef * g1 * g2, 0.0f)) / ECG_FS;
    q.hum50 = (int)(2.0f * amp50);
    q.ayun_bersih = (int)fmaxf(q.ayun - GAIN_50HZ * 2.0f * amp50, 0.0f);
    q.mentah_min = m_min;
    q.mentah_maks = m_maks;
    q.clipping = (m_maks >= ADC_ATAS || m_min <= ADC_BAWAH);
    if (lapor_kualitas)
        Serial.printf("kualitas | mentah %4d..%4d | ayun %4d - dengung50 %4d = "
                      "BERSIH %4d (ambang %d) | clipping %d | LO %d %d\n",
                      q.mentah_min, q.mentah_maks, q.ayun, q.hum50,
                      q.ayun_bersih, AMBANG_AYUN,
                      (int)q.clipping, digitalRead(PIN_LOP), digitalRead(PIN_LON));
}
#endif
