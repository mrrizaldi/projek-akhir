# Eval: kicad-pcb-pa

Penilai: model berbeda dari penulis. Skor 0-10; lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah (tanpa akses repo, tidak menjalankan
perintah; keluaran perintah ditulis `[N]`).

## Tugas uji

Fakta yang diberikan ke peserta: KiCad terpasang 9.0.2; proyek di
`hardware/mainboard/`; server MCP kicad dipakai untuk membuat proyek dan
menyinkronkan skematik ke board; skrip pcbnew dijalankan dengan
`/usr/bin/python3`.

1. Sesudah `create_project` dari MCP, `kicad-cli sch export netlist` mencetak
   `Failed to load schematic`. Tiga baris pertama berkas:
   `(kicad_sch (version 20260101) (generator "eeschema") (generator_version "10.0")`.
   Tulis perubahan persisnya dan perintah yang membuktikan berkas terbaca.
2. Dioda `Diode:SS34` (pad 1 = K, pad 2 = A, footprint `Diode_SMD:D_SMA`,
   pad di x = −2 dan +2 mm pada rot 0) ditempatkan di (100; 100,8) dengan
   rotasi 180. Net +5V harus keluar dari katoda ke kiri menuju x = 90. Sebut
   koordinat pad K dan A sesudah rotasi, langkah yang dijalankan sebelum
   menggambar jalur, dan keputusan penempatan akhirnya.
3. Teman meninggalkan pin BLK TFT tidak tersambung. GPIO12 bebas, 3V3 ada.
   Tulis apa yang kamu lakukan sebelum menyambung BLK.
4. DRC `--schematic-parity` sesudah sinkronisasi MCP melapor 117 baris
   `Pad net (+5V) doesn't match net given by schematic (/+5V)` dan
   `Pad missing net given by schematic (unconnected-(U1-GPIO7{slash}ADC1_CH6-Pad7))`.
   Tulis perbaikannya, cara persis menerapkan perubahan skematik berikutnya
   ke board (fungsi pcbnew yang dipakai dan data yang disalin), dan perintah
   verifikasinya.
5. Kamu baru saja merute dan mengunci jalur daya, lalu ingin Freerouting
   merute sisanya. Tulis urutan langkah sebelum dan sesudah autoroute,
   termasuk parameter autoroute dan cara membuktikan jalur manual tidak
   berubah.
6. Papan dibuat di JLCPCB. Jalur `+3V3` (netclass Default) harus lewat di
   antara dua pin bertetangga di satu kolom U1 (pitch 2,54 mm, pad oval
   2,0 × 1,4 mm, sisi 1,4 mm searah pitch). Tulis lebar dan clearance profil
   papan, hitung apakah jalur selebar itu muat, dan bila tidak, apa yang kamu
   lakukan beserta angkanya.
7. User akan memakai holder 18650 berkabel yang ditempel di sisi atas papan.
   Baterai berukuran 65 × 18 mm; ukuran holder belum diukur. Tulis apa yang
   kamu lakukan di PCB dan bagaimana membuktikannya.
8. Footprint `PinSocket_1x06` (J3) diputar 90° sehingga barisan pinnya
   mendatar sepanjang 12,7 mm, tetapi ref dan value-nya ikut tegak. Ruang
   kosong: 2,0 mm di atas courtyard, 6,0 mm di bawahnya; ke kiri dan kanan
   hanya 2,0 mm sebelum header tetangga, jadi teks di atas/bawah J3 boleh
   selebar maksimal 16,7 mm. Teks 1 mm selebar ±0,75 mm per karakter dan
   setinggi 1,3 mm per baris. Value `AD8232 GND 3V3 OUT LO- LO+ SDN`
   (30 karakter). Teks Fab `${REFERENCE}` milik footprint (sebuah
   `PCB_TEXT`, bukan field) menimpa pin. Tulis posisi, sudut, dan ukuran ref
   dan value, apa yang dilakukan pada `${REFERENCE}` itu (fungsi pcbnew yang
   dipakai dan di skrip mana), serta keluaran pemeriksa yang diharapkan.
9. Freerouting selesai dengan `"success": true`. Tulis apa yang kamu periksa
   sesudahnya dan apa yang dilakukan bila satu sambungan +3V3 belum dirute.
   Sebut juga di mana skrip rute manual disimpan.

## Rubrik (tiap butir 2 poin)

- A. Tugas 1–2: kepala diganti `(version 20250114)` dan
  `(generator_version "9.0")` + verifikasi `kicad-cli` sukses; K di
  (102; 100,8), A di (98; 100,8), langkah mencetak pad (keluaran boleh `[N]`),
  keputusan tegas rotasi 0 sehingga K di (98; 100,8), lalu pad dicetak ulang.
- B. Tugas 3: tidak memilih sendiri; bertanya ke user dengan ≥ 2 opsi
  (3V3, GPIO12, atau jumper) beserta akibat tiap opsi dan rekomendasi + alasan.
