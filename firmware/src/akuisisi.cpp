// Akuisisi sampel. Kontrak: include/akuisisi.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "akuisisi.h"

#include <Arduino.h>
#include "driver/adc.h"

#include "gerbang.h"
#include "klasifikasi.h"
#include "konfig.h"
#include "perangkat.h"
#include "rekam.h"
#include "golden_ref.h"

static volatile uint16_t antre[ANTRE_N];
static volatile size_t tulis, baca;
static volatile uint32_t n_lewat;          // antrean penuh = sampel hilang
static hw_timer_t *timer;

// Sumber sinyal replay: golden_raw (record 208, 2400 sampel, 9 beat)
// diputar berulang menggantikan ADC. Tanpa sinyal, ecg_live_push tidak pernah
// mengeluarkan beat — jadi replay bukan kemudahan, tapi syarat untuk mengukur
// daya per mode (HW-7) dan untuk menguji jalur MQTT tanpa elektroda.
//
// Jumlah beat yang SEHARUSNYA keluar jadi diketahui persis, dan itulah yang
// membuat kehilangan data bisa diukur: beat hilang = seharusnya - sampai.
//
// Replay rekaman memakai jalur yang sama: berkas /rekam/NNN.csv dimuat ke PSRAM
// lalu diputar berulang. ISR cukup membaca array apa pun yang ditunjuk rp_data.
// PSRAM aman dibaca di ISR ini: timerAttachInterrupt memasangnya tanpa
// ESP_INTR_FLAG_IRAM, jadi ia ditahan selama flash ditulis (cache mati).
static int sumber, sumber_rekam;
static const uint16_t *volatile rp_data;   // NULL = ADC
static volatile size_t rp_n, replay_i;
static uint16_t *rekam_buf;                // PSRAM, dialokasikan saat pertama dipakai
static bool pasang(int s, int nomor);

// golden_raw satuannya mV (bisa negatif); antrean menyimpan counts ADC 12-bit.
// Skalanya bebas — bandpass membuang DC dan z-score membuang skala, jadi
// pipeline kebal terhadap pilihan ini. Yang TIDAK boleh: sampai terpotong di
// rail, karena clipping merusak morfologi. 1000 counts/mV menaruh puncak R
// (~1,5 mV) di ~3550, aman di bawah 4095.
constexpr float SKALA_REPLAY = 1000.0f;
constexpr float OFFSET_REPLAY = 2048.0f;

// Konversi dilakukan SEKALI di akuisisi_mulai(), bukan di ISR. ESP32 tidak
// menyimpan register FPU di konteks interrupt, jadi operasi float di on_timer()
// merusak state FPU task yang sedang diinterupsi. Gejalanya panic "Coprocessor
// exception" (EXCCAUSE 4) setelah ~18 detik, bukan crash seketika — cukup
// lambat untuk lolos uji 20 detik.
static uint16_t sim_counts[GOLDEN_N];

static void IRAM_ATTR on_timer()
{
    const size_t berikut = (tulis + 1) % ANTRE_N;
    if (berikut == baca) { n_lewat++; return; }        // loop ketinggalan
    if (rp_data) {
        antre[tulis] = rp_data[replay_i];          // INTEGER saja — lihat catatan
        if (++replay_i >= rp_n) replay_i = 0;
    } else {
        antre[tulis] = (uint16_t)adc1_get_raw(KANAL_EKG);   // cepat, aman di ISR
    }
    tulis = berikut;
}

void akuisisi_mulai(void)
{
    for (size_t i = 0; i < GOLDEN_N; i++) {        // WAJIB sebelum timer jalan: ISR cuma baca
        float v = golden_raw[i] * SKALA_REPLAY + OFFSET_REPLAY;
        if (v < 0.0f) v = 0.0f;
        if (v > 4095.0f) v = 4095.0f;
        sim_counts[i] = (uint16_t)v;
    }
    timer = timerBegin(0, 80, true);
    timerAttachInterrupt(timer, &on_timer, true);
    timerAlarmWrite(timer, 1000000 / ECG_FS, true);
    // Sumber tersimpan di NVS. Sesi kalibrasi sudah dimulai setup(), jadi
    // tidak perlu sesi baru; rekaman yang sudah dihapus jatuh ke ADC.
    if (!pasang(konfig_sumber(), konfig_sumber_rekam())) pasang(SUMBER_ADC, 0);
    timerAlarmEnable(timer);
}

bool akuisisi_ambil(uint16_t *sampel)
{
    if (baca == tulis) return false;
    *sampel = antre[baca];
    baca = (baca + 1) % ANTRE_N;
    return true;
}

size_t akuisisi_isi(void) { return (tulis - baca + ANTRE_N) % ANTRE_N; }
uint32_t akuisisi_lewat(void) { return n_lewat; }
void akuisisi_nol_lewat(void) { n_lewat = 0; }
bool akuisisi_replay(void) { return sumber != SUMBER_ADC; }
int akuisisi_sumber(void) { return sumber; }
int akuisisi_sumber_rekam(void) { return sumber_rekam; }

void akuisisi_timer(bool jalan)
{
    if (jalan) timerAlarmEnable(timer);
    else       timerAlarmDisable(timer);
}

// Dipanggil saat timer mati (atau sebelum timer pertama kali jalan).
static bool pasang(int s, int nomor)
{
    if (s == SUMBER_REKAM) {
        if (!rekam_buf) rekam_buf = (uint16_t *)ps_malloc(REKAM_SAMPEL_MAKS * sizeof(uint16_t));
        const size_t n = rekam_buf ? rekam_muat(nomor, rekam_buf, REKAM_SAMPEL_MAKS) : 0;
        if (n < ECG_FS) {                  // < 1 detik: tidak ada beat yang bisa keluar
            Serial.printf("replay rekaman %d GAGAL dimuat (%u sampel)\n", nomor, (unsigned)n);
            return false;
        }
        rp_n = n;
        rp_data = rekam_buf;
    } else if (s == SUMBER_ACUAN) {
        rp_n = GOLDEN_N;
        rp_data = sim_counts;
    } else {
        s = SUMBER_ADC;
        rp_data = nullptr;
    }
    replay_i = 0;
    sumber = s;
    sumber_rekam = s == SUMBER_REKAM ? nomor : 0;
    return true;
}

bool akuisisi_set_sumber(int s, int nomor, bool simpan)
{
    if (rekam_tolak("ganti sumber")) return false;
    akuisisi_timer(false);                 // memuat berkas memblok; jangan dihitung sampel hilang
    const bool ok = pasang(s, nomor);
    akuisisi_timer(true);
    if (!ok) return false;
    if (simpan) konfig_set_sumber(sumber, sumber_rekam);
    gerbang_mulai_sesi();
    klasifikasi_reset();
    if (sumber == SUMBER_REKAM)
        Serial.printf("replay ON (rekaman %03d, %u sampel)\n", sumber_rekam, (unsigned)rp_n);
    else
        Serial.printf("replay %s\n", sumber == SUMBER_ACUAN ? "ON (golden_raw)" : "OFF (ADC)");
    return true;
}

void akuisisi_ganti_sumber(void)
{
    akuisisi_set_sumber(sumber == SUMBER_ADC ? SUMBER_ACUAN : SUMBER_ADC, 0, true);
}
#endif
