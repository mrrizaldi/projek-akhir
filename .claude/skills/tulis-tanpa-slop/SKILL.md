---
name: tulis-tanpa-slop
description: Dipakai saat menyunting paragraf laporan PA (progres-pa-1, buku-pa) supaya tidak terbaca sebagai tulisan AI, atau saat user meminta "rapikan biar tidak AI slop", "humanize", atau "bersihkan gaya tulis". Isi, angka, sitasi, dan istilah tidak berubah; yang diubah frasa klise, struktur formulaik, dan kebiasaan kaku. Diperiksa scripts/cek_slop.py, termasuk banding invarian sebelum dan sesudah.
---

# Tulis tanpa slop

Asal: riset 21 Nov 2026 atas naskah-id (MIT), humanizer-indonesia (MIT),
blader/humanizer (MIT), stop-slop (MIT), Wikipedia "Signs of AI writing"
(CC BY-SA), dan bahasa-skills (tanpa lisensi, hanya rujukan gagasan). Katalog
lengkap 74 pola, sumber, dan konflik: `docs/2026-11-21-skill-anti-slop/katalog.md`.
Uji coba pertama hanya di `laporan/progres-pa-1/bab/bab2.tex` sampai
`bab4.tex` (keputusan user); Bab 1, bagian depan, dan Bab 5 tidak disentuh.

## Yang tidak boleh berubah

1. Angka, satuan, `\cite`, `\ref`, `\label`, nama variabel, dan baris
   komentar `%`. Diperiksa
   `python3 scripts/cek_slop.py --banding <lama.tex> <baru.tex>` (harus
   `invarian aman`).
2. Isi klaim dan derajat kepastiannya: *menunjukkan* (fakta) tetap fakta,
   *diduga* tetap dugaan. Kalimat yang butuh fakta pengganti tetapi faktanya
   tidak ada di naskah dibiarkan dan dilaporkan, tidak dikarang.
3. Tabel, isi `figure`, persamaan, dan `\caption` (kecuali galat mesin di
   dalamnya).
4. Aturan rumah di `laporan/CLAUDE.md` menang atas saran sumber:
   - tanpa titik dua, titik koma, dan em dash di paragraf; tanpa numbering
     inline;
   - istilah teknis bahasa Inggris dan miring (`\textit{board}`), daftar kata
     adopsi tegak tetap tegak; padanan Indonesia tidak dipakai;
   - desimal koma, ribuan titik, `~\cite{}`, judul Title Case;
   - tanpa "kami", "kita", "saya"; label internal repo tidak tercetak.

## Prinsip

- **Gerombolan, bukan kemunculan.** Satu "Selain itu" bukan masalah. Yang
  ditindak kepadatan dan pengulangan. Prinsip ini tidak berlaku untuk pola
  posisi dan pola `galat`: "karena itu" di tengah klausa dan koma sebelum
  "sehingga" diubah setiap kali muncul, walau hanya sekali.
- **Uji hapus.** Kalimat atau frasa yang bila dihapus tidak menghilangkan
  informasi dibuang. Penghubung sebab-akibat ("karena", "sehingga",
  "akibatnya", "karena itu") memuat informasi, yaitu hubungan antarfakta.
  Bentuk atau posisinya boleh diganti, tetapi hubungannya tidak boleh hilang
  dengan dalih uji hapus.
- **Ganti penilaian dengan fakta yang sudah ada di naskah.** "Latensinya
  sangat rendah" → "latensinya 38~ms, di bawah periode \textit{window}".
- **Variasi lahir dari isi.** Kalimat temuan pendek, sebab-akibat lebih
  panjang. Jangan memecah atau menggabung kalimat hanya demi variasi.
- **Penyuntingan minimal.** Kalimat yang tidak berpola dibiarkan.

## Pola yang ditindak

Kode dalam kurung = keluaran `cek_slop.py` (`galat` wajib nol, `tinjau`
diputuskan per kemunculan).

### Kebiasaan bawaan aturan rumah (paling sering di buku ini)

1. **"karena itu" disisipkan di tengah klausa** (S-KARENA-ITU). "DS2 tidak
   diberi \textit{jitter} dan karena itu mewakili anotasi tanpa
   \textit{error}." → "DS2 tidak diberi \textit{jitter} sehingga mewakili
   anotasi tanpa \textit{error}." atau pecah menjadi kalimat baru yang
   dibuka subjeknya. Hubungan sebabnya wajib tetap tertulis ("sehingga",
   "akibatnya", "karena"), bukan dibuang bersama "karena itu". Aturan ini
   soal posisi, jadi satu kemunculan pun diubah. Yang sah: "Karena itu," di
   awal kalimat bila jarang, serta "bukan karena itu" dan "justru karena
   itu" yang bermakna harfiah.
2. **"yaitu" berderet** (S-YAITU-PADAT, dua atau lebih per paragraf).
   Larangan titik dua tidak berarti setiap daftar memakai "yaitu". Ganti
   sebagian dengan "berupa", "meliputi", kurung, atau sebut langsung tanpa
   pengantar ("lima rekaman DS1 (101, 114, 201, 220, dan 223)").
3. **Koma sebelum "sehingga"** (S-KOMA-SEHINGGA, galat). EYD V: induk
   kalimat di depan anak kalimat tidak berkoma. Setiap ", sehingga" menjadi
   " sehingga", termasuk di kalimat yang tidak disunting karena alasan lain:
   "latensi rata-rata 939~ms, sehingga target terpenuhi" → "latensi
   rata-rata 939~ms sehingga target terpenuhi".
