# Daftar placeholder gambar buku-pa

Gambar di buku-pa yang belum ada berkasnya. Di posisinya, `.tex` memuat
`\PlaceholderGambar` dan kartu spesifikasi (komentar `% PLACEHOLDER-GAMBAR`).
Sumber kebenaran tetap kartu di `.tex`; dokumen ini adalah ringkasannya.
Daftar terkini:

```bash
grep -rn "PLACEHOLDER-GAMBAR" laporan/buku-pa/bab
```

Ada dua kelompok:

- **A. Revisi gambar proposal** (5): gambar proposal dipakai sebagai dasar,
  lalu label yang disebut di kolom "Ubah" diganti.
  Berkas asal ada di `laporan/proposal-pa/gambar/`.
- **B. Gambar baru** (7): tidak ada padanannya di proposal.

## Cara memasang gambar jadi

1. Simpan berkas di folder ini (`laporan/buku-pa/gambar/`) dengan nama yang
   menjelaskan isinya, mis. `arsitektur_sistem.png`.
2. Di `.tex`, ganti baris `\PlaceholderGambar{...}{...}` dengan
   `\includegraphics[<ukuran dari kartu>]{gambar/<nama berkas>}`.
3. Hapus blok komentar `% PLACEHOLDER-GAMBAR` beserta kartunya.
   Baris `% sumber:` tetap disimpan.
4. Jangan ubah `\caption` dan `\label`, karena `\ref` di teks bergantung padanya.
5. Jalankan `cd laporan/buku-pa && make pdf`, lalu cek gambarnya di
   `output/main.pdf`.
6. Hapus barisnya dari dokumen ini.

## A. Revisi gambar proposal

| Label | Lokasi | Gambar asal (proposal) | Caption |
|---|---|---|---|
| `fig:arsitektur-sistem` | `bab/bab3.tex:20` | `gambar_3_1.png` | Arsitektur sistem secara *high-level view* |
| `fig:alir-preprocessing` | `bab/bab3.tex:129` | `gambar_3_2.png` | Flowchart preprocessing pada perangkat |
| `fig:segmentasi` | `bab/bab3.tex:171` | `gambar_segmentasi_normalisasi.png` | Ilustrasi segmentasi berbasis R-*peak* dan efek normalisasi *z-score* |
| `fig:pipeline-training` | `bab/bab3.tex:245` | `gambar_3_4.png` | Arsitektur model CNN *hybrid* dengan fitur RR |
| `fig:alir-firmware` | `bab/bab3.tex:361` | `gambar_3_5.png` | Flowchart *runtime firmware* dan jalur resilien (bufer PSRAM, *batch offload*, deteksi *half-open*) |

### fig:arsitektur-sistem

| Semula (proposal) | Menjadi |
|---|---|
| Label payload "JSON ~100-150 byte" | "±200 byte per rekaman, batch ≤ 50" |

Sumber angka: `firmware/src/ecg_mqtt.cpp` fungsi `ecg_mqtt_payload` (200 byte
tipikal, 215 byte terburuk per rekaman, diukur dengan mengompilasi fungsi itu
di PC); `firmware/include/ecg_mqtt.h` (`ECG_MQTT_BATCH_N 50`).

### fig:alir-preprocessing

| Semula (proposal) | Menjadi |
|---|---|
| Segmentasi "±250 sampel di R" | "256 sampel (128 sebelum, 128 sesudah R)" |
| Belum ada | Langkah "kompensasi offset + penyelarasan puncak" di antara deteksi R-peak dan segmentasi |
| Belum ada | Timer ISR 360 Hz dan antrean sampel sebelum filter |

Sumber angka: `model/config.py` (`FS = 360`, `WIN_LEN = 256`). Urutan alur
mengikuti urutan subsubbab preprocessing di Bab 3.

### fig:segmentasi

| Semula (proposal) | Menjadi |
|---|---|
| "window tetap = 250 sampel, 90 pra-R, 160 pasca-R" | "256 sampel, 128 pra-R, 128 pasca-R" |

Sumber angka: `model/config.py` (`WIN_PRE = 128`, `WIN_POST = 128`,
`WIN_LEN = 256`).

### fig:pipeline-training

| Semula (proposal) | Menjadi |
|---|---|
| "Window ECG 250 × 1" | "256 × 1" |
| "Dense 16 ReLu - Dropout" | "Dense 16 ReLU" (tanpa Dropout) |
| "Sigmoid σ ≥ 0.5" | "Sigmoid σ ≥ 0,80" |

### fig:alir-firmware

| Semula (proposal) | Menjadi |
|---|---|
| "Publikasi real-time per-rekaman" dan "Baca 50-100 rekaman" | Semua beat masuk antrean PSRAM, kirim batch ≤ 50, PUBACK dipungut tanpa blocking |
| Belum ada | Fase kalibrasi (kontak baik 60 detik + R-R tenang 30 detik) dan penilaian kontak elektroda tiap detik (lead-off, ayunan, dengung) sebelum publikasi |

