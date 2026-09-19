// Firmware utama: akuisisi + klasifikasi aritmia langsung di alat.
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

#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#if __has_include("tensorflow/lite/micro/micro_error_reporter.h")
#include "tensorflow/lite/micro/micro_error_reporter.h"
#define TFLM_PUNYA_ERROR_REPORTER 1
#endif

#include "ecg_live.h"
#include "ecg_mqtt.h"
#include "model_int8.h"
#include "golden_ref.h"

constexpr adc1_channel_t KANAL_EKG = ADC1_CHANNEL_7;   // GPIO 8 (ADC1_CH7)
constexpr int PIN_LOP = 17, PIN_LON = 7;
constexpr int PIN_REC = 6, PIN_DUMP = 5, PIN_LED = 48;

constexpr size_t ANTRE_N = 256;            // >= 13 (puncak burst), dibulatkan pangkat 2
constexpr uint32_t DETIK_MAKS = 300;
constexpr size_t REKAM_N = (size_t)ECG_FS * DETIK_MAKS;
constexpr const char *BERKAS = "/rekaman.csv";
constexpr int ARENA_N = 24 * 1024;

// Ambang kualitas sinyal, dari akuisisi-walkthrough.md §2 (angka empiris, bukan
// tebakan: kontak segar 691 counts, elektroda dipakai ulang 195).
constexpr int AMBANG_AYUN = 60;            // ayunan TERSARING 1 detik, counts ADC
constexpr int ADC_ATAS = 4090, ADC_BAWAH = 5;

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

// Kualitas sinyal 1 detik terakhir (dipakai LED + laporan serial).
static int ayun_1s, ayun_bersih_1s, hum50_1s, mentah_min_1s, mentah_maks_1s;
static bool clipping_1s;
static bool lapor_kualitas;                // toggle 'q': cetak tiap detik

// Sumber sinyal replay: golden_raw (record 208, 2400 sampel, 8 beat = ~72 bpm)
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

// Konversi dilakukan SEKALI di setup(), bukan di ISR. Versi pertama mengalikan
// float di dalam on_timer() dan board panic "Coprocessor exception" (EXCCAUSE 4)
// setelah ~18 detik: ESP32 tidak menyimpan register FPU di konteks interrupt,
// jadi float di ISR merusak state FPU task yang sedang diinterupsi. Bukan crash
// seketika — itu sebabnya sempat lolos uji 20 detik.
static uint16_t sim_counts[GOLDEN_N];

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
static void mulai_sesi()
{
    ecg_live_reset();
    t_sesi_ms = millis();
}

static void publikasi(const ecg_beat_t &beat, float p, bool aritmia)
{
    if (!ecg_mqtt_aktif()) return;
    if (ayun_bersih_1s < AMBANG_AYUN) { beat_ditahan++; return; }
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
    t.quality_ok = 1;
    // Snippet: window z-score dicuplik merata dan dikali 1000 supaya muat di
    // int16 tanpa float di payload. ponytail: cuplikan merata, bukan di sekitar
    // R — kalau widget butuh QRS yang terpusat, ambil ECG_SNIPPET_N titik mulai
    // dari ECG_WIN_PRE.
    for (int i = 0; i < ECG_SNIPPET_N; i++) {
        const int j = i * (ECG_WIN_LEN_ - 1) / (ECG_SNIPPET_N - 1);
        t.snippet[i] = (int16_t)(beat.window[j] * 1000.0f);
    }
    ecg_mqtt_antre_isi(&t);
}

static void simpan()
{
    rekam = false;
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
// Tiga keadaan, tanpa kedip. Clipping DULU punya pola merah kedip sendiri;
// dicabut karena menumpuk arti di satu warna dan bikin merah ambigu. Clipping
// tetap dihitung dan dilaporkan lewat serial ('q' tiap detik, 's' sesaat) —
// yang hilang cuma penanda visualnya, jadi sinyal terpotong kini tampil HIJAU.
// LO+/LO- SENGAJA tidak dipakai menyetir LED: ia hanya melaporkan elektroda
// lepas total, dan pada 3-lead tanpa RL yang rapat ia menyala terus walau
// sinyalnya sebenarnya bagus. Ayunan mengukur yang benar-benar kita butuhkan.
static void perbarui_led()
{
    static uint32_t t_led = 0;

    if (millis() - t_led < 250) return;    // neopixelWrite matikan interrupt ~30 us
    t_led = millis();

    if (rekam)                             led(64, 0, 0);
    else if (ayun_bersih_1s < AMBANG_AYUN) led(64, 24, 0);
    else                                   led(0, 48, 0);
}

static bool ditekan(int pin, uint32_t &terakhir, bool &sebelumnya)
{
    const bool kini = (digitalRead(pin) == LOW);
    const uint32_t t = millis();
    bool tepi = false;
    if (kini != sebelumnya && t - terakhir > 50) {
        tepi = kini; sebelumnya = kini; terakhir = t;
    }
    return tepi;
}

void setup()
{
    Serial.begin(115200);
    delay(1500);
    // INPUT_PULLUP, bukan INPUT: kalau kabel LO putus/lepas, pin terbaca HIGH
    // = "elektroda lepas". Pin mengambang yang kebetulan terbaca LOW pernah
    // menipu kami — ia melaporkan "elektroda menempel" untuk kabel yang tidak
    // tersambung ke apa pun. Output LO AD8232 push-pull, jadi pull-up internal
    // 45k tidak melawannya.
    pinMode(PIN_LOP, INPUT_PULLUP); pinMode(PIN_LON, INPUT_PULLUP);
    pinMode(PIN_REC, INPUT_PULLUP); pinMode(PIN_DUMP, INPUT_PULLUP);

    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(KANAL_EKG, ADC_ATTEN_DB_11);

    rekam_buf = (uint16_t *)ps_malloc(REKAM_N * sizeof(uint16_t));
    if (!rekam_buf) Serial.println("PERINGATAN: PSRAM gagal, perekaman mentah nonaktif");
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
                  "REC=GPIO%d  DUMP=GPIO%d  |  serial: r/d/s/q/y/m\n",
                  ECG_FS, (unsigned)ANTRE_N, (unsigned)interp->arena_used_bytes(),
                  ECG_THRESHOLD, PIN_REC, PIN_DUMP);
}

