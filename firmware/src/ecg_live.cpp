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
#if ECG_RR_RATIO
static float qrsw_riwayat[2 * ECG_RR_LOCAL_WINDOW];
static size_t n_qrsw;
// Indeks sampel ABSOLUT dari beat terakhir yang dikeluarkan lewat timeout.
// Absolut, BUKAN posisi di r_hist: r_hist bergeser (memmove) saat penuh, jadi
// posisi tersimpan akan basi dan beat bisa keluar dua kali.
static int r_timeout;
#endif

void ecg_live_reset(void)
{
    memset(sos_state, 0, sizeof(sos_state));
    memset(ring, 0, sizeof(ring));
    n_total = sejak_deteksi = 0;
    n_hist = n_beat = n_antre = i_antre = 0;
    r_terakhir = -ECG_PT_REFRACTORY;
#if ECG_RR_RATIO
    memset(qrsw_riwayat, 0, sizeof(qrsw_riwayat));
    n_qrsw = 0;
    r_timeout = -1;
#endif
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

// Susun satu beat siap-klasifikasi dari r[idx]. Return 0 kalau window tak muat
// di ring (bisa terjadi kalau denyut sangat lambat) — gagal aman, bukan diam
// merusak: beat dilewati, bukan diisi angka sampah.
static int keluarkan(int idx, const int *r, size_t n_r, int sentinel,
                     ecg_beat_t *beat)
{
    const int r_nilai = r[idx];
    if (!ecg_rr_features(r, n_r, (size_t)idx, ECG_FS, beat->rr)) {
        return 0;
    }
    static float potong[ECG_LIVE_RING];
    const size_t awal = n_total - ((n_total < ECG_LIVE_RING) ? n_total : ECG_LIVE_RING);
    const size_t n = n_total - awal;
    ambil(awal, n, potong);
    if (!ecg_window_zscore(potong, n, r_nilai - (int)awal, beat->window)) {
        return 0;
    }
#if ECG_QRSW
    ecg_qrs_width_features(beat->window, qrsw_riwayat, n_qrsw,
                           beat->rr + ECG_N_RR_DASAR);
    n_qrsw++;
#endif
    beat->r_abs = r_nilai;
    beat->sinyal_hilang = sentinel;
    n_beat++;
    return 1;
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

        // Butuh 3 R-peak (i >= 2) agar fitur RR ada — aturan yang sama dengan
        // valid_beat_indices di prep_beats.py.
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
#if ECG_RR_RATIO
        // TUNDA 1 BEAT (GATE G2): yang dinilai bukan R yang baru datang, tapi
        // yang SEBELUMNYA — karena RR+1/RR0 butuh r[i+1], dan r_abs itulah
        // "i+1"-nya. Buffer tidak berubah: r_hist sudah memuat keduanya.
        const int idx_nilai = idx_hist - 1;
        if (idx_nilai < 2 || r_hist[idx_nilai] <= r_timeout) {
            continue;                    // sudah dikeluarkan lewat timeout
        }
#else
        const int idx_nilai = idx_hist;
#endif
        if (!keluarkan(idx_nilai, r_hist, n_hist, 0, beat)) {
            continue;
        }
        return 1;
    }

#if ECG_RR_RATIO
    // Timeout: R berikutnya tidak datang. Keluarkan beat yang menggantung dengan
    // R SEMU (asumsi RR berikutnya = RR sekarang) -> RR+1/RR0 = 1,0 tepat, yaitu
    // sentinel netral. Tidak perlu mengubah ecg_rr_features sama sekali.
    if (n_hist >= 3 && r_hist[n_hist - 1] > r_timeout) {
        const int r_akhir = r_hist[n_hist - 1];
        if (n_total > (size_t)r_akhir && n_total - (size_t)r_akhir > ECG_LIVE_TIMEOUT) {
            int r_tmp[ECG_LIVE_HIST + 1];
            memcpy(r_tmp, r_hist, (size_t)n_hist * sizeof(int));
            r_tmp[n_hist] = r_akhir + (r_akhir - r_hist[n_hist - 2]);
            if (keluarkan(n_hist - 1, r_tmp, (size_t)n_hist + 1, 1, beat)) {
                r_timeout = r_akhir;
                return 1;
            }
        }
    }
#endif
    return 0;
}

float ecg_live_tersaring_terakhir(void)
{
    return n_total ? ring[(n_total - 1) % ECG_LIVE_RING] : 0.0f;
}

size_t ecg_live_total_sampel(void) { return n_total; }
int ecg_live_total_beat(void) { return n_beat; }