Sumber: `firmware/include/ecg_mqtt.h` (`ECG_MQTT_BATCH_N 50`);
`firmware/src/gerbang.cpp` fungsi `gerbang_nilai_fase()` dan `publikasi()`
(gerbang sebelum `ecg_mqtt_antre_isi`); `firmware/src/ecg_mqtt.cpp` fungsi
`ecg_mqtt_layani()`.

Di `laporan/proposal-pa/gambar/` juga ada `gambar_3_5_revisi.mmd` (draf
Mermaid). Draf itu belum dicocokkan dengan tabel di atas, jadi periksa dulu
sebelum dipakai sebagai dasar.

## B. Gambar baru

| Label | Lokasi | Jenis | Dibuat oleh | Caption |
|---|---|---|---|---|
| `fig:blok-perangkat-keras` | `bab/bab3.tex:59` | Diagram blok, landscape | Digambar user | Diagram blok perangkat keras |
| `fig:3-tata-letak-layar` | `bab/bab3.tex:585` | Mockup layar TFT 320×172 (atau foto layar beranotasi) | Digambar user | Tata letak layar pemantauan pada perangkat |
| `fig:3-pohon-menu` | `bab/bab3.tex:646` | Diagram pohon menu, landscape | Digambar user | Struktur menu pada perangkat |
| `fig:3-alur-rekam` | `bab/bab3.tex:675` | Diagram keadaan, landscape | Digambar user | Diagram keadaan perekaman sinyal mentah |
| `fig:4-elektroda` | `bab/bab4.tex:132` | Foto dokumentasi, portrait | Difoto user | Posisi elektroda Lead II |
| `fig:4-foto-rakitan` | `bab/bab4.tex:271` | Foto perangkat, landscape | Difoto user | Rakitan perangkat pada ujicoba |
| `fig:4-bufer` | `bab/bab4.tex:931` | Plot data garis, landscape | Skrip plot belum ada, keputusan user | Jumlah detak pada bufer selama *broker* dibekukan 24 detik dan dikuras setelah dilanjutkan |

### fig:blok-perangkat-keras

- **Pesan:** komponen serta jalur sinyal dan daya di sekitar ESP32-S3.
- **Elemen:** ESP32-S3 N16R8; AD8232 (OUT ke ADC, LO+ LO-); elektroda RA LA RL;
  TFT ST7789 (SPI); modul buzzer pasif A18009 (VCC dari 3V3, I/O langsung ke
  GPIO, aktif LOW); tombol B1 B2 B3; LED NeoPixel; INA219 (I2C); jalur daya
  sel 18650 → TP4056 → INA219 (VIN+ ke VIN-) → konverter DC-DC → pin 5 V board;
  USB sebagai catu alternatif (garis putus-putus) saat daya tidak sedang diukur.
- **Alur baca:** sensor di kiri, ESP32-S3 di tengah, keluaran (TFT, buzzer, LED,
  WiFi) di kanan; tombol di atas; daya di bawah dari kiri ke kanan.
- **Teks:** nama komponen persis seperti di paragraf.
- **Bahan repo:** `firmware/include/perangkat.h`; `firmware/README.md` bagian
  Pin map dan Rangkaian catu baterai;
  `model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md`.

### fig:3-tata-letak-layar

- **Pesan:** isi setiap area layar pemantauan.
- **Elemen:** kiri atas "HR" (angka bpm); tengah atas bergantian antara
  "INA219" (arus mA besar, tegangan V dan daya mW kecil) dan "Waktu" (jam WIB
  HH:MM:SS + tanggal, atau uptime bila belum sinkron); kanan atas "Status
  rekaman" dengan contoh REC00:12 merah, JEDA kuning, SIMPAN hijau, RP 208
  kuning; tengah "Gelombang ECG"; bawah tiga kotak "B1", "B2", "B3" berlabel
  BUNYI/BISU, JALAN/BEKU, REC/JEDA/LANJUT.
- **Alur baca:** baris atas dari kiri ke kanan, gelombang di tengah, kotak
  tombol di bawah.
- **Teks:** label anotasi persis "HR", "INA219", "Waktu", "Status rekaman",
  "Gelombang ECG", "B1", "B2", "B3".
- **Bahan repo:** `firmware/README.md` bagian Antarmuka alat;
  `firmware/src/tampilan.cpp` (`gambar_tengah`, `gambar_kanan`, label tombol).
- **Ukuran:** `width=\linewidth,keepaspectratio`.

### fig:3-pohon-menu

- **Pesan:** enam menu utama beserta pilihan di bawah masing-masing.
- **Elemen:** akar "Menu"; "Sumber sinyal" (Sensor (ADC), REPLAY 208, Replay
  rekaman → daftar berkas); "Kalibrasi" (Mulai ulang, Lewati (bench), Status);
  "Tes perangkat" (Buzzer, Layar, ADC & lead-off, INA219, Tombol); "Ukur daya"
  (Mulai tangga, Hasil terakhir); "Jaringan" (WiFi → daftar, Broker → daftar,
  MQTT ON/OFF, Status); "Info".
- **Alur baca:** akar di kiri, menu utama dalam satu kolom, pilihan di kolom
  kanan.
