// Inferensi dan publikasi. Kontrak: include/klasifikasi.h
#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "klasifikasi.h"

#include <Arduino.h>

#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#if __has_include("tensorflow/lite/micro/micro_error_reporter.h")
#include "tensorflow/lite/micro/micro_error_reporter.h"
#define TFLM_PUNYA_ERROR_REPORTER 1
#endif

#include "ecg_mqtt.h"
#include "gerbang.h"
#include "model_int8.h"
#include "tampilan.h"

constexpr int ARENA_N = 24 * 1024;
alignas(16) static uint8_t arena[ARENA_N];
static tflite::MicroInterpreter *interp;
static TfLiteTensor *in_morph, *in_rr, *keluar;

// tunda_*: tunda SISI ALAT, dari saat beat TERJADI sampai paketnya ditulis ke
// socket. Dipakai memecah latensi end-to-end jadi "milik alat" vs "milik
// jaringan+cloud", supaya target 2 detik bab3.tex bisa dibebankan ke penyebab
// yang benar.
static klasifikasi_hitung_t h;

const klasifikasi_hitung_t &klasifikasi_hitung(void) { return h; }
void klasifikasi_reset(void) { h = klasifikasi_hitung_t{}; }
size_t klasifikasi_arena(void) { return interp->arena_used_bytes(); }
float klasifikasi_ambang(void) { return ECG_THRESHOLD; }

void klasifikasi_mulai(void)
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
        while (true) { tampilan_led(64, 0, 0); delay(200); tampilan_led(0, 0, 0); delay(200); }
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
static void publikasi(const ecg_beat_t &beat, float p, bool aritmia)
{
    if (!ecg_mqtt_aktif()) return;
    if (gerbang_fase() != FASE_BAIK) { h.ditahan++; return; }
    if (beat.sinyal_hilang) { h.ditahan++; return; }      // beat timeout, RR+1 sentinel

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
    t.ms = gerbang_t_sesi_ms() + (uint32_t)((uint64_t)beat.r_abs * 1000ULL / ECG_FS);
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
    h.tunda_jml += tunda; h.tunda_n++;
    if (tunda > h.tunda_maks) h.tunda_maks = tunda;

    ecg_mqtt_antre_isi(&t);
}

bool klasifikasi_proses(const ecg_beat_t &beat)
{
    const float p = klasifikasi(beat);
    const bool aritmia = p >= ECG_THRESHOLD;
    h.total++;
    if (aritmia) h.aritmia++;
    // BPM dari RR_prev, BUKAN dari selisih millis(): beat keluar bergerombol
    // setelah deteksi berkala, jadi jarak waktu antar-cetak tidak sama dengan
    // jarak antar-detak.
    const float bpm = (beat.rr[0] > 0.05f) ? 60.0f / beat.rr[0] : 0.0f;
    Serial.printf("beat %4d  p=%.4f  %-7s  RR=%.3fs  %3.0f bpm\n",
                  h.total, p, aritmia ? "ARITMIA" : "normal", beat.rr[0], bpm);
    publikasi(beat, p, aritmia);
    return aritmia;
}
#endif