void loop()
{
    static ecg_beat_t beat;
    static uint32_t t_rec = 0, t_dump = 0;
    static bool s_rec = false, s_dump = false;

    // Kuras antrean ISR. Satu sampel per iterasi supaya tombol & serial tetap
    // responsif; beban 3% membuat antrean selalu terkejar.
    if (baca != tulis) {
        const float sampel = (float)antre[baca];
        baca = (baca + 1) % ANTRE_N;

        if (rekam && rekam_buf && rekam_n < REKAM_N) {
            rekam_buf[rekam_n++] = (uint16_t)sampel;
            if (digitalRead(PIN_LOP) || digitalRead(PIN_LON)) rekam_lepas++;
        }

        const int ada_beat = ecg_live_push(sampel, &beat);
        nilai_kualitas(sampel);            // SETELAH push: baca sampel tersaring terbaru

        if (ada_beat) {
            const float p = klasifikasi(beat);
            const bool aritmia = p >= ECG_THRESHOLD;
            beat_total++;
            if (aritmia) beat_aritmia++;
            // BPM dari RR_prev, BUKAN dari selisih millis(): beat keluar
            // bergerombol setelah deteksi berkala, jadi jarak waktu antar-cetak
            // tidak sama dengan jarak antar-detak.
            const float bpm = (beat.rr[0] > 0.05f) ? 60.0f / beat.rr[0] : 0.0f;
            Serial.printf("beat %4d  p=%.4f  %-7s  RR=%.3fs  %3.0f bpm\n",
                          beat_total, p, aritmia ? "ARITMIA" : "normal", beat.rr[0], bpm);
            publikasi(beat, p, aritmia);
        }
    }

    // Di luar cabang "ada sampel": sambung ulang & kuras backlog harus jalan
    // walau antrean ADC sedang kosong.
    ecg_mqtt_layani();
    perbarui_led();

    if (Serial.available()) {
        const char c = Serial.read();
        if (c == 'r') { if (rekam) simpan(); else { rekam_n = rekam_lepas = n_lewat = 0; rekam = true; Serial.println("REKAM mulai"); } }
        else if (c == 'd') { if (!rekam) dump(); else Serial.println("Sedang merekam."); }
        else if (c == 'y') {
            replay = !replay;
            replay_i = 0;
            mulai_sesi();
            beat_total = beat_aritmia = beat_ditahan = 0;
            Serial.printf("replay %s\n", replay ? "ON (golden_raw)" : "OFF (ADC)");
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
            Serial.printf("status: rekam=%d n=%u | replay=%d | beat %d (%d aritmia, "
                          "%d ditahan) | antrean %u | sampel hilang %u | LO %d %d | "
                          "mentah %d..%d ayun %d clipping %d\n"
                          "        mqtt %s | terkirim %u | backlog %u | hilang %u | gagal %u\n",
                          (int)rekam, (unsigned)rekam_n, (int)replay, beat_total, beat_aritmia,
                          beat_ditahan,
                          (unsigned)((tulis - baca + ANTRE_N) % ANTRE_N), (unsigned)n_lewat,
                          digitalRead(PIN_LOP), digitalRead(PIN_LON),
                          mentah_min_1s, mentah_maks_1s, ayun_bersih_1s, (int)clipping_1s,
                          ecg_mqtt_status(), (unsigned)ecg_mqtt_terkirim(),
                          (unsigned)ecg_mqtt_antre_n(), (unsigned)ecg_mqtt_antre_hilang(),
                          (unsigned)ecg_mqtt_gagal());
    }

    if (ditekan(PIN_REC, t_rec, s_rec)) {
        if (rekam) simpan(); else { rekam_n = rekam_lepas = n_lewat = 0; rekam = true; Serial.println("REKAM mulai"); }
    }
    if (ditekan(PIN_DUMP, t_dump, s_dump)) {
        if (rekam) Serial.println("DUMP diabaikan saat merekam."); else dump();
    }
}
#endif
