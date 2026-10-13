// Akuisisi sampel. Kontrak: include/akuisisi.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "akuisisi.h"

#include <Arduino.h>
#include "driver/adc.h"

#include "gerbang.h"
#include "klasifikasi.h"
#include "perangkat.h"
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
static volatile bool replay;
static volatile size_t replay_i;

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
    if (replay) {
        antre[tulis] = sim_counts[replay_i];       // INTEGER saja — lihat catatan
        replay_i = (replay_i + 1) % GOLDEN_N;
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
bool akuisisi_replay(void) { return replay; }

void akuisisi_timer(bool jalan)
{
    if (jalan) timerAlarmEnable(timer);
    else       timerAlarmDisable(timer);
}

void akuisisi_ganti_sumber(void)
{
    replay = !replay;
    replay_i = 0;
    gerbang_mulai_sesi();
    klasifikasi_reset();
    Serial.printf("replay %s\n", replay ? "ON (golden_raw)" : "OFF (ADC)");
}
#endif
