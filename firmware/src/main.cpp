// Firmware utama: akuisisi + klasifikasi aritmia langsung di alat, dengan
// tampilan TFT (HR, gelombang, status, daya INA219), bip buzzer per detak, dan
// tiga tombol. Pin map PCB rev1 ada di include/perangkat.h.
//
// ADC dibaca di timer ISR 360 Hz dan ditaruh ke antrean; loop utama yang
// menguras dan memproses. Pemisahan ini WAJIB: beban pemrosesan menggumpal —
// rata-rata 82 us/sampel tapi puncaknya 33 ms saat deteksi dan inferensi
// bersamaan. Kalau ADC dibaca di loop, ~12 sampel hilang tiap detik dan
// interval RR rusak (docs/firmware-walkthrough.md §5b).
#ifndef PIO_UNIT_TESTING
#include <Arduino.h>
#include <LittleFS.h>
#include <string.h>
#include "driver/adc.h"
#include <WiFi.h>
#include "esp_wifi.h"

#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#if __has_include("tensorflow/lite/micro/micro_error_reporter.h")
#include "tensorflow/lite/micro/micro_error_reporter.h"
#define TFLM_PUNYA_ERROR_REPORTER 1
#endif

#include "ecg_live.h"
#include "ecg_mqtt.h"
#include "ina219.h"
#include "perangkat.h"
#include "model_int8.h"
#include "golden_ref.h"

constexpr size_t ANTRE_N = 256;            // >= 13 (puncak burst), dibulatkan pangkat 2
constexpr uint32_t DETIK_MAKS = 300;
constexpr size_t REKAM_N = (size_t)ECG_FS * DETIK_MAKS;
constexpr const char *BERKAS = "/rekaman.csv";
constexpr int ARENA_N = 24 * 1024;

// Ambang kualitas sinyal, dari akuisisi-walkthrough.md §2 (angka empiris, bukan
// tebakan: kontak segar 691 counts, elektroda dipakai ulang 195).
constexpr int AMBANG_AYUN = 60;            // ayunan TERSARING 1 detik, counts ADC
constexpr int ADC_ATAS = 4090, ADC_BAWAH = 5;

// Fase kualitas sinyal, bab3.tex §Pengujian Pipeline tahap 1-2.
//
// KALIBRASI -> BAIK: butuh TIGA hal sekaligus — elektroda sudah stabil (waktu),
// RR masuk rentang fisiologis dan tenang (30 detik), dan ayunan cukup. Selama
// KALIBRASI inferensi TIDAK dijalankan dan tidak ada yang dipublikasikan.
//
// PENTING: kriteria RR di bawah adalah gerbang MASUK, bukan gerbang per detak.
// Setelah fase pemantauan dimulai, dRR TIDAK lagi dibatasi — beat ventrikular
// memang datang dengan dRR besar, jadi menegakkan dRR <= 200 ms terus-menerus
// akan membungkam justru aritmia yang ingin dideteksi. bab3.tex juga
// menuliskannya sebagai syarat "layak untuk fase pemantauan", sekali saja.
constexpr uint32_t STABIL_MS = 10UL * 60 * 1000;   // bab3: 10-15 menit; ambil 10
constexpr uint32_t RR_TENANG_MS = 30UL * 1000;     // bab3: >= 30 detik
constexpr float RR_MIN_S = 0.300f, RR_MAKS_S = 1.500f;   // bab3: 300-1500 ms
constexpr float DRR_MAKS_S = 0.200f;                     // bab3: <= 200 ms

enum { FASE_KALIBRASI, FASE_BAIK, FASE_BURUK };
static int fase;
static uint32_t t_rr_langgar;      // millis() pelanggaran RR terakhir
// Override manual gerbang masuk (waktu stabilisasi DAN kriteria RR) untuk bench,
// toggle 'k'. Mematikannya memulai sesi baru sehingga gerbang penuh berlaku lagi.
//
// Replay melewati gerbang yang sama, tetapi lewat kondisi `replay` di
// nilai_fase(), bukan lewat flag ini: bypass-nya melekat pada sumber sinyal dan
// berhenti bersama replay. golden_raw adalah record 208 yang penuh beat
// ventrikular (dRR terukur -0,364 / +0,478 s), jadi kriteria "dRR <= 200 ms
// konsisten 30 detik", yang dirancang untuk subjek sehat yang duduk diam, tidak
// akan pernah lulus.
static bool lewati_kalibrasi;

// Bandpass 0,5-40 Hz TIDAK membunuh 50 Hz, cuma meredamnya -9,3 dB (diukur dari
// ecg_sos dengan sosfreqz). Jadi dengung jala-jala tetap masuk hitungan ayunan
// dan bisa memalsukan LED hijau. Kontribusinya diukur dengan Goertzel lalu
// dikurangkan. 50 Hz x 1 detik = 50 siklus bulat, jadi binnya tepat.
constexpr float GAIN_50HZ = 0.342f;

static volatile uint16_t antre[ANTRE_N];
static volatile size_t tulis, baca;
static volatile uint32_t n_lewat;          // antrean penuh = sampel hilang
static hw_timer_t *timer;

static uint16_t *rekam_buf;
static volatile size_t rekam_n;
static volatile bool rekam;
static size_t rekam_lepas;                 // sampel dgn LO aktif selama merekam

alignas(16) static uint8_t arena[ARENA_N];
static tflite::MicroInterpreter *interp;
static TfLiteTensor *in_morph, *in_rr, *keluar;

