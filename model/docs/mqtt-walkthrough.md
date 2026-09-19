# HW-6 — publikasi MQTT: dari beat di alat sampai baris di dashboard

**19 September 2026.** Modul: `firmware/src/ecg_mqtt.cpp`, `include/ecg_mqtt.h`,
plus sambungannya di `firmware/src/main.cpp`.

✅ **Status: TERVERIFIKASI DI BOARD, 19 September 2026.** Seluruh mekanisme
`bab3.tex` §Pipeline Edge-to-Cloud yang Resilien terpasang, dan **6 dari 6 target
Tabel Rencana Pengukuran terukur** — 5 lulus, 1 lulus di median tapi tidak di p95
(§7c).  `pio test -e native`
22/22, `pio test -e esp32-s3` 16/16, dan telemetri sungguhan mendarat di
ThingsBoard lewat WiFi. Uji resiliensi lulus: broker dibekukan 24 detik, deret
waktu di dashboard **tidak berlubang** (jeda maksimum 911 ms). Angka lengkap di
§7, tiga bug yang cuma muncul di hardware di §7b.

---

## 1. Peta besar

```
        ┌─────────────── SUMBER SINYAL (toggle 'y') ───────────────┐
        │  replay ON  : sim_counts[] dari golden_raw (record 208)  │
        │  replay OFF : adc1_get_raw() — AD8232, elektroda         │
        └──────────────────────────┬───────────────────────────────┘
                                   │ ISR 360 Hz → antrean 256
                                   v
   bandpass → Pan-Tompkins → selaraskan R → window+z-score → fitur RR
                                   │  (ecg_live_push)
                                   v
                        inferensi INT8 (TFLM)  →  p
                                   │
                                   v
                      ┌──── publikasi(): GERBANG ────┐
                      │ ayun_bersih_1s >= AMBANG_AYUN │
                      │ && !beat.sinyal_hilang        │
                      └──────────────┬────────────────┘
                                     v
                      ring backlog 64 beat (ecg_mqtt_antre_isi)
                                     │
                                     v   ecg_mqtt_layani(), tiap loop()
                      PUBLISH QoS 1 ──► broker ──► PUBACK
                                     │                  │
                          batch <=16 │       geser ring SETELAH PUBACK
                                     v
                          ThingsBoard CE: ts_kv → widget
```

Satu kalimat: **beat yang lolos gerbang kualitas masuk ring; ring dikuras ke
broker; ring baru digeser setelah PUBACK.**

---

## 2. Yang sudah ada sebelum HW-6 (jangan dibangun ulang)

| Bagian | Sudah ada di | Sejak |
|---|---|---|
| Sumber sinyal dummy | `main.cpp` `replay` / `sim_counts[]`, toggle `'y'` | HW-7 Task 4, **verified di board 18 Sep** |
| Broker + rule engine + dashboard | `dashboard/` (ThingsBoard CE) | b906903 |
| Kontrak payload (7 field, QoS 1, topic) | `dashboard/README.md`, `bab3.tex` | b906903 |
| Referensi kawat MQTT yang terbukti | `dashboard/smoke_test.py` | b906903 |
| Penilai kualitas sinyal | `main.cpp` `nilai_kualitas()`, `AMBANG_AYUN` | HW-4 |

HW-6 **tidak menambah satu pun** dari daftar itu. Yang ditambah cuma klien MQTT
dan gerbangnya.

---

## 3. Fungsi per fungsi

### 3.1 Dua gerbang: fase kalibrasi, lalu ayunan sinyal

`bab3.tex` §Pengujian Pipeline menetapkan **dua** tahap sebelum pemantauan mulai,
dan keduanya ada di `nilai_fase()`:

```
KALIBRASI -> BAIK butuh tiga hal sekaligus:
  1. elektroda stabil   millis() - t_sesi >= 10 menit
  2. RR layak & tenang  RR 300-1500 ms dan |dRR| <= 200 ms, konsisten 30 detik
  3. ayunan cukup       ayun_bersih_1s >= AMBANG_AYUN
```

