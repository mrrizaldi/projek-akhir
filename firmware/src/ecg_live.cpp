// Implementasi alur hidup. Kontrak & alasan: include/ecg_live.h
#include "ecg_live.h"

#include <string.h>

static float ring[ECG_LIVE_RING];       // sinyal TERFILTER, melingkar
static float scratch[ECG_LIVE_RING];    // buffer kerja detektor
static int r_det[64];

static float sos_state[ECG_N_SOS * 2];
static size_t n_total;                  // sampel yang sudah masuk sejak reset
static size_t sejak_deteksi;
static int r_hist[ECG_LIVE_HIST];       // indeks absolut R, terurut
static int n_hist;
static int r_terakhir;                  // R terakhir yang sudah dikeluarkan
static int n_beat;

// Antrean beat siap: deteksi berkala bisa menemukan >1 beat sekaligus,
// sementara push() mengembalikan satu per panggilan.
static int antre[8];
static int n_antre, i_antre;

void ecg_live_reset(void)
{
    memset(sos_state, 0, sizeof(sos_state));
    memset(ring, 0, sizeof(ring));
    n_total = sejak_deteksi = 0;
    n_hist = n_beat = n_antre = i_antre = 0;
    r_terakhir = -ECG_PT_REFRACTORY;
}

static float dari_ring(size_t abs_idx)
{
    return ring[abs_idx % ECG_LIVE_RING];
}

// Salin potongan ring [awal, awal+n) ke buffer lurus supaya fungsi pipeline
// (yang menganggap array kontigu) bisa dipakai apa adanya.
static void ambil(size_t awal, size_t n, float *keluar)
{
    for (size_t i = 0; i < n; i++) {
        keluar[i] = dari_ring(awal + i);
    }
}

static void tambah_hist(int r_abs)
{
    if (n_hist == ECG_LIVE_HIST) {
        memmove(r_hist, r_hist + 1, (ECG_LIVE_HIST - 1) * sizeof(int));
        n_hist--;
    }
    r_hist[n_hist++] = r_abs;
}

static void jalankan_deteksi(void)
{
    const size_t n = (n_total < ECG_LIVE_RING) ? n_total : ECG_LIVE_RING;
    if (n < (size_t)(2 * ECG_FS)) {
        return;                          // ambang adaptif butuh 2 detik pertama
    }
    const size_t awal = n_total - n;     // indeks absolut sampel tertua di ring

    static float lurus[ECG_LIVE_RING];
    ambil(awal, n, lurus);

    const int jml = ecg_detect_r(lurus, n, scratch, r_det, 64);
    for (int i = 0; i < jml; i++) {
        const int r_sel = ecg_align_r(lurus, n, r_det[i]);
        const int r_abs = (int)awal + r_sel;

        if (r_abs - r_terakhir < ECG_PT_REFRACTORY) {
            continue;                    // sudah pernah dikeluarkan / terlalu rapat
        }
        // Window harus utuh DAN masih ada di ring.
        if (r_abs - ECG_WIN_PRE < (int)awal) continue;
        if (r_abs + ECG_WIN_POST > (int)n_total) continue;

        tambah_hist(r_abs);
        r_terakhir = r_abs;
        if (n_antre < 8) {
            antre[n_antre++] = r_abs;
        }
    }
}

int ecg_live_push(float sampel_mentah, ecg_beat_t *beat)
{
    float terfilter;
    ecg_bandpass(&sampel_mentah, &terfilter, 1, sos_state);
    ring[n_total % ECG_LIVE_RING] = terfilter;
    n_total++;

    if (++sejak_deteksi >= ECG_LIVE_TIAP) {
        sejak_deteksi = 0;
        n_antre = i_antre = 0;
        jalankan_deteksi();
    }

    while (i_antre < n_antre) {
        const int r_abs = antre[i_antre++];

        // Butuh 3 R-peak (i >= 2) agar RR_prev & dRR ada — aturan yang sama
        // dengan valid_beat_indices di prep_beats.py.
        if (n_hist < 3) {
            continue;
        }
        int idx_hist = -1;
        for (int i = 0; i < n_hist; i++) {
            if (r_hist[i] == r_abs) { idx_hist = i; break; }
        }
        if (idx_hist < 2) {
            continue;
        }
        if (!ecg_rr_features(r_hist, (size_t)n_hist, (size_t)idx_hist, ECG_FS, beat->rr)) {
            continue;
        }

        static float potong[ECG_LIVE_RING];
        const size_t awal = n_total - ((n_total < ECG_LIVE_RING) ? n_total : ECG_LIVE_RING);
        const size_t n = n_total - awal;
        ambil(awal, n, potong);
        if (!ecg_window_zscore(potong, n, r_abs - (int)awal, beat->window)) {
            continue;
        }
        beat->r_abs = r_abs;
        n_beat++;
        return 1;
    }
    return 0;
}

float ecg_live_tersaring_terakhir(void)
{
    return n_total ? ring[(n_total - 1) % ECG_LIVE_RING] : 0.0f;
}

size_t ecg_live_total_sampel(void) { return n_total; }
int ecg_live_total_beat(void) { return n_beat; }