- **Teks:** nama menu persis seperti di paragraf.
- **Bahan repo:** `firmware/README.md` bagian Pohon menu; `firmware/src/menu.cpp`
  (`H_AKAR`, `I_SUMBER`, `I_KALIB`, `I_TES`, `I_DAYA`, `I_JARINGAN`).
- **Ukuran:** `width=\linewidth,keepaspectratio`.

### fig:3-alur-rekam

- **Pesan:** tiga keadaan perekaman dan tombol yang memindahkannya.
- **Elemen:** keadaan "Tidak merekam", "Merekam", "Dijeda"; aksi "Simpan berkas"
  (berkas bernomor di flash). Panah: Tidak merekam → Merekam "B3 pendek (sumber
  sensor)"; Merekam → Dijeda "B3 pendek"; Dijeda → Merekam "B3 pendek";
  Merekam → Simpan berkas dan Dijeda → Simpan berkas "B3 lama"; Simpan berkas →
  Tidak merekam. Catatan pada Merekam dan Dijeda: "menu dan pergantian
  pengaturan terkunci". Catatan pada transisi Dijeda → Merekam: "penanda jeda
  ditulis".
- **Alur baca:** kiri ke kanan, Tidak merekam → Merekam ↔ Dijeda → Simpan
  berkas → kembali ke Tidak merekam.
- **Teks:** label persis seperti di Elemen.
- **Bahan repo:** `firmware/src/rekam.cpp` (`rekam_toggle`, `jeda`,
  `rekam_tolak`); `firmware/README.md` bagian Merekam;
  `model/docs/akuisisi-walkthrough.md` §3.
- **Ukuran:** `width=\linewidth,keepaspectratio`.

### fig:4-elektroda

- **Pesan:** letak tiga elektroda wet-gel untuk Lead II.
- **Elemen:** torso dari bahu sampai pinggang **tanpa wajah, tato, atau penanda
  identitas**; RA di bawah selangka kanan; LA di bawah rusuk kiri; RL di bawah
  rusuk kanan sebagai referensi.
- **Alur baca:** atas ke bawah, yaitu RA, LA, lalu RL.
- **Teks:** label persis "RA", "LA", "RL".
- **Bahan repo:** `model/docs/akuisisi-walkthrough.md` §1.
- **Ukuran:** `height=0.4\textheight,keepaspectratio`.

### fig:4-foto-rakitan

- **Pesan:** susunan fisik rakitan yang dipakai pada uji perangkat dan perekaman.
- **Elemen:** ESP32-S3 N16R8; AD8232 dengan kabel elektroda RA LA RL; TFT
  ST7789 menyala dan menampilkan layar pemantauan; modul buzzer pasif A18009;
  tombol B1 B2 B3; INA219; catu (powerbank, atau sel 18650 + TP4056 + konverter
  DC-DC).
- **Alur baca:** kiri ke kanan, yaitu catu daya, ESP32-S3 dengan layar dan
  tombol, lalu AD8232 dan kabel elektroda.
- **Teks (opsional):** "ESP32-S3", "AD8232", "TFT", "Buzzer", "B1", "B2", "B3",
  "INA219", "RA", "LA", "RL".
- **Bahan repo:** `firmware/include/perangkat.h`; `firmware/README.md` bagian
  Pin map dan Rangkaian catu baterai; `model/docs/akuisisi-walkthrough.md` §1.
- **Ukuran:** `width=\linewidth,keepaspectratio`. Tanpa orang, wajah, atau
  identitas.
- **Perlu dikonfirmasi penulis:** rakitan ini PCB rev1 atau breadboard dengan
  peta pin PCB. Sesuaikan caption bila perlu.

### fig:4-bufer

- **Pesan:** backlog naik selama broker dibekukan, lalu terkuras habis tanpa
  ada detak yang hilang.
- **Elemen:** sumbu x "Waktu (detik)", sumbu y "Backlog (detak)"; satu garis
  backlog; penanda vertikal "Broker dibekukan" pada 32,3 detik dan "Broker
  dilanjutkan" pada 56,1 detik; empat titik terukur: 30,2 detik (1 detak),
  54,0 detik (33), 58,2 detik (43), 82,8 detik (0). Keempat titik diberi
  penanda dan disambung garis putus-putus karena nilai di antaranya tidak
  diukur.
- **Alur baca:** kiri ke kanan. Backlog hampir 0, naik sampai 43 detak selama
  broker beku, lalu terbaca 0 pada 82,8 detik, paling lama 24,6 detik sesudah
  perangkat tersambung kembali.
- **Teks:** label persis "Waktu (detik)", "Backlog (detak)", "Broker
  dibekukan", "Broker dilanjutkan".
- **Bahan repo:** `model/docs/mqtt-walkthrough.md` bagian "Uji resiliensi"
  (empat baris status bertanda waktu 30,2 s sampai 82,8 s).
- **Catatan:** titik datanya sedikit. Untuk kurva yang halus, uji perlu diulang
  sambil mencatat baris status `s` tiap detik. Skrip plot belum ada, jadi
  keputusannya ada di user.
- **Ukuran:** `width=\linewidth,keepaspectratio`.