Selama `calibrating` **CNN tidak dijalankan** (bab3: *"inferensi CNN belum
dijalankan"*) dan tidak ada yang dipublikasikan. Detektor tetap jalan — RR-nya
justru yang dipakai menilai kelayakan.

> ⚠️ **Kriteria RR itu gerbang MASUK, bukan gerbang per detak.** Sesudah fase
> pemantauan mulai, `dRR` TIDAK lagi dibatasi. Menegakkan `dRR <= 200 ms`
> terus-menerus akan membungkam justru aritmia yang ingin dideteksi — beat
> ventrikular memang datang dengan `dRR` besar. `bab3.tex` juga menuliskannya
> sebagai syarat *"layak untuk fase pemantauan"*, sekali saja.

Gerbang publikasi per detak:

```c
if (!ecg_mqtt_aktif()) return;
if (fase != FASE_BAIK)  { beat_ditahan++; return; }
if (beat.sinyal_hilang) { beat_ditahan++; return; }
```

**Dua gerbang, dua mekanisme independen.** Ayunan mengukur amplitudo, RR mengukur
kelayakan ritme. Beat karangan tanpa elektroda gagal di dua-duanya sekaligus:
ayunan ~27 counts (< 60) DAN RR 0,208 s (< 300 ms). Redundansi ini disengaja, dan
senada dengan pelajaran `lepas 0%`: satu indikator bisa berbohong, dua indikator
yang salah bersamaan jauh lebih jarang.

### 3.1b Kenapa replay harus melewati gerbang kalibrasi

`golden_raw` adalah **record 208**, penuh beat ventrikular; `dRR`-nya terukur
−0,364 s dan +0,478 s. Kriteria *"dRR ≤ 200 ms selama 30 detik"* **tidak akan
pernah terpenuhi** — dan memang tidak seharusnya: kriteria itu untuk subjek
**sehat** yang duduk diam, sementara sinyal uji kita sengaja aritmik.

Dua hal itu tidak bisa dipenuhi bersamaan, jadi yang mengalah gerbangnya, dengan
pengumuman: toggle `y` otomatis menyalakan `lewati_kalibrasi` dan serial mencetak
`GERBANG DILEWATI (bench)` saat fase berpindah. Toggle `k` melakukan hal sama
untuk jalur ADC. **Jalur sinyal tubuh tetap menegakkan gerbang penuh.**

**Digerbangi kualitas sinyal, bukan ada-tidaknya beat.** Alasannya terukur dan
sudah masuk daftar jebakan `../CLAUDE.md`:

> Tanpa elektroda, alat mengarang aritmia: **~2 beat/detik, 57% "ARITMIA"**.
> Ambang Pan-Tompkins adaptif relatif terhadap sinyal yang ada, jadi "tidak ada
> sinyal" bukan kondisi yang ia kenali — derau 15 counts pun punya puncak.

Kalau publikasi digerbangi beat, elektroda lepas = banjir alarm palsu ke broker.
`beat_ditahan` dihitung supaya penahanan itu terlihat di `'s'`, bukan jadi data
yang hilang diam-diam.

Baris ketiga menolak beat yang keluar lewat `ECG_LIVE_TIMEOUT` (asistol /
elektroda lepas). `ecg_live.h` sudah menyuruhnya: *"Pemanggil sebaiknya
menaikkan alarm 'sinyal hilang' TERPISAH dari klasifikasi aritmia, supaya tidak
mengotori metrik."*

### 3.2 `confidence` — keyakinan pada KEPUTUSAN, bukan `p` mentah

```c
t.confidence = aritmia ? p : 1.0f - p;
```

`p = 0,02` untuk beat normal artinya alat **sangat yakin**. Mengirim 0,02 apa
adanya membuat widget menampilkan "keyakinan 2%" persis saat alat paling yakin.

### 3.3 `ecg_mqtt_payload()` — murni, karena itu bisa diuji

```c
size_t ecg_mqtt_payload(char *buf, size_t n, const ecg_mqtt_beat_t *b, size_t nb,
                        uint64_t ts_base_ms);
```

`nb == 1` → objek tunggal; `nb > 1` → array. Dua bentuk itu bukan gaya, itu
kontrak ThingsBoard (`dashboard/README.md`: real-time vs batch flush).

**`ts` tiap beat = `ts_base_ms + beat.ms`.** Ini inti dari klaim resiliensi:
beat yang tertahan 40 detik di backlog tetap membawa waktu **kejadian**-nya.
Kalau `ts` diambil saat kirim, seluruh backlog menumpuk di satu detik dan
grafik dashboard berbohong — dan yang lebih buruk, uji dedup `smoke_test.py`
tetap lulus, jadi kesalahannya tidak akan ketahuan dari situ.

Buffer kurang → return **0**, bukan payload terpotong. JSON separuh diterima
broker sebagai sampah tanpa error yang terlihat di board. Diuji:
`test_payload_buffer_kurang`.

### 3.4 Ring backlog — dan kenapa `intip` terpisah dari `buang`

```c
size_t ecg_mqtt_antre_intip(ecg_mqtt_beat_t *keluar, size_t maks);
void   ecg_mqtt_antre_buang(size_t n);
```

Dipisah supaya **pointer baca hanya bergeser setelah PUBACK**:

```c
if (w && publish(buf, w)) {
    ecg_mqtt_antre_buang(n);          // HANYA setelah PUBACK
    terkirim += n;
}
```

Kalau digabung jadi satu `ambil()`, beat hilang setiap kali PUBACK tidak datang
— dan QoS 1 jadi hiasan. `dashboard/README.md` menulis syarat ini sebagai
kontrak: *"geser read pointer ring buffer hanya setelah PUBACK"*.

Ring penuh → **buang yang TERTUA**. Alat monitoring lebih butuh menit terakhir
daripada menit pertama saat koneksi baru pulih. Yang terbuang dicatat di
`ecg_mqtt_antre_hilang()`, tidak disembunyikan.

### 3.5 Klien MQTT — empat paket, tanpa library

`CONNECT` / `PUBLISH QoS1` / `PUBACK` / `PINGREQ`. Ditulis di atas `WiFiClient`.

Kawatnya **bukan tebakan**: `dashboard/smoke_test.py` sudah bicara ke broker
yang sama dengan byte yang sama (`0x10` CONNECT flags `0x80` username-saja,
`0x32` PUBLISH QoS1, cek `0x40` PUBACK + pid). Port C-nya menyalin itu.

### 3.6 Jam — `configTime()` + `ts_base_ms`

```c
ts_base_ms = (uint64_t)t * 1000ULL - (uint64_t)millis();
```

Epoch ms saat `millis() == 0`, dihitung sekali begitu SNTP masuk. Sesudah itu
tiap beat cukup menyimpan `millis()` (4 byte) dan waktunya direkonstruksi saat
payload disusun. Tanpa jam benar, `ecg_mqtt_status()` melapor `tunggu-jam` dan
backlog **menunggu** — sengaja tidak mengirim dengan ts salah.

---

## 4. Cara memakai — toggling lengkap

### 4.1 Sekali di awal: kredensial

```bash
cd dashboard && docker compose up -d      # broker + dashboard
python3 smoke_test.py                     # cetak: device ... token=XXXX
ip addr                                   # IP laptop, BUKAN localhost

cd ../firmware
cp include/wifi_secrets.example.h include/wifi_secrets.h
$EDITOR include/wifi_secrets.h            # isi SSID/PASS/TB_HOST/TB_TOKEN
```

`include/wifi_secrets.h` ada di `.gitignore` — kredensial tidak pernah masuk git.
**Tanpa file itu firmware tetap ter-build dan tetap jalan**, MQTT-nya saja yang
nonaktif dengan satu baris peringatan saat boot (`#if __has_include`).

`TB_HOST` = IP laptop di jaringan, bukan `localhost`: board mencarinya di
jaringan, bukan di dirinya sendiri.

### 4.2 Toggle serial

| Tombol | Arti | Keluaran |
|---|---|---|
| **`y`** | **sumber sinyal: replay ⇄ ADC** | `replay ON (golden_raw)` / `replay OFF (ADC)` |
| **`m`** | **publikasi MQTT: on ⇄ off** | `mqtt ON` / `mqtt OFF` |
| **`k`** | **lewati gerbang kalibrasi** (bench saja) | `lewati gerbang kalibrasi ON` |
| `q` | laporan kualitas tiap detik | `kualitas \| mentah … ayun … BERSIH …` |
| `s` | status sesaat (termasuk MQTT) | lihat di bawah |
| `r` | rekam mentah ke LittleFS | `REKAM mulai` / `SIMPAN …` |
| `d` | dump rekaman lewat serial | `---MULAI--- … ---SELESAI---` |

Dua toggle itu **ortogonal**, dan itu memang tujuannya:

| | `m` OFF | `m` ON |
|---|---|---|
| **`y` ON (replay)** | uji pipeline & daya, offline | **uji MQTT tanpa elektroda** ← dipakai selama PCB masih desain |
| **`y` OFF (ADC)** | akuisisi & rekam, offline | operasi normal |

### 4.3 Demo tanpa elektroda — urutan persis

```
1. boot, tunggu:   mqtt: WiFi "…" -> 192.168.x.x:1883
2. tekan 'm'  (kalau belum ON)  ->  mqtt ON
3. tekan 'y'                    ->  replay ON (golden_raw)
4. tunggu ~7 detik              ->  beat mulai keluar di serial
5. tekan 's'                    ->  mqtt online | terkirim N | backlog 0
6. buka http://localhost:8080   ->  telemetri masuk
```

**Kenapa replay lolos gerbang kualitas tanpa perlakuan khusus:** ayunannya
~2700 counts, jauh di atas `AMBANG_AYUN` 60. Jadi dummy dan sinyal tubuh
melewati **satu jalur kode yang sama persis** — tidak ada cabang `if (dummy)`
di mana pun. Itu disengaja: cabang khusus dummy berarti yang didemokan bukan
yang dipakai nanti.

### 4.4 Membaca baris status

```
status: rekam=0 n=0 | replay=1 | beat 44 (12 aritmia, 3 ditahan) | antrean 2 |
        sampel hilang 0 | LO 1 1 | mentah 1204..3550 ayun 2701 clipping 0
        mqtt online | terkirim 41 | backlog 0 | hilang 0 | gagal 0
```

| Kolom | Artinya kalau tidak nol |
|---|---|
| `ditahan` | beat yang sengaja TIDAK dipublikasi (kualitas / timeout) |
| `backlog` | beat menunggu di ring — broker sedang tak terjangkau |
| `hilang` | ring penuh, beat tertua dibuang — outage > ~53 detik |
| `gagal` | PUBACK tidak datang / tidak cocok |

`mqtt` bisa berisi: `mati` (toggle `m` off atau tanpa kredensial), `no-wifi`,
`no-broker`, `tunggu-jam` (SNTP belum masuk), `online`.

**Akuntansi kehilangan:** `beat_total − ditahan = terkirim + backlog + hilang`.
Identitas itu yang membuat uji resiliensi bisa diukur, dan ia cuma berlaku
karena replay **deterministik** — 11 beat per putaran 6,67 detik, sudah terukur
di board (`2026-09-18-robustness-changelog.md` §207).

---

## 5. Keputusan yang diambil, beserta alternatif yang ditolak

| Keputusan | Dipilih | Ditolak, dan kenapa |
|---|---|---|
| Letak data dummy | **sumber sinyal (ADC)** | *dummy di publisher* — melewati bandpass, detektor, dan inferensi. Yang teruji cuma JSON + WiFi, padahal klaim PA ini "klasifikasi di edge". Makin dekat titik injeksi ke tepi sistem, makin banyak kode nyata ikut teruji |
| Bentuk toggle | **runtime (`y`, `m`)** | *compile-time `#ifdef DUMMY`* — dua binary, dan yang didemokan bukan yang di-flash nanti |
| Klien MQTT | **ditulis sendiri, 4 paket** | *PubSubClient* — gate point CLAUDE.md (jangan tambah dependency untuk yang beberapa baris selesai); kawatnya sudah terbukti di `smoke_test.py`; preseden `ina219.cpp` yang juga tanpa library. **Kalau nanti butuh QoS 2, retained, atau subscribe, pindah ke PubSubClient — itu batas atas pilihan ini** |
| Gerbang publikasi | **ayunan sinyal** | *ada-tidaknya beat* — derau pun menghasilkan beat, 57% "ARITMIA" |
| `ts` | **waktu kejadian** (`base + millis`) | *waktu kirim* — backlog menumpuk di satu detik, dan `smoke_test.py` tetap lulus jadi tidak ketahuan |
| Geser ring | **setelah PUBACK** | *saat kirim* — QoS 1 jadi hiasan |
| Ring penuh | **buang tertua** | *tolak yang baru* — alat monitoring butuh menit terakhir |
| Kredensial | **header ter-`.gitignore`** | *hardcode* (bocor) / *`build_flags` di `platformio.ini`* (ikut ter-commit) |
| Nama field | **snake_case** | *camelCase* yang disarankan docs ThingsBoard — proposal terlanjur menulis snake_case dan tetap jalan normal |

---

## 6. Yang sengaja TIDAK dilakukan

- **TLS (port 8883).** Broker jalan di jaringan lokal untuk PoC. Pindah ke VPS
  nanti butuh ini, dan butuh sertifikat di flash — bukan pekerjaan PoC.
- **Subscribe / RPC dari dashboard ke alat.** Belum ada perintah yang perlu
  dikirim ke alat. `ecg_mqtt.cpp` cuma publish.
- **Backlog tahan reboot.** Ring ada di RAM. LittleFS sudah dipakai untuk
  rekaman mentah, jadi jalurnya ada kalau nanti dibutuhkan.
- **`ecg_sim.h` rekaman lebih panjang/beragam.** `2026-09-18-robustness-plan.md`
  Task 0 menulis: tambah **hanya kalau** dashboard butuh — keputusan setelah
  MQTT jalan, bukan sebelum. Masih berlaku.
- **Batch adaptif / kompresi payload.** 1 beat/detik × ~300 B tidak mendekati
  batas apa pun.

---

## 7. Angka nyata (diukur di board, 19 Sep 2026)

| Hal | Sebelum HW-6 | Sesudah |
|---|---|---|
| `pio test -e native` | 17/17 | **22/22** (+5 uji payload & ring) |
| `pio test -e esp32-s3` | 16/16 | **16/16** — inferensi tidak tersentuh |
| RAM (build) | 21,2% | **36,9%** (121.008 B) |
| Flash (build) | 6,6% | **13,5%** (881.861 B) |
| Ukuran payload 1 beat | — | ~330 B; batch 50 beat ~15 KB |
| Backlog | — | **27.000 beat** di PSRAM (1.054 KB, 40 B/entri) ≈ 4–7 jam |

⚠️ **Jangan memakai angka RAM/Flash yang diukur tanpa `wifi_secrets.h`.**
Tanpa file itu `WIFI_SSID` adalah `""`, `strlen("")` dilipat jadi konstanta oleh
kompilator, `WiFi.begin()` jadi kode mati, dan **seluruh tumpukan WiFi tidak
ikut di-link**: 26,4% / 8,0% — selisih 358 KB flash dari angka sebenarnya. Dua
build itu terlihat sama-sama "SUCCESS" dan bedanya tidak diumumkan di mana pun.

### Jalur data, terukur

| Hal | Angka |
|---|---|
| Laju beat replay | **1,60 beat/detik** (45 beat / 28,2 s) vs 1,58 terukur HW-7 |
| Baris mendarat di ThingsBoard | 171 baris / 103,2 detik, **0 ts duplikat** |
| Jeda antar-`ts` | **433–911 ms** — tidak bergerombol, tidak berlubang |
| Gerbang kualitas, tanpa elektroda | `beat 19 (7 aritmia, 19 ditahan)` → **terkirim 0** |
| Gerbang kualitas, replay | `ditahan 0` → **terkirim 100%** |
| `sampel hilang` selama semua uji | **0** |

Akuntansi `beat − ditahan = terkirim + backlog + hilang` cocok di setiap
pengambilan status. Contoh: `beat 148 = terkirim 147 + backlog 1 + hilang 0`.

### Uji resiliensi — `docker pause` 24 detik

```
[30,2s] mqtt online    | terkirim  20 | backlog  1 | hilang 0 | gagal 0
[32,3s] === docker pause ===
[54,0s] mqtt no-broker | terkirim  28 | backlog 33 | hilang 0 | gagal 1
[56,1s] === docker unpause ===
[58,2s] mqtt tersambung, backlog 43 beat
[82,8s] mqtt online    | terkirim 109 | backlog  0 | hilang 0 | gagal 1
```

`pause` dipilih, bukan `stop`: container membeku sehingga CONNECT tidak dijawab
sama sekali (SYN/paket ditelan), dan itu menguji batas waktu connect **dan**
CONNACK — lebih ganas daripada `stop` yang membalas RST seketika. Bonusnya
praktis: `unpause` pulih dalam 2 detik, sementara `docker start` butuh ~55 detik
menunggu ThingsBoard boot.

Yang membuktikan klaim di proposal: 24 detik outage, tapi **jeda maksimum di
deret waktu dashboard cuma 911 ms** — backlog mengisi lubangnya dengan `ts`
asli, bukan `ts` saat kirim.

Latensi per detak (26,6 ms) tidak berubah: publikasi cuma menyalin struct ke
ring; jaringan diurus `ecg_mqtt_layani()` di luar jalur beat.

---

## 7b. Tiga bug yang HANYA muncul di hardware

Semuanya lolos `pio test -e native` 22/22 dan lolos build. Ini catatan kenapa
"kode jadi" bukan "kode benar".

### (1) Menunggu PUBACK memblokir loop → 4.493 sampel hilang

Gejala: `antrean 255/256` (penuh), `sampel hilang 4493`, `PUBACK timeout`
berulang. Sebab: `publish()` menunggu PUBACK di tempat dengan batas 3 detik,
di dalam loop yang sedang menguras antrean ADC. Antrean 256 sampel @360 Hz =
**711 ms**, jadi satu timeout saja sudah melahap antrean penuh — dan interval RR
rusak, yaitu persis kegagalan yang arsitektur HW-4 dibangun untuk mencegah.

Perbaikan: PUBACK dipungut **lintas iterasi** `loop()` (`menunggu_ack` +
`pungut_ack()`), bukan di dalam satu panggilan. Tambahan: `ecg_mqtt_layani()`
dibatasi tiap 20 ms — dipanggil 360×/detik, `WiFi.status()` + `time()` sebanyak
itu ikut memakan anggaran 2.778 µs/sampel.

Hasil: 4.493 → **146**.

### (2) `sock.connect()` masih blocking → 2.788 sampel hilang saat broker booting

Gejala: `sampel hilang` melompat ke 2.788 tepat saat `docker start`. Sebab:
selama broker MATI, connect gagal seketika (RST) — tidak ada kerugian. Tapi saat
broker sedang **booting**, portnya terbuka dan paketnya ditelan, jadi
`sock.connect()` menggantung ~7,7 detik.

Perbaikan: `sock.connect(ip, port, 300)` — batas 300 ms, di bawah kedalaman
antrean 711 ms. Dan `IPAddress`, bukan hostname: resolusi DNS adalah panggilan
blocking **terpisah** yang tidak ikut dibatasi argumen timeout itu.

Hasil: 2.788 → **290**. Sisa 290 dari `tunggu()` CONNACK yang masih blocking
1.500 ms → CONNACK pun dijadikan non-blocking (`pungut_connack()`), dan fungsi
`tunggu()` dihapus seluruhnya.

Hasil akhir: **0**.

### (3) Enam `sock.write()` tanpa memeriksa nilai kembalian → paket terpotong

Gejala paling menipu dari ketiganya: `PUBACK timeout` berulang **padahal broker
sehat**, dan **hanya** saat backlog dikuras. Log broker bersih — nol petunjuk di
sisi sana. Sebab: paket MQTT ditulis 6 kali terpisah dan nilai kembaliannya
diabaikan. Saat payload besar (16 beat ≈ 4,8 KB) socket tidak menampung
semuanya; write pendek meninggalkan paket MQTT **terpotong**, broker menunggu
sisa yang tidak pernah datang, dan tidak pernah mengirim PUBACK.

Jadi gejalanya menyamar sebagai "broker lambat", padahal pengirimnya yang
berbohong soal berapa byte yang berhasil ditulis.

Perbaikan: satu paket dirakit di satu buffer, **satu** `sock.write()`, dan
panjangnya diperiksa (`!= q` → putus). `ECG_MQTT_BATCH_N` 16 → 8 supaya paket
tetap ~2,4 KB.

Hasil: `gagal` berhenti di 1 — satu-satunya yang sah, saat broker memang
dibekukan.

### (4) PINGRESP tidak pernah dibaca → aliran baca desync

Kita mengirim PINGREQ tiap 30 detik; broker membalas PINGRESP (2 byte,
`0xD0 0x00`) yang tidak pernah dibaca. Dua byte nyasar itu mengendap di socket
lalu terbaca sebagai dua byte pertama "PUBACK" berikutnya — aliran baca desync
permanen sampai reconnect.

Perbaikan: `pungut_masuk()` membaca header 2 byte, mengurus PUBACK, dan **membuang
isi paket lain secara utuh** supaya byte berikutnya tetap jatuh di batas paket.

**Catatan kejujuran:** ini bug nyata dan perbaikannya benar, **tapi ternyata bukan
penyebab** `PUBACK timeout` yang sedang dikejar — sesudah diperbaiki, `gagal`
masih 4 dalam 150 detik. Hipotesisnya salah, dan yang membuktikannya bukan
penalaran melainkan pencacah baru di bug (5).

### (5) Nagle menahan segmen kecil → PUBACK terlambat 1–4,8 detik

Alih-alih menebak lagi, dipasang pencacah RTT PUBACK dan pencetak keadaan saat
timeout. Hasilnya menunjuk satu arah:

```
mqtt: PUBACK lambat 1266 ms (1 beat)      <- berulang di ~1.250 ms
mqtt: PUBACK lambat 1278 ms (1 beat)
mqtt: PUBACK lambat 4235 ms (1 beat)
mqtt: PUBACK timeout, 1 beat terbang, 0 byte menunggu dibaca
                                          ^^^ socket KOSONG = bukan desync
27 kejadian >1 detik dalam 130 detik
```

`0 byte menunggu dibaca` menutup hipotesis desync: broker memang belum menjawab.
Dan nilai yang **berulang di ~1.250 ms** adalah tanda khas algoritma Nagle
berpasangan dengan delayed-ACK: segmen kecil (payload 1 beat ~330 B) ditahan
sampai ACK segmen sebelumnya datang.

Perbaikan: `sock.setNoDelay(true)` sesudah connect — satu baris.

| | sebelum | sesudah |
|---|---|---|
| `gagal` / 150 dtk | 4 | **0** |
| latensi p95 | 13.259 ms | **3.402 ms** |
| latensi maksimum | 19.926 ms | **4.903 ms** |
| PDSR | 96,7% | **99,5%** |

**Pola yang sama di kelimanya:** gagal tanpa error, dan gejalanya menunjuk ke
tempat yang salah (broker, bukan firmware). Senada dengan jebakan op `MEAN` di
TFLM dan `float` di ISR — repo ini sudah beberapa kali tertipu pola "salah tanpa
berisik".

Pelajaran kedua, khusus dari (4) vs (5): **dua bug dengan gejala identik bisa
hidup berdampingan.** Memperbaiki yang satu tidak menghilangkan gejalanya, dan
satu-satunya jalan keluar adalah memasang pencacah sampai gejalanya punya angka —
bukan menalar mana yang "paling mungkin".

---

## 7c. Target `bab3.tex` Tabel *Rencana pengukuran pada pengujian pipeline*

Diukur dengan `dashboard/ukur_pipeline.py 150` (replay ON, tanpa elektroda).

| Aspek | Target | Terukur | Vonis |
|---|---|---|---|
| PDSR | ≥ 95% | **99,5%** (206/207 paket) | ✅ |
| Latensi end-to-end | ≤ 2 detik | median **1.907 ms**, min 1.286 ms | ✅ median |
| — p95 | ≤ 2 detik | **3.402 ms** (maks 4.903 ms) | ❌ |
| Pemenuhan bufer lokal | tidak overflow dalam ±27.000 | kapasitas **27.000** terpasang di PSRAM | ✅ |
| Integritas data saat putus | tanpa kehilangan data | `hilang 0` untuk outage 24 detik | ✅ |
| Waktu pemulihan bufer | ≤ 60 detik | **~24 detik** (43 beat) | ✅ |
| Deduplikasi cloud | duplikat QoS-1 dikenali | **0 ts duplikat** dari 288 baris | ✅ |

### Latensi dipecah, supaya gagalnya dibebankan ke penyebab yang benar

Firmware mencacah `tunda alat` = dari beat TERJADI sampai paketnya ditulis ke
socket. Angkanya **stabil di 5 pengukuran**: 887 / 880 / 879 / 878 / **874 ms**
(maks 1.353 ms).

```
latensi total median   1.907 ms
  sisi alat              874 ms   <- kadens deteksi, BUKAN jaringan
  broker + cloud        ~1.033 ms
```

Sisi alat itu **arsitektural, bukan inefisiensi**: `ecg_live.h` menjalankan
deteksi tiap `ECG_LIVE_TIAP` = 1 detik atas ring 4 detik, dan sebuah beat baru
boleh keluar setelah `ECG_WIN_POST` = 128 sampel (356 ms) sesudah R tersedia.
Batas bawah teoretisnya 0–1.000 ms (menunggu tik deteksi) + 356 ms, dan minimum
terukur **1.286 ms** jatuh persis di rentang itu.

**Target 2 detik di proposal tidak memperhitungkan kadens deteksi 1 detik itu.**
Kalau p95 harus lolos, kandidat perubahannya `ECG_LIVE_TIAP` 1 detik → 0,5 detik
(hemat ~250 ms di median). Itu menyentuh modul yang sudah tervalidasi golden
Python↔C, jadi **gate point** — tidak diubah tanpa persetujuan.

Sisa ~1 detik milik broker: RTT PUBACK masih >1 detik pada 23 dari 207 paket
(maks 3.157 ms) walau `gagal 0`. ThingsBoard di laptop yang menjalankan 9
container lain bukan lingkungan yang wajar untuk klaim latensi — kalau angka p95
mau dipakai di laporan, ukur ulang di broker yang tidak bersaing beban.

---

## 8. Cek pemahaman

1. Kenapa `ecg_mqtt_antre_buang()` dipisah dari `ecg_mqtt_antre_intip()`, dan
   apa yang rusak kalau digabung?
2. Alat kehilangan WiFi 2 menit lalu pulih. Berapa beat sampai di broker, dan
   `ts`-nya menunjukkan waktu apa? (petunjuk: 64 vs 53 detik)
3. Elektroda dilepas tapi `m` masih ON. Berapa banyak yang terkirim ke broker,
   dan angka mana di baris `'s'` yang bergerak?
4. Kenapa replay tidak butuh cabang khusus untuk lolos gerbang kualitas?
5. `ts_base_ms` masih 0 (SNTP belum masuk) tapi beat terus keluar. Ke mana
   beat-beat itu pergi, dan apa yang terjadi saat jam akhirnya tersinkron?
6. Kenapa `ecg_mqtt_payload()` mengembalikan 0 alih-alih memotong payload?

---

## 9. Skrip & berkas pendukung

| Berkas | Peran |
|---|---|
| `firmware/include/ecg_mqtt.h` | kontrak; bagian murni vs jaringan dipisah `#ifdef ARDUINO` |
| `firmware/src/ecg_mqtt.cpp` | payload + ring (murni), WiFi + MQTT (board) |
| `firmware/test/test_mqtt/test_mqtt.cpp` | 5 uji: format, batch, buffer kurang, FIFO, ring penuh |
| `firmware/include/wifi_secrets.example.h` | templat kredensial |
| `dashboard/smoke_test.py` | referensi kawat MQTT + uji dedup `ts_kv` |
| `dashboard/README.md` | kontrak field, dan kenapa ThingsBoard |

## 10. Sisa pekerjaan HW-6

- [x] Nyalakan di board dengan broker hidup — **selesai 19 Sep 2026**, 171 baris
      mendarat, laju 1,60 beat/detik cocok dengan 1,58 milik HW-7
- [x] Uji resiliensi — **lulus**, jeda maksimum 911 ms untuk outage 24 detik
- [ ] **Ukur daya mode MQTT.** HW-7 punya tangga mode `p0`–`p4` tapi WiFi belum
      pernah masuk pengukuran, dan radio itu beban terbesar di seluruh alat.
      Angka daya di laporan saat ini belum mencakupnya
- [ ] **Uji dengan sinyal tubuh** (tertahan HW-5: header AD8232 belum disolder).
      Dua hal yang cuma bisa diuji di sana: (a) apakah `AMBANG_AYUN` 60 memisahkan
      elektroda lepas dari sinyal tubuh lemah — replay ~2700 counts terlalu jauh di
      atas ambang; (b) **gerbang kalibrasi penuh** (10 menit + RR tenang 30 detik),
      yang tidak bisa dilewati replay karena record 208 memang aritmik (§3.1b)
- [ ] Ukur ulang latensi p95 di broker yang tidak bersaing beban dengan 9 container
      lain, atau turunkan `ECG_LIVE_TIAP` (gate point — lihat §7c)
- [ ] Widget dashboard untuk `ecg_snippet` (datanya sudah masuk, belum digambar)