- C. Tugas 4–5: net board diganti ke `/NAMA`, pad NC `unconnected-(...)`
  dengan `{slash}`, pola netclass ikut `/`, perubahan berikutnya lewat skrip
  pcbnew (FootprintLoad, salin ref/posisi/rotasi/net) bukan sinkronisasi
  ulang, verifikasi paritas → 0; jalur dan footprint dikunci, salinan acuan,
  autoroute satu percobaan (`maxPasses`), segmen terkunci dibandingkan
  (0 hilang/berubah), segmen nol-panjang dan tak terkunci di net manual
  dihapus, zona dituang, `cek_board.py` LULUS.
- D. Tugas 6–7: 0,5 mm + clearance 0,35 mm; celah 2,54 − 1,4 = 1,14 mm <
  0,5 + 2 × 0,35 = 1,2 mm sehingga tidak muat; segmen di sela menyempit ke
  0,4 mm (0,4 + 0,7 = 1,1 ≤ 1,14) dengan segmen dipecah dan pengecualian
  dicatat di README;
  holder: rule area "dilarang footprint" berukuran holder terukur + margin
  (atau ±80 × 24 mm dengan ukuran holder dicatat belum terverifikasi /
  ditanyakan), garis + teks silkscreen, uji negatif DRC menolak footprint di
  dalam area.
- E. Tugas 8: ref `J3` di silkscreen 1,0 mm (atau 0,8 mm), sudut 0, di atas J3
  (muat di ruang 2,0 mm); value di Fab, sudut 0, di bawah J3 (sisi
  berlawanan), dikecilkan karena 30 × 0,75 × 0,8 = 18 mm > 16,7 mm: ukuran
  0,7 mm (15,75 mm) atau lebih kecil sampai ≥ 0,4 mm, dengan keputusan tertulis;
  `${REFERENCE}` dihapus dengan `Delete()` di skrip terpisah (bukan
  `SetVisible(False)`, yang tidak tersimpan); dibuktikan `cek_tata_letak.py`
  teks 0 temuan. Tugas 9: DRC `unconnected` dibaca sesudah autoroute walau
  sukses; sambungan sisa dirute manual dan dikunci; skrip rute manual di repo
  (`hardware/mainboard/tata_letak.py`), bukan scratchpad. (Tugas 9 bagian
  dari butir E; E penuh hanya bila tugas 8 dan 9 sama-sama benar.)

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-16 | sonnet | haiku | 8/10 | B: keputusan rotasi ditunda; D: jalur pengganti sinkronisasi ulang tidak disebut. Di luar rubrik: klaim memeriksa berkas tanpa akses. SKILL.md: aturan 6 putuskan rotasi saat itu, aturan 5 prosedur skrip pengganti sync, aturan 10 klaim sebatas yang dilakukan; tugas 2 minta keputusan akhir |
| 2026-10-16 | sonnet | haiku | 10/10 | Lulus. Di luar rubrik (tidak mengubah SKILL.md): klaim isi berkas yang tidak dibuka di tugas 3, urutan simpan/muat ulang sesudah Delete tidak ditulis, klaim daya backlight dari ingatan |
| 2026-10-16 | sonnet | haiku | 9/10 | SKILL.md + aturan 11–13 (teks, holder, lebar; ditangkap user), tugas 6–8 baru. E: penempatan value panjang tidak diputuskan. Di luar rubrik: holder disebut "terukur" padahal belum. SKILL.md: urutan tetap penempatan value, ukuran khas vs terukur di aturan 12 |
| 2026-10-16 | sonnet | haiku | 9/10 | E: keputusan value tidak diambil; sebab soal tanpa data ruang (tidak berjawaban pasti). Tugas 8 diberi angka ruang, rubrik E diisi jawaban pasti. SKILL.md: aturan 11 mengizinkan ubah bentuk pad footprint resmi bila lubang dan posisi tetap, dicatat di README |
| 2026-10-16 | sonnet | haiku | 10/10 | Lulus (putaran ke-3 siklus aturan 11–13). Di luar rubrik, tidak mengubah SKILL.md: DRC tanpa tuang zona di tugas 4/6/7; aturan 9 `python3` vs aturan 7 `/usr/bin/python3` (bukan pertentangan: cek_board.py tanpa pcbnew dan memanggil cek_tata_letak.py lewat /usr/bin/python3); klaim GPIO12 dari ingatan |
| 2026-10-18 | sonnet | haiku | 8/10 | Siklus aturan 8 (cek unconnected sesudah autoroute, alat di repo) dan 11 (profil JLCPCB, neck di sela pin), tugas 6 diubah, tugas 9 baru. C: prosedur FootprintLoad tidak ditulis; E: cara hapus ${REFERENCE} dan "teks 0 temuan" tidak ditulis. Soal 4 dan 8 diminta caranya secara eksplisit. SKILL.md: definisi net daya di aturan 11 |
| 2026-10-18 | sonnet | haiku | 10/10 | Lulus (putaran ke-2 siklus 18 Okt). Di luar rubrik, tidak mengubah SKILL.md: kata "terukur" sekali terselip untuk holder yang belum diukur, ukuran ref ditulis ganda (0,8 / 1 mm), hasil pemeriksa ditulis sebelum dijalankan |