static int beat_total, beat_aritmia;
static int beat_ditahan;   // tidak dipublikasi: kualitas sinyal / beat timeout
// millis() saat sesi ecg_live dimulai. Dipakai mengubah indeks sampel jadi waktu
// dinding, lihat publikasi().
static uint32_t t_sesi_ms;
// Tunda SISI ALAT: dari saat beat TERJADI sampai paketnya ditulis ke socket.
// Dipakai memecah latensi end-to-end jadi "milik alat" vs "milik jaringan+cloud",
// supaya target 2 detik bab3.tex bisa dibebankan ke penyebab yang benar.
static uint32_t tunda_jml, tunda_n, tunda_maks;

// Kualitas sinyal 1 detik terakhir (dipakai LED + laporan serial).
static int ayun_1s, ayun_bersih_1s, hum50_1s, mentah_min_1s, mentah_maks_1s;
static bool clipping_1s;
static bool lapor_kualitas;                // toggle 'q': cetak tiap detik

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

// Konversi dilakukan SEKALI di setup(), bukan di ISR. ESP32 tidak menyimpan
// register FPU di konteks interrupt, jadi operasi float di on_timer() merusak
// state FPU task yang sedang diinterupsi. Gejalanya panic "Coprocessor
// exception" (EXCCAUSE 4) setelah ~18 detik, bukan crash seketika — cukup
// lambat untuk lolos uji 20 detik.
static uint16_t sim_counts[GOLDEN_N];

// Tangga ukur daya (docs/arsip/2026-09-16-daya-design.md §1), perintah serial
// 'p0'..'p5'; 'p' + huruf lain kembali ke operasi normal (-1). Tiap anak tangga
// menambah satu beban; ongkos satu tahap = selisih dua anak tangga.
//   p0 timer ISR mati          p3 + inferensi CNN
//   p1 + ISR 360 Hz & kuras    p4 + UI: gelombang TFT, bip, LED
//   p2 + ecg_live (DSP)        p5 + radio WiFi & MQTT (= operasi normal)
// Radio WiFi mati di p0-p4. Teks TFT 1 Hz, tombol, dan pembacaan INA219 jalan di
// semua anak tangga, sehingga ongkosnya hilang di selisih.
static int mode_daya = -1;
constexpr uint32_t JENDELA_DAYA_MS = 10000;
static uint32_t beat_dsp;          // beat keluar dari ecg_live, termasuk saat kalibrasi

void IRAM_ATTR on_timer()
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

static void led(uint8_t r, uint8_t g, uint8_t b) { neopixelWrite(PIN_LED, r, g, b); }

static void siapkan_replay()
{
    for (size_t i = 0; i < GOLDEN_N; i++) {
        float v = golden_raw[i] * SKALA_REPLAY + OFFSET_REPLAY;
        if (v < 0.0f) v = 0.0f;
        if (v > 4095.0f) v = 4095.0f;
        sim_counts[i] = (uint16_t)v;
    }
}

static void siapkan_model()
{
    const tflite::Model *m = tflite::GetModel(model_int8_tflite);
    static tflite::MicroMutableOpResolver<8> res;
    res.AddConv2D(); res.AddDepthwiseConv2D(); res.AddMaxPool2D();
    res.AddConcatenation(); res.AddLogistic(); res.AddAdd();
    res.AddReshape(); res.AddExpandDims();
#ifdef TFLM_PUNYA_ERROR_REPORTER
    static tflite::MicroErrorReporter lapor;
    static tflite::MicroInterpreter it(m, res, arena, ARENA_N, &lapor);
#else
    static tflite::MicroInterpreter it(m, res, arena, ARENA_N);
#endif
    interp = &it;
    if (interp->AllocateTensors() != kTfLiteOk) {
        Serial.println("FATAL: AllocateTensors gagal");
        while (true) { led(64, 0, 0); delay(200); led(0, 0, 0); delay(200); }
    }
    TfLiteTensor *a = interp->input(0), *b = interp->input(1);
    const bool a_kecil = a->bytes < b->bytes;
    in_rr = a_kecil ? a : b;
    in_morph = a_kecil ? b : a;
    keluar = interp->output(0);
}

static int8_t ke_int8(float x, float skala, int nol)
{
    long q = lroundf(x / skala) + nol;
    if (q < -128) q = -128;
    if (q > 127) q = 127;
    return (int8_t)q;
}