4. **"Jadi" pembuka kalimat** (S-JADI). Ragam lisan untuk kesimpulan; ganti
   dengan "Dengan begitu", "Akibatnya", atau gabung dengan kalimat
   sebelumnya, atau buang bila kalimatnya hanya mengulang.

### Frasa (umumnya dicek mesin)

- Pembuka zaman (S-ZAMAN), penegas tanpa bukti (S-PENEGAS), kalimat meta
  "perlu dicatat" (S-META), klaim digelembungkan "memegang peranan krusial"
  (S-GELEMBUNG), kata payung "berbagai aspek" (S-PAYUNG), penutup ritual
  "Secara keseluruhan," (S-PENUTUP), pleonasme "adalah merupakan"
  (S-PLEONASME), kalke "memainkan peran", "dalam kasus ini" (S-KALKE),
  "di mana"/"yang mana" sebagai penghubung (S-DIMANA, S-YANG-MANA), kata
  ganti orang (S-PERSONA), nada promosi dan emosi (S-PROMOSI, S-EMOSI).
- "signifikan" tanpa uji statistik (S-SIGNIFIKAN): sebut angka dan
  ambangnya. Kata mutlak "selalu", "pasti" (S-MUTLAK): sah bila datanya
  memang mencakup semua kasus.

### Kalimat

- **Subjek hilang** (S-SUBJEK): "Berdasarkan Tabel~4.2 menunjukkan ..." →
  "Tabel~4.2 menunjukkan ...".
- **Konjungsi berpasangan** (S-KONJ-GANDA): "Meskipun ..., tetapi ...".
- **"Sehingga"/"Sedangkan" di awal kalimat** (S-PEMBUKA-KONJ).
- **Penyangkalan antisipatif** "Ini bukan berarti ..." (S-SANGKAL): nyatakan
  batasnya langsung.
- **Kontras formulaik** "tidak hanya ... tetapi juga ..." (S-KONTRAS): baku
  bila sekali, ditindak bila berulang atau separuh negatifnya kosong.
- **Klausa ekor penafsiran** ", yang menunjukkan keandalan ..." (S-EKOR):
  ganti dengan pembanding faktual atau buang.
- **Kopula dihindari** "berperan sebagai otak sistem" (S-KOPULA): pakai
  "adalah" atau sebut tugasnya.
- **Nominalisasi** "melakukan pengukuran terhadap" (S-NOMINAL) → "mengukur".
- **Modalitas bertumpuk** "mungkin dapat berpotensi" (S-MODAL).
- **Kalimat lebih dari 35 kata** (S-PANJANG) dan **rantai "yang"**
  (S-RANTAI-YANG): pecah di batas klausa.
- **Personifikasi benda mati** (tidak dicek mesin): "model cukup cerdas",
  "ESP32-S3 bekerja keras" → sebut kerjanya dengan angka.
- **Triplet sifat** "efektif, efisien, dan andal" (tidak dicek mesin): buang
  sifat yang tidak dibuktikan; tiga metrik atau tiga kelas nyata tetap sah.

### Paragraf

- **Kalimat tentang dokumen** "Subbab ini membahas ..." (S-DOKUMEN).
- **Ringkasan di akhir paragraf** yang mengulang isinya: buang.
- **Kalimat penanda arah** "Hasilnya jelas." "Pertanyaannya sederhana.":
  gabung dengan fakta pertama.
- **Tinjauan pustaka per sumber** ("Menurut A ... Senada dengan itu, B ...",
  S-SENADA): susun per gagasan, sumber di `\cite`.
- **Rujukan spasial** "tabel berikut", "gambar di atas" (S-SPASIAL): pakai
  nomor `Tabel~\ref{}`.

## Yang bukan slop (jangan dikoreksi)

- Pasif di metode dan hasil ("Rekaman dibagi menjadi DS1 dan DS2").
- "Penelitian ini" sebagai subjek; *merupakan*/*adalah* untuk definisi.
- Hedging yang sesuai data ("berpotensi", "belum diukur").
- Istilah teknis yang memang dipakai literatur (*robust*, mengimplementasikan).
- Pengulangan istilah yang sama demi konsistensi (jangan diganti sinonim).

## Prosedur

Dari `laporan/progres-pa-1`. Cadangan sudah ada sebelum mulai (tag git atau
arsip); bila belum, buat dulu.

```bash
cp bab/bab3.tex /tmp/bab3.lama.tex
python3 ../../scripts/cek_slop.py --ringkas bab/bab3.tex
python3 ../../scripts/cek_slop.py bab/bab3.tex
python3 ../../scripts/cek_slop.py --banding /tmp/bab3.lama.tex bab/bab3.tex
python3 ../../scripts/cek_tabel.py bab/*.tex
python3 ../../scripts/cek_slop.py --ringkas bab/bab3.tex
make pdf
grep -cE "undefined|Overfull" output/main.log
```

Hasil yang diharapkan: `galat` 0, `tinjau` turun dan sisanya disengaja,
`invarian aman`, `cek_tabel` 0 galat, log 0. Satu bab per commit, pesan
commit memuat metrik `--ringkas` sebelum dan sesudah.
