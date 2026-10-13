# Riwayat: Walkthrough `firmware/` — port ke ESP32-S3

**Dokumen sumber:** [`firmware-walkthrough.md`](../firmware-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## 18 Sep 2026 — nama test penyelarasan R
- **Perubahan:** test `test_align_r_menaruh_puncak_di_r_idx` semula bernama
  `..._di_94`, dengan angka 94 ditulis lurus di dua tempat. Saat window pindah ke
  128/128, satu tempat terlewat dan test gagal dengan pesan yang menuduh firmware.
  Test diubah menjaga sifat (`R_IDX = ECG_WIN_PRE + ECG_GROUP_DELAY`), bukan angka.
- **Alasan / bukti:** prinsip "test yang menjaga sifat harus menuliskan sifatnya"
  dipertahankan di dokumen aktif §2.

## 18 Sep 2026 — float di ISR replay
- **Perubahan:** versi pertama sumber sinyal replay mengalikan float langsung di
  `on_timer()`; board panic `Coprocessor exception` di detik 18,49. Diganti tabel
  `sim_counts[]` yang dikonversi sekali di `setup()`.
- **Alasan / bukti:** jebakan dan angkanya dipertahankan di dokumen aktif §5b.

## BPM dari `millis()`
- **Perubahan:** versi pertama firmware menghitung BPM dari selisih waktu
  antar-cetak (hasil "2000 bpm"); diganti BPM dari `beat.rr[0]`.
- **Alasan / bukti:** beat keluar bergerombol setelah deteksi berkala; dokumen aktif §5b.

## Window 250 → 256 (angka device)
- **Perubahan:** angka device sebelum window 256: inferensi 26,0 ms, arena 12.756 B,
  model 22,91 KB. Sesudah: 26,6 ms, 12.948 B, 22,94 KB.
- **Alasan / bukti:** dokumen aktif §6 menyajikannya sebagai biaya window 256 vs 250.

## Status jalur MQTT
- **Perubahan:** dokumen menulis gerbang kualitas untuk "jalur MQTT nanti" dan antrean
  256 "memberi ruang kalau nanti WiFi/MQTT ikut". Modul MQTT terpasang dan
  terverifikasi 19 Sep 2026; dokumen aktif kini merujuk `mqtt-walkthrough.md`.
- **Alasan / bukti:** diagram §5c diperbarui mengikuti `main.cpp` saat ini (gerbang
  kalibrasi, publikasi, `ecg_mqtt_layani`). Diagram lama menulis "LED kedip (merah =
  aritmia)"; kode saat ini memakai LED untuk kualitas sinyal/rekam.

## Jumlah test native
- **Perubahan:** tabel perintah menulis "11 test di PC". Kode saat ini: 23 test
  (`test_preproc` 11, `test_ina219` 6, `test_mqtt` 6).
- **Alasan / bukti:** `pio test -e native`, Okt 2026: 23 succeeded.
