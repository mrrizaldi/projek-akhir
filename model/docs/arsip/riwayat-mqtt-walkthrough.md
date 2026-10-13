# Riwayat: HW-6 — publikasi MQTT: dari beat di alat sampai baris di dashboard

**Dokumen sumber:** [`mqtt-walkthrough.md`](../mqtt-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Asal komponen yang dipakai ulang
- **Perubahan:** tabel §2 semula memuat kolom "Sejak": sumber sinyal dummy dari
  HW-7 Task 4 (terverifikasi di board 18 Sep 2026); broker + dashboard, kontrak
  payload, dan `smoke_test.py` dari commit `b906903`; penilai kualitas sinyal dari
  HW-4.
- **Alasan / bukti:** kolom asal-usul adalah riwayat; dokumen aktif cukup menyebut letaknya.

## 19 Sep 2026 — PUBACK lintas iterasi dan CONNACK non-blocking
- **Perubahan:** fungsi `tunggu()` yang menunggu CONNACK di tempat (1.500 ms)
  dihapus seluruhnya; CONNACK dipungut `pungut_connack()`. Fungsi pemungut PUBACK
  semula bernama `pungut_ack()`, kini `pungut_masuk()` (juga membuang PINGRESP).
- **Alasan / bukti:** sampel hilang 4.493 → 146 → 290 → 0 (dokumen aktif §7b bug 1–2).

## 19 Sep 2026 — penulisan paket dan ukuran batch
- **Perubahan:** paket MQTT semula ditulis 6 kali terpisah tanpa memeriksa nilai
  kembalian. Perbaikan pertama: satu buffer, satu `sock.write()`, panjang diperiksa
  (`!= q` → putus), dan `ECG_MQTT_BATCH_N` diturunkan 16 → 8 (paket ~2,4 KB).
  Perbaikan berikutnya: `kirim_sampai_habis()` menulis sisa secara bertahap (batas
  200 ms), sehingga batas ukuran paket hilang dan `ECG_MQTT_BATCH_N` dinaikkan ke 50
  (~15 KB, batas bawah target `bab3.tex`). Peta besar semula menulis "batch <=16".
- **Alasan / bukti:** paket terpotong tidak pernah di-PUBACK; komentar
  `ECG_MQTT_BATCH_N` di `ecg_mqtt.h`.

## Ring backlog 64 → 27.000 beat
- **Perubahan:** ring backlog semula statis 64 beat ("hilang" berarti outage > ~53
  detik). Kini 27.000 beat di PSRAM (target `bab3.tex`, 4–7 jam), dengan 64 beat
  sebagai cadangan bila alokasi PSRAM gagal. Soal cek pemahaman no. 2 semula
  berpetunjuk "64 vs 53 detik".
- **Alasan / bukti:** `ECG_MQTT_ANTRE_TARGET` / `ECG_MQTT_ANTRE_MIN` di `ecg_mqtt.h`.

## 19 Sep 2026 — bug PINGRESP bukan penyebab PUBACK timeout
- **Perubahan:** dokumen memuat "Catatan kejujuran": perbaikan PINGRESP (bug 4)
  dikira penyebab `PUBACK timeout`; sesudah diperbaiki, `gagal` masih 4 dalam 150
  detik. Hipotesis itu salah; penyebab sisanya (Nagle, bug 5) ditemukan lewat
  pencacah RTT baru, bukan penalaran.
- **Alasan / bukti:** dokumen aktif menyatakan fakta dua bug bergejala identik (§7b).

## 19 Sep 2026 — KOREKSI: broker tidak lambat
- **Perubahan:** versi dokumen sebelumnya menulis *"sisa ~1 detik milik broker"* dan
  menyalahkan ThingsBoard yang berbagi laptop dengan 9 container lain. Klaim itu
  salah dan sudah di-commit sebelum dibantah.
- **Alasan / bukti:** probe 60 detik (`dashboard/probe_rtt.py`; dokumen semula
  menyebut `scratchpad/probe_rtt.py`): RTT PUBACK laptop → broker median 1,1 ms,
  maks 3,5 ms, nol kejadian > 1 detik. Angka ~1 detik berasal dari galat jam
  `time()` (bug 6) dan retransmisi WiFi. Commit `6fc426c`.

## 19 Sep 2026 — `time()` → `gettimeofday()`
- **Perubahan:** `sinkron_jam()` semula memakai `time(NULL)`; potongan kode §3.6
  menulis `ts_base_ms = (uint64_t)t * 1000ULL - millis()`. Diganti `gettimeofday()`.
- **Alasan / bukti:** latensi minimum 1.286 → 429 ms, median 1.907 → 939–1.108 ms
  setelah koreksi jam (commit `6fc426c`).

## Status dan checklist (19 Sep 2026)
- **Perubahan:** dokumen dibuka dengan "✅ Status: TERVERIFIKASI DI BOARD" dan ditutup
  checklist "Sisa pekerjaan HW-6": board dengan broker hidup (selesai 19 Sep 2026,
  171 baris), uji resiliensi (lulus), ukur daya mode MQTT (terbuka), uji sinyal tubuh
  (tertahan HW-5: header AD8232 belum disolder), ukur ulang p95, widget `ecg_snippet`
  (terbuka). Dokumen aktif menyatakannya sebagai cakupan dan batas pengujian (§10).
- **Alasan / bukti:** —

## Angka build dan test
- **Perubahan:** angka 19 Sep 2026: `pio test -e native` 22/22 (17 + 5 uji MQTT),
  RAM 36,9% (121.008 B), Flash 13,5% (881.861 B). Kode Okt 2026: native 23/23
  (`test_antre_pasang_kapasitas` ditambahkan), RAM 37,0% (121.336 B), Flash 13,5%
  (887.873 B).
- **Alasan / bukti:** `pio run` dan `pio test -e native`, Okt 2026.
