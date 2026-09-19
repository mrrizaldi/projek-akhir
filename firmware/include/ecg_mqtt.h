// Publikasi hasil klasifikasi ke broker MQTT (ThingsBoard CE).
//
// Dua bagian sengaja dipisah:
//   - MURNI  (payload JSON + antrean backlog) — tanpa Arduino, diuji di native
//   - JARINGAN (WiFi + MQTT 3.1.1) — di balik #ifdef ARDUINO
// Pemisahan itu yang membuat format payload bisa diuji tanpa board dan tanpa
// broker, sama seperti ecg_live.h menaruh inferensi di pemanggil.
//
// Kontrak field-nya milik dashboard/README.md ("Kontrak dengan firmware") dan
// bab3.tex §payload-json. Kalau berubah di satu tempat, ubah di ketiganya.
#ifndef ECG_MQTT_H
#define ECG_MQTT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Potongan sinyal untuk grafik dashboard. 8 titik = cukup untuk mengenali
// bentuk QRS di widget, dan menjaga payload di bawah ~300 B.
#define ECG_SNIPPET_N 8

// Kedalaman backlog saat broker tidak terjangkau. 64 beat ~= 53 detik pada
// 72 bpm. ponytail: ring di RAM, hilang kalau board reboot — kalau butuh
// tahan reboot, pindahkan ke LittleFS (alatnya sudah ada di main.cpp).
#define ECG_MQTT_ANTRE_N 64

// Batas beat per PUBLISH saat menguras backlog. Membatasi ukuran payload
// sekaligus memberi PUBACK titik pijak: gagal di tengah = ulangi 8, bukan 64.
// Diturunkan dari 16 setelah diukur di board: paket makin besar makin mungkin
// tidak habis ditulis sekali jalan, dan paket MQTT terpotong tidak pernah
// di-PUBACK. Sekarang panjangnya ikut diperiksa (lihat kirim_publish), 8 cuma
// menjaga paket tetap ~2,4 KB.
#define ECG_MQTT_BATCH_N 8

typedef struct {
    uint32_t ms;                      // millis() saat beat keluar
    float bpm;
    float rr_ms;
    float confidence;                 // keyakinan pada KEPUTUSAN, bukan p mentah
    int label;                        // 0 normal, 1 aritmia
    int quality_ok;                   // ayunan bersih >= AMBANG_AYUN
    int16_t snippet[ECG_SNIPPET_N];   // window z-score x1000, di sekitar R
} ecg_mqtt_beat_t;

// ---------- MURNI (native-testable) ----------

// Susun payload ThingsBoard. nb==1 -> objek tunggal, nb>1 -> array batch.
// ts tiap beat = ts_base_ms + beat.ms, jadi beat yang tertahan di backlog tetap
// membawa waktu KEJADIAN-nya, bukan waktu kirim. Tanpa ini klaim resiliensi
// runtuh: semua beat hasil flush akan menumpuk di satu detik.
// Return jumlah byte tertulis (0 kalau buf kurang).
size_t ecg_mqtt_payload(char *buf, size_t n, const ecg_mqtt_beat_t *b, size_t nb,
                        uint64_t ts_base_ms);

void ecg_mqtt_antre_reset(void);
size_t ecg_mqtt_antre_n(void);
size_t ecg_mqtt_antre_hilang(void);          // beat yang terbuang karena ring penuh
// Menaruh beat ke ring. Kalau penuh, beat TERTUA dibuang: alat monitoring lebih
// butuh menit terakhir daripada menit pertama saat koneksi baru pulih.
void ecg_mqtt_antre_isi(const ecg_mqtt_beat_t *b);
// Mengintip n beat tertua tanpa membuangnya. Pointer yang dibuang baru setelah
// PUBACK datang (ecg_mqtt_antre_buang) — itu yang membuat QoS 1 berarti.
size_t ecg_mqtt_antre_intip(ecg_mqtt_beat_t *keluar, size_t maks);
void ecg_mqtt_antre_buang(size_t n);

// ---------- JARINGAN (hanya di board) ----------
#ifdef ARDUINO
// Mulai WiFi + sinkron waktu (SNTP). Tidak memblokir: sambungan diurus
// ecg_mqtt_loop(). Aman dipanggil walau kredensial kosong (fitur mati).
void ecg_mqtt_mulai(void);
// Panggil tiap iterasi loop(). Mengurus sambung ulang, keepalive, dan menguras
// backlog. Murah saat idle (cek jam, bukan blocking I/O).
void ecg_mqtt_layani(void);
int  ecg_mqtt_tersambung(void);
int  ecg_mqtt_aktif(void);                   // toggle serial 'm'
void ecg_mqtt_set_aktif(int on);
uint32_t ecg_mqtt_terkirim(void);
uint32_t ecg_mqtt_gagal(void);
const char *ecg_mqtt_status(void);           // satu kata untuk baris status 's'
#endif

#ifdef __cplusplus
}
#endif
#endif  // ECG_MQTT_H