static float klasifikasi(const ecg_beat_t &beat)
{
    for (int i = 0; i < ECG_WIN_LEN_; i++)
        in_morph->data.int8[i] = ke_int8(beat.window[i], ECG_IN_MORPH_SCALE, ECG_IN_MORPH_ZERO);
    for (int i = 0; i < ECG_N_RR; i++)
        in_rr->data.int8[i] = ke_int8(beat.rr[i], ECG_IN_RR_SCALE, ECG_IN_RR_ZERO);
    interp->Invoke();
    return (keluar->data.int8[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;
}

// Menyusun satu record telemetri dan menaruhnya ke antrean MQTT.
//
// GERBANG KUALITAS, bukan gerbang beat. Tanpa elektroda, ambang adaptif
// Pan-Tompkins tetap menemukan puncak di derau 15 counts: alat mengarang ~2
// beat/detik dengan 57% "ARITMIA". Kalau publikasi digerbangi ada-tidaknya
// beat, elektroda lepas = banjir alarm palsu ke broker. Yang menggerbangi
// harus ayunan sinyal (akuisisi-walkthrough.md §2).
//
// Replay TIDAK diperlakukan khusus dan memang tidak perlu: ayunannya ~2700
// counts, jauh di atas AMBANG_AYUN 60, jadi ia lolos gerbang yang sama persis
// dengan sinyal tubuh. Satu jalur kode untuk dummy dan nyata.
static void bunyi(uint32_t ms);
constexpr uint32_t BIP_KALIB_MS = 600;     // tanda kalibrasi mulai & selesai

static void mulai_sesi()
{
    bunyi(BIP_KALIB_MS);
    ecg_live_reset();
    t_sesi_ms = millis();
    fase = FASE_KALIBRASI;
    t_rr_langgar = millis();       // hitungan 30 detik mulai dari nol
}

static const char *nama_fase()
{
    return fase == FASE_KALIBRASI ? "calibrating" : (fase == FASE_BAIK ? "good" : "poor");
}

// Dipanggil tiap beat, SEBELUM keputusan inferensi. Menilai kelayakan RR dan
// memindahkan fase kalau syaratnya sudah lengkap.
static void nilai_fase(const ecg_beat_t &beat)
{
    const float rr = beat.rr[0];
    const float drr = fabsf(beat.rr[2]);
    const bool rr_wajar = rr >= RR_MIN_S && rr <= RR_MAKS_S && drr <= DRR_MAKS_S;
    if (!rr_wajar) t_rr_langgar = millis();

    const bool ayun_ok = ayun_bersih_1s >= AMBANG_AYUN;

    if (fase == FASE_KALIBRASI) {
        const bool stabil = millis() - t_sesi_ms >= STABIL_MS;
        const bool rr_tenang = millis() - t_rr_langgar >= RR_TENANG_MS;
        if ((lewati_kalibrasi || replay || (stabil && rr_tenang)) && ayun_ok) {
            fase = FASE_BAIK;
            bunyi(BIP_KALIB_MS);
            Serial.printf("kualitas: calibrating -> good (%s, RR tenang %lu s, ayun %d)\n",
                          replay ? "GERBANG DILEWATI (replay)"
                          : lewati_kalibrasi ? "GERBANG DILEWATI (bench)" : "gerbang penuh",
                          (unsigned long)((millis() - t_rr_langgar) / 1000), ayun_bersih_1s);
        }
        return;                    // masih kalibrasi: tidak ada inferensi
    }
    // Sesudah fase pemantauan dimulai, yang menggerbangi cuma ayunan sinyal.
    fase = ayun_ok ? FASE_BAIK : FASE_BURUK;
}

static void publikasi(const ecg_beat_t &beat, float p, bool aritmia)
{
    if (!ecg_mqtt_aktif()) return;
    if (fase != FASE_BAIK) { beat_ditahan++; return; }
    if (beat.sinyal_hilang) { beat_ditahan++; return; }   // beat timeout, RR+1 sentinel

    ecg_mqtt_beat_t t;
    // Waktu KEJADIAN beat, dihitung dari indeks sampelnya — bukan millis() saat
    // beat dikeluarkan. Deteksi jalan tiap 1 detik atas ring 4 detik, jadi
    // beberapa beat keluar bergerombol dalam milidetik yang sama; memakai
    // millis() membuat dashboard menampilkan denyut yang berdesakan lalu
    // menganggur. Terukur di board 19 Sep: jeda antar-ts minimum 28 ms padahal
    // RR terpendek ~200 ms.
    //
    // Sampel yang HILANG (antrean penuh) membuat hitungan ini menyimpang dari
    // jam dinding sebesar durasi yang hilang. Itu sebabnya `sampel hilang` ikut
    // dilaporkan di baris 's': kalau ia tidak nol, ts ikut meleset.
    t.ms = t_sesi_ms + (uint32_t)((uint64_t)beat.r_abs * 1000ULL / ECG_FS);
    t.rr_ms = beat.rr[0] * 1000.0f;
    t.bpm = (beat.rr[0] > 0.05f) ? 60.0f / beat.rr[0] : 0.0f;
    t.label = aritmia ? 1 : 0;
    // Keyakinan pada KEPUTUSAN, bukan p mentah: p=0,02 untuk "normal" itu
    // keyakinan 0,98. Dashboard menampilkannya apa adanya, jadi angka mentah
    // akan terbaca "alat ragu" persis saat ia paling yakin.
    t.confidence = aritmia ? p : 1.0f - p;
    t.quality_ok = 1;                  // fase sudah dipastikan FASE_BAIK di atas
    // Snippet: window z-score dicuplik merata dan dikali 1000 supaya muat di
    // int16 tanpa float di payload. ponytail: cuplikan merata, bukan di sekitar
    // R — kalau widget butuh QRS yang terpusat, ambil ECG_SNIPPET_N titik mulai
    // dari ECG_WIN_PRE.
    for (int i = 0; i < ECG_SNIPPET_N; i++) {
        const int j = i * (ECG_WIN_LEN_ - 1) / (ECG_SNIPPET_N - 1);
        t.snippet[i] = (int16_t)(beat.window[j] * 1000.0f);
    }
    const uint32_t tunda = millis() - t.ms;
    tunda_jml += tunda; tunda_n++;
    if (tunda > tunda_maks) tunda_maks = tunda;

    ecg_mqtt_antre_isi(&t);
}

static void simpan()
{
    rekam = false;
    buzzer(false);       // menulis berkas memblok loop beberapa detik; bip jangan ikut tertahan
    File f = LittleFS.open(BERKAS, "w");
    if (!f) { Serial.println("GAGAL membuka LittleFS"); return; }
    // 'lepas' menjawab yang tidak bisa dijawab data mentah: apakah elektroda
    // benar-benar menempel saat rekaman dibuat? AD8232 memarkir output di
    // mid-rail saat leads-off, dan garis datar itu menyamar sebagai "sinyal
    // tenang" di CSV.
    f.printf("# fs=%u n=%u lewat=%u lepas=%u (%.0f%%)\n", ECG_FS, (unsigned)rekam_n,
             (unsigned)n_lewat, (unsigned)rekam_lepas,
             rekam_n ? 100.0f * rekam_lepas / rekam_n : 0.0f);
    for (size_t i = 0; i < rekam_n; i++) f.printf("%u\n", rekam_buf[i]);
    f.close();
    Serial.printf("SIMPAN %u sampel (%.1f detik), %u terlewat, elektroda lepas %.0f%% -> %s\n",
                  (unsigned)rekam_n, (float)rekam_n / ECG_FS, (unsigned)n_lewat,
                  rekam_n ? 100.0f * rekam_lepas / rekam_n : 0.0f, BERKAS);
    if (rekam_lepas > rekam_n / 10)
        Serial.println("PERINGATAN: elektroda lepas >10% — rekaman ini kemungkinan besar kosong.");
}

static void dump()
{
    File f = LittleFS.open(BERKAS, "r");
    if (!f) { Serial.println("Belum ada rekaman."); return; }
    Serial.println("---MULAI---");
    while (f.available()) Serial.write(f.read());
    Serial.println("---SELESAI---");
    f.close();
}

// Menilai kualitas sinyal tiap 1 detik, lalu menyetir LED.
//
// Ayunan diukur pada sinyal SETELAH bandpass 0,5-40 Hz, bukan ADC mentah:
// dengung 50 Hz ada di luar pita, jadi kabel yang dipenuhi jala-jala tidak
// lagi terbaca "kuat". Clipping tetap dinilai dari ADC mentah — begitu
// terpotong di rail, informasinya sudah hilang sebelum filter.
static void nilai_kualitas(float mentah)
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
    ayun_1s = (int)(f_maks - f_min);
    // Amplitudo puncak 50 Hz -> puncak-ke-puncak -> porsinya yang lolos filter.
    const float amp50 = 2.0f * sqrtf(fmaxf(g1 * g1 + g2 * g2 - koef * g1 * g2, 0.0f)) / ECG_FS;
    hum50_1s = (int)(2.0f * amp50);
    ayun_bersih_1s = (int)fmaxf(ayun_1s - GAIN_50HZ * 2.0f * amp50, 0.0f);
    mentah_min_1s = m_min;
    mentah_maks_1s = m_maks;
    clipping_1s = (m_maks >= ADC_ATAS || m_min <= ADC_BAWAH);
    if (lapor_kualitas)
        Serial.printf("kualitas | mentah %4d..%4d | ayun %4d - dengung50 %4d = "
                      "BERSIH %4d (ambang %d) | clipping %d | LO %d %d\n",
                      mentah_min_1s, mentah_maks_1s, ayun_1s, hum50_1s,
                      ayun_bersih_1s, AMBANG_AYUN,
                      (int)clipping_1s, digitalRead(PIN_LOP), digitalRead(PIN_LON));
}

// Arti LED (akuisisi-walkthrough.md §2):
//   merah  : sedang merekam — HANYA itu, tidak ada arti lain
//   oranye : ayunan BERSIH < ambang — kontak kurang / dengung dominan
//   hijau  : ayunan sehat, siap rekam
// Tiga keadaan, tanpa kedip. Clipping sengaja tidak punya pola LED sendiri:
// pola tambahan menumpuk arti di satu warna dan membuat merah ambigu. Clipping
// tetap dihitung dan dilaporkan lewat serial ('q' tiap detik, 's' sesaat);
// sinyal terpotong tampil HIJAU.
// LO+/LO- SENGAJA tidak dipakai menyetir LED: ia hanya melaporkan elektroda
// lepas total, dan pada 3-lead tanpa RL yang rapat ia menyala terus walau
// sinyalnya sebenarnya bagus. Ayunan mengukur yang benar-benar kita butuhkan.
static void perbarui_led()
{
    static uint32_t t_led = 0;

    if (millis() - t_led < 250) return;    // neopixelWrite matikan interrupt ~30 us
    t_led = millis();

    if (mode_daya >= 0 && mode_daya < 4)  led(0, 0, 0);      // LED ikut diukur di p4
    else if (rekam)                        led(64, 0, 0);
    else if (fase == FASE_KALIBRASI)       led(0, 16, 64);   // biru: stabilisasi
    else if (ayun_bersih_1s < AMBANG_AYUN) led(64, 24, 0);
    else                                   led(0, 48, 0);
}

// ---------------------------------------------------------------------------
// Antarmuka alat: TFT, buzzer, tombol.
//
// Layar landscape 320x172:
//   atas   HR (merah bila detak terakhir ARITMIA), arus/tegangan INA219,
//          status (REC detik / REPLAY / fase kualitas)
//   tengah gelombang EKG tersaring 0,5-40 Hz, skala otomatis per sapuan
//   bawah  tiga kotak tombol, kuning selama ditekan
// Tombol: B1 bisu/bunyi bip detak (tahan 2 detik = ganti sumber seperti 'y'),
//         B2 bekukan gelombang + bip, B3 mulai/simpan rekaman (seperti 'r').
// Bip detak senyap selama kalibrasi; bunyi panjang BIP_KALIB_MS menandai
// kalibrasi mulai (boot, ganti sumber, 'k' OFF) dan selesai (masuk fase BAIK).
constexpr int GY = 30, GH = 112;           // area gelombang
constexpr int DESIMASI = 3;                // 120 px/detik -> 320 px = 2,7 detik
constexpr uint16_t ABU = 0x4208;
constexpr uint32_t BIP_MS = 50, BIP_ARITMIA_MS = 250, TAHAN_MS = 2000;
// Tanpa detak selama ini, HR di layar menjadi "--".
constexpr uint32_t HR_BASI_MS = 3000;

static bool bisu, beku, ina_ada;
static bool tekan[3];
static int hr_tampil;                      // bpm, 0 = belum ada
static bool hr_aritmia;
static uint32_t t_hr;
static uint32_t buzz_sampai;

static void bunyi(uint32_t ms)
{
    buzzer(true);
    buzz_sampai = millis() + ms;
}

// Bip per detak, SINKRON dengan ritme. Beat keluar dari ecg_live bergerombol
// tiap ECG_LIVE_TIAP sampel; membunyikannya saat keluar membuat dua detak lebur
// jadi satu bip. Karena itu bip dijadwalkan di r_abs + TUNDA_BIP pada jam
// sampel yang sama dengan ecg_live: semua bip telat sama rata (1,46 detik),
// jarak antar-bip = RR persis. TUNDA = kadens deteksi + post-window (telat
// terburuk sebuah beat keluar) + 0,1 detik margin.
constexpr uint32_t TUNDA_BIP = ECG_LIVE_TIAP + ECG_WIN_POST + ECG_FS / 10;
constexpr int JADWAL_N = 8;                // 250 bpm x 1,46 detik = 6 bip menunggu
static struct { uint32_t sampel; uint16_t ms; } jadwal[JADWAL_N];
static int j_kepala, j_isi;

static void jadwalkan_bip(const ecg_beat_t &b, bool aritmia)
{
    if (bisu || j_isi == JADWAL_N) return;
    auto &j = jadwal[(j_kepala + j_isi++) % JADWAL_N];
    j.sampel = (uint32_t)b.r_abs + TUNDA_BIP;
    j.ms = aritmia ? BIP_ARITMIA_MS : BIP_MS;
}

// ponytail: jam = sampel yang sudah diproses ecg_live, bukan yang masuk antrean;
// saat burst deteksi bip telat paling lama sepanjang burst (~33 ms).
static void jalankan_jadwal()
{
    const uint32_t kini = (uint32_t)ecg_live_total_sampel();
    while (j_isi && (int32_t)(kini - jadwal[j_kepala].sampel) >= 0) {
        const uint16_t ms = jadwal[j_kepala].ms;
        j_kepala = (j_kepala + 1) % JADWAL_N;
        j_isi--;
        // Beku dicek saat berbunyi: layar juga ditunda TUNDA_BIP, jadi bip
        // berhenti tepat di R terakhir yang tergambar.
        if (!beku) bunyi(ms);
    }
}

// Gelombang di layar ikut ditunda TUNDA_BIP: R tergambar tepat saat bipnya
// berbunyi.
static float tunda_plot[TUNDA_BIP];
static size_t i_plot;

static float tertunda(float f)
{
    const float lama = tunda_plot[i_plot];
    tunda_plot[i_plot] = f;
    i_plot = (i_plot + 1) % TUNDA_BIP;
    return lama;
}

static void plot(float f)
{
    static int n, x, y_lalu = GY + GH / 2;
    static float lo = -300, hi = 300, mn = 1e9f, mx = -1e9f;

    mn = fminf(mn, f);
    mx = fmaxf(mx, f);
    if (++n < DESIMASI || beku) return;
    n = 0;

    int y = GY + GH - 1 - (int)((f - lo) * (GH - 1) / (hi - lo));
    y = constrain(y, GY, GY + GH - 1);
    tft.fillRect(x, GY, min(4, TFT_W - x), GH, ST77XX_BLACK); // hapus di depan kursor
    tft.drawFastVLine(x, min(y, y_lalu), abs(y - y_lalu) + 1, ST77XX_GREEN);
    y_lalu = y;

    if (++x < TFT_W) return;
    x = 0;                                 // akhir sapuan: skala ulang dari sapuan ini
    const float span = fmaxf(mx - mn, 50.0f);
    lo = mn - 0.1f * span;
    hi = lo + 1.2f * span;
    mn = 1e9f;
    mx = -1e9f;
}

static void mulai_rekam()
{
    rekam_n = rekam_lepas = n_lewat = 0;
    rekam = true;
    Serial.println("REKAM mulai");
}

// Sumber sinyal ADC <-> replay golden_raw. Dipakai serial 'y' dan B1 tahan 2 detik.
static void ganti_replay()
{
    replay = !replay;
    replay_i = 0;
    mulai_sesi();
    j_isi = 0;                     // jam sampel ecg_live mulai dari nol lagi
    beat_total = beat_aritmia = beat_ditahan = 0;
    tunda_jml = tunda_n = tunda_maks = 0;
    Serial.printf("replay %s\n", replay ? "ON (golden_raw)" : "OFF (ADC)");
}

static void gambar_tombol(int i)
{
    static const char *const label[3][2] = {
        {"B1 BUNYI", "B1 BISU"}, {"B2 JALAN", "B2 BEKU"}, {"B3 REC", "B3 STOP"}};
    const bool aktif = (i == 0) ? bisu : (i == 1) ? beku : rekam;
    const int x = i * 107;
    const uint16_t bg = tekan[i] ? ST77XX_YELLOW : ABU;
    tft.fillRect(x, 148, 105, 24, bg);
    tft.setTextSize(2);
    tft.setTextColor(tekan[i] ? ST77XX_BLACK : ST77XX_WHITE, bg);
    tft.setCursor(x + 6, 153);
    tft.print(label[i][aktif]);
}

// B1 pendek (bisu) bertindak saat DILEPAS, karena tahan 2 detik punya arti lain.
static void tombol()
{
    static uint32_t t_ubah[3];
    static bool b1_lama;                   // tahan sudah dieksekusi: lepasnya bukan toggle bisu
    if (tekan[0] && !b1_lama && millis() - t_ubah[0] >= TAHAN_MS) {
        b1_lama = true;
        ganti_replay();                    // berbunyi panjang lewat mulai_sesi()
    }
    for (int i = 0; i < 3; i++) {
        const bool kini = digitalRead(PIN_BTN[i]) == LOW;
        if (kini == tekan[i] || millis() - t_ubah[i] < 50) continue;   // debounce
        tekan[i] = kini;
        t_ubah[i] = millis();
        if (i == 0 && !kini && !b1_lama) bisu = !bisu;
        if (kini) {
            bunyi(20);                     // klik
            if (i == 0) b1_lama = false;
            if (i == 1) beku = !beku;
            if (i == 2) { if (rekam) simpan(); else mulai_rekam(); }
            Serial.printf("tombol B%d (GPIO%d)\n", i + 1, PIN_BTN[i]);
        }
        gambar_tombol(i);
    }
}

// HR diambil dari RR_prev beat yang lolos gerbang ayunan, sama dengan bip:
// tanpa elektroda detektor menemukan "beat" di derau, dan itu tidak boleh
// berbunyi atau tampil sebagai detak jantung.
static void saat_beat_ui(const ecg_beat_t &beat, bool aritmia)
{
    if (ayun_bersih_1s < AMBANG_AYUN) return;
    hr_tampil = (beat.rr[0] > 0.05f) ? (int)lroundf(60.0f / beat.rr[0]) : 0;
    hr_aritmia = aritmia;
    t_hr = millis();
    if (fase != FASE_KALIBRASI) jadwalkan_bip(beat, aritmia);   // kalibrasi: senyap
}

static void layar_1hz()
{
    static uint32_t t = 0;
    if (millis() - t < 1000) return;
    t = millis();

    const bool hr_ada = hr_tampil > 0 && millis() - t_hr < HR_BASI_MS;
    tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
    tft.setTextSize(2);
    tft.setCursor(4, 8);
    tft.print("HR");
    tft.setTextSize(3);
    tft.setCursor(32, 3);
    tft.setTextColor(hr_ada && hr_aritmia ? ST77XX_RED : ST77XX_WHITE, ST77XX_BLACK);
    if (hr_ada) tft.printf("%3d", hr_tampil);
    else        tft.print(" --");
    tft.setTextSize(1);
    tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
    tft.setCursor(90, 17);
    tft.print("bpm");

    // Warna fase sama dengan NeoPixel.
    tft.setTextSize(2);
    tft.setCursor(220, 8);
    if (rekam) {
        tft.setTextColor(ST77XX_RED, ST77XX_BLACK);
        tft.printf("REC%4u", (unsigned)(rekam_n / ECG_FS));
    } else if (replay) {
        tft.setTextColor(ST77XX_YELLOW, ST77XX_BLACK);
        tft.print("REPLAY ");
    } else if (fase == FASE_KALIBRASI) {
        tft.setTextColor(ST77XX_CYAN, ST77XX_BLACK);
        tft.print("KALIB  ");
    } else if (fase == FASE_BAIK) {
        tft.setTextColor(ST77XX_GREEN, ST77XX_BLACK);
        tft.print("BAIK   ");
    } else {
        tft.setTextColor(ST77XX_ORANGE, ST77XX_BLACK);
        tft.print("BURUK  ");
    }

    // INA219 di celah x 116..215. Chip merata-rata 128 sampel (~68 ms), jadi
    // satu baca per detik tidak melompat mengikuti burst 33 ms.
    float mA = 0, V = 0;
    const bool ina_ok = ina_ada && ina219_baca(R_SHUNT, &mA, &V);
    tft.setTextSize(2);
    tft.setCursor(116, 2);
    tft.setTextColor(ina_ok ? ST77XX_CYAN : ST77XX_RED, ST77XX_BLACK);
    if (ina_ok) tft.printf("%4.0fmA", mA);
    else        tft.print("INA -- ");
    tft.setTextSize(1);
    tft.setCursor(116, 20);
    if (ina_ok) tft.printf("%4.2fV %5.0fmW", V, mA * V);
    else        tft.printf("cek SDA%d SCL%d", I2C_SDA, I2C_SCL);

    // Label tombol bisa berubah lewat serial ('r'), jadi digambar ulang di sini.
    for (int i = 0; i < 3; i++) gambar_tombol(i);
}

// Bacaan INA219 untuk baris status serial 's'.
static const char *ina_teks()
{
    static char teks[48];
    float mA, V;
    if (ina_ada && ina219_baca(R_SHUNT, &mA, &V))
        snprintf(teks, sizeof teks, "I=%.1f mA V=%.3f V P=%.0f mW", mA, V, mA * V);
    else
        snprintf(teks, sizeof teks, "tidak menjawab");
    return teks;
}

static bool daya_mulai_ulang;

static void set_mode_daya(int m)
{
    static bool wifi_mati;
    mode_daya = m;
    if (m == 0) timerAlarmDisable(timer);
    else        timerAlarmEnable(timer);
    // esp_wifi_stop/start, bukan WiFi.mode(WIFI_OFF): yang terakhir ikut
    // men-deinit driver dan berebut dengan task WiFi (panic LoadProhibited di core 0).
    if (m >= 0 && m < 5) {
        if (!wifi_mati) { ecg_mqtt_set_aktif(0); esp_wifi_stop(); }
        wifi_mati = true;
    } else if (wifi_mati) {        // p5 / normal: radio kembali dengan setelan ecg_mqtt_mulai()
        esp_wifi_start();
        ecg_mqtt_mulai();
        ecg_mqtt_set_aktif(1);
        wifi_mati = false;
    }
    daya_mulai_ulang = true;
    if (m < 0) Serial.println("daya: mode normal");
    else       Serial.printf("daya: mode p%d, jendela %lu s\n", m, (unsigned long)(JENDELA_DAYA_MS / 1000));
}

// Rata-rata INA219 per jendela tetap, satu baris 'DAYA' per jendela. Dibaca tiap
// 100 ms (> 68 ms konversi 128 sampel), jadi tiap bacaan adalah rata-rata baru.
// Baris pertama sesudah ganti mode memuat transien; pencatat membuangnya.
static void ukur_daya()
{
    static uint32_t t_baca, t_jendela, beat0, lewat0;
    static double jml, jml2, jml_v;
    static int n;
    if (mode_daya < 0 || !ina_ada || millis() - t_baca < 100) return;
    t_baca = millis();
    if (daya_mulai_ulang) {
        daya_mulai_ulang = false;
        jml = jml2 = jml_v = 0; n = 0;
        t_jendela = millis(); beat0 = beat_dsp; lewat0 = n_lewat;
    }
    float mA, V;
    if (ina219_baca(R_SHUNT, &mA, &V)) { jml += mA; jml2 += (double)mA * mA; jml_v += V; n++; }
    if (millis() - t_jendela < JENDELA_DAYA_MS || n == 0) return;
    const double i = jml / n, v = jml_v / n;
    Serial.printf("DAYA p%d n=%d I=%.2f sd=%.2f mA V=%.3f P=%.1f mW beat=%u lewat=%u replay=%d\n",
                  mode_daya, n, i, sqrt(fmax(jml2 / n - i * i, 0.0)), v, i * v,
                  (unsigned)(beat_dsp - beat0), (unsigned)(n_lewat - lewat0), (int)replay);
    daya_mulai_ulang = true;
}

void setup()
{
    perangkat_mulai();              // PERTAMA: buzzer diam secepatnya, urutan SPI di dalamnya
    Serial.begin(115200);
    delay(1500);
    ina_ada = ina219_mulai(I2C_SDA, I2C_SCL);
    tft.drawFastHLine(0, GY - 2, TFT_W, ABU);
    for (int i = 0; i < 3; i++) gambar_tombol(i);

    rekam_buf = (uint16_t *)ps_malloc(REKAM_N * sizeof(uint16_t));
    if (!rekam_buf) Serial.println("PERINGATAN: PSRAM gagal, perekaman mentah nonaktif");

    // Ring backlog MQTT di PSRAM, target bab3.tex: +-27.000 rekaman (4-7 jam).
    // Satu entri 40 byte -> ~1,08 MB dari 8 MB. Kalau gagal, ecg_mqtt jatuh ke
    // cadangan statis 64 beat: backlog pendek jauh lebih baik daripada mati.
    ecg_mqtt_beat_t *ring = (ecg_mqtt_beat_t *)ps_malloc(
        ECG_MQTT_ANTRE_TARGET * sizeof(ecg_mqtt_beat_t));
    if (ring) {
        ecg_mqtt_antre_pasang(ring, ECG_MQTT_ANTRE_TARGET);
        Serial.printf("backlog: %u beat di PSRAM (%u KB, %u entri x %u B)\n",
                      ECG_MQTT_ANTRE_TARGET,
                      (unsigned)(ECG_MQTT_ANTRE_TARGET * sizeof(ecg_mqtt_beat_t) / 1024),
                      ECG_MQTT_ANTRE_TARGET, (unsigned)sizeof(ecg_mqtt_beat_t));
    } else {
        Serial.printf("PERINGATAN: PSRAM ring gagal, backlog turun ke %u beat\n",
                      ECG_MQTT_ANTRE_MIN);
    }
    if (!LittleFS.begin(true)) Serial.println("PERINGATAN: LittleFS gagal mount");

    siapkan_model();
    siapkan_replay();               // WAJIB sebelum timer jalan: ISR cuma baca
    mulai_sesi();
    ecg_mqtt_mulai();               // non-blocking: sambungan diurus di loop()

    timer = timerBegin(0, 80, true);
    timerAttachInterrupt(timer, &on_timer, true);
    timerAlarmWrite(timer, 1000000 / ECG_FS, true);
    timerAlarmEnable(timer);

    Serial.printf("\n=== MONITOR ARITMIA SIAP ===\n"
                  "fs=%u Hz  antrean=%u  arena=%u B  threshold=%.2f\n"
                  "tombol B1/B2/B3 = GPIO%d/%d/%d (bisu, beku, rekam)  |  serial: r/d/s/q/y/m/k\n"
                  "INA219 (SDA %d, SCL %d, 0x%02X): %s  |  TFT ST7789 %dx%d  |  buzzer GPIO%d @%u Hz\n",
                  ECG_FS, (unsigned)ANTRE_N, (unsigned)interp->arena_used_bytes(),
                  ECG_THRESHOLD, PIN_BTN[0], PIN_BTN[1], PIN_BTN[2],
                  I2C_SDA, I2C_SCL, INA219_ALAMAT, ina_ada ? "siap" : "TIDAK TERDETEKSI",
                  TFT_W, TFT_H, PIN_BUZZ, (unsigned)NADA_HZ);
}

void loop()
{
    static ecg_beat_t beat;

    // Kuras antrean ISR. Satu sampel per iterasi supaya tombol & serial tetap
    // responsif; beban 3% membuat antrean selalu terkejar.
    if (baca != tulis) {
        const float sampel = (float)antre[baca];
        baca = (baca + 1) % ANTRE_N;

        if (rekam && rekam_buf && rekam_n < REKAM_N) {
            rekam_buf[rekam_n++] = (uint16_t)sampel;
            if (digitalRead(PIN_LOP) || digitalRead(PIN_LON)) rekam_lepas++;
        }

        const bool dsp = mode_daya < 0 || mode_daya >= 2;
        const bool cnn = mode_daya < 0 || mode_daya >= 3;
        const bool ui = mode_daya < 0 || mode_daya >= 4;
        const int ada_beat = dsp ? ecg_live_push(sampel, &beat) : 0;
        if (dsp) nilai_kualitas(sampel);   // SETELAH push: baca sampel tersaring terbaru

        bool aritmia = false;
        if (ada_beat) {
            beat_dsp++;
            nilai_fase(beat);
            if (fase == FASE_KALIBRASI) {
                // bab3.tex: "inferensi CNN belum dijalankan" selama calibrating.
                // Detektor tetap jalan — RR-nya justru yang dipakai menilai
                // kelayakan sinyal. Yang dilewati cuma CNN-nya.
                static uint32_t t_lapor;
                if (millis() - t_lapor > 5000) {
                    t_lapor = millis();
                    Serial.printf("calibrating | RR=%.3fs dRR=%+.3fs | tenang %lu/%lu s | "
                                  "ayun %d (ambang %d) | stabil %lu/%lu s | lewati=%d replay=%d\n",
                                  beat.rr[0], beat.rr[2],
                                  (unsigned long)((millis() - t_rr_langgar) / 1000),
                                  (unsigned long)(RR_TENANG_MS / 1000), ayun_bersih_1s,
                                  AMBANG_AYUN,
                                  (unsigned long)((millis() - t_sesi_ms) / 1000),
                                  (unsigned long)(STABIL_MS / 1000), (int)lewati_kalibrasi,
                                  (int)replay);
                }
            } else if (cnn) {
                const float p = klasifikasi(beat);
                aritmia = p >= ECG_THRESHOLD;
                beat_total++;
                if (aritmia) beat_aritmia++;
                // BPM dari RR_prev, BUKAN dari selisih millis(): beat keluar
                // bergerombol setelah deteksi berkala, jadi jarak waktu
                // antar-cetak tidak sama dengan jarak antar-detak.
                const float bpm = (beat.rr[0] > 0.05f) ? 60.0f / beat.rr[0] : 0.0f;
                Serial.printf("beat %4d  p=%.4f  %-7s  RR=%.3fs  %3.0f bpm\n",
                              beat_total, p, aritmia ? "ARITMIA" : "normal", beat.rr[0], bpm);
                publikasi(beat, p, aritmia);
            }
            if (ui) saat_beat_ui(beat, aritmia);
        }
        if (ui) {
            jalankan_jadwal();
            plot(tertunda(ecg_live_tersaring_terakhir()));
        }
    }

    // Di luar cabang "ada sampel": sambung ulang & kuras backlog harus jalan
    // walau antrean ADC sedang kosong.
    ecg_mqtt_layani();
    perbarui_led();
    ukur_daya();

    if (Serial.available()) {
        const char c = Serial.read();
        if (c == 'r') { if (rekam) simpan(); else mulai_rekam(); }
        else if (c == 'd') { if (!rekam) dump(); else Serial.println("Sedang merekam."); }
        else if (c == 'y') ganti_replay();
        else if (c == 'p') {
            const uint32_t t0 = millis();
            while (!Serial.available() && millis() - t0 < 500) {}
            const char d = Serial.available() ? Serial.read() : 0;
            set_mode_daya(d >= '0' && d <= '5' ? d - '0' : -1);
        }
        else if (c == 'k') {
            lewati_kalibrasi = !lewati_kalibrasi;
            if (!lewati_kalibrasi) { mulai_sesi(); j_isi = 0; }   // gerbang penuh dari nol
            Serial.printf("lewati gerbang kalibrasi %s (bench saja — bab3 menuntut "
                          "stabilisasi 10-15 menit + RR tenang 30 s)\n",
                          lewati_kalibrasi ? "ON" : "OFF");
        }
        else if (c == 'm') {
            ecg_mqtt_set_aktif(!ecg_mqtt_aktif());
            Serial.printf("mqtt %s\n", ecg_mqtt_aktif() ? "ON" : "OFF");
        }
        else if (c == 'q') {
            lapor_kualitas = !lapor_kualitas;
            Serial.printf("laporan kualitas %s\n", lapor_kualitas ? "ON" : "OFF");
        }
        else if (c == 's')
            Serial.printf("status: rekam=%d n=%u | replay=%d | kualitas %s | beat %d "
                          "(%d aritmia, %d ditahan) | antrean %u | sampel hilang %u | "
                          "LO %d %d | mentah %d..%d ayun %d clipping %d\n"
                          "        mqtt %s | terkirim %u | backlog %u/%u | hilang %u | "
                          "gagal %u | paket %u/%u PDSR %.1f%% | tunda alat rata %u ms "
                          "maks %u ms | RTT maks %u ms (lambat %u) | RSSI %d dBm | epoch_ms %llu\n"
                          "        INA219 %s | bisu %d | beku %d | lewati %d | daya %d\n",
                          (int)rekam, (unsigned)rekam_n, (int)replay, nama_fase(),
                          beat_total, beat_aritmia, beat_ditahan,
                          (unsigned)((tulis - baca + ANTRE_N) % ANTRE_N), (unsigned)n_lewat,
                          digitalRead(PIN_LOP), digitalRead(PIN_LON),
                          mentah_min_1s, mentah_maks_1s, ayun_bersih_1s, (int)clipping_1s,
                          ecg_mqtt_status(), (unsigned)ecg_mqtt_terkirim(),
                          (unsigned)ecg_mqtt_antre_n(), (unsigned)ecg_mqtt_antre_kapasitas(),
                          (unsigned)ecg_mqtt_antre_hilang(), (unsigned)ecg_mqtt_gagal(),
                          (unsigned)ecg_mqtt_paket_ack(), (unsigned)ecg_mqtt_paket_kirim(),
                          ecg_mqtt_paket_kirim()
                              ? 100.0 * ecg_mqtt_paket_ack() / ecg_mqtt_paket_kirim() : 0.0,
                          (unsigned)(tunda_n ? tunda_jml / tunda_n : 0), (unsigned)tunda_maks,
                          (unsigned)ecg_mqtt_rtt_maks(), (unsigned)ecg_mqtt_rtt_lambat(),
                          ecg_mqtt_rssi(), (unsigned long long)ecg_mqtt_epoch_ms(),
                          ina_teks(), (int)bisu, (int)beku, (int)lewati_kalibrasi, mode_daya);
    }

    tombol();
    layar_1hz();
    if (buzz_sampai && (int32_t)(millis() - buzz_sampai) >= 0) {
        buzzer(false);
        buzz_sampai = 0;
    }
}
#endif
