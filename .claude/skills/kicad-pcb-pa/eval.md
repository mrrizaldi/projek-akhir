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
   Tulis perbaikannya dan perintah verifikasinya.
5. Kamu baru saja merute dan mengunci jalur daya, lalu ingin Freerouting
   merute sisanya. Tulis urutan langkah sebelum dan sesudah autoroute,
   termasuk parameter autoroute dan cara membuktikan jalur manual tidak
   berubah.

## Rubrik (tiap butir 2 poin)

- A. Tugas 1: kepala diganti `(version 20250114)` dan `(generator_version "9.0")`,
  verifikasi `kicad-cli sch export netlist` (atau ERC) sukses.
- B. Tugas 2: K di (102; 100,8), A di (98; 100,8); langkah mencetak koordinat
  pad dari board sebelum merute (keluaran boleh `[N]`); keputusan tegas:
  rotasi diganti 0 sehingga K di (98; 100,8), lalu pad dicetak ulang.
- C. Tugas 3: tidak memilih sendiri; bertanya ke user dengan ≥ 2 opsi
  (3V3, GPIO12, atau jumper) beserta akibat tiap opsi dan rekomendasi + alasan.
- D. Tugas 4: net board diganti nama ke `/NAMA`, pad NC diberi net
  `unconnected-(...)` dengan `{slash}`, pola netclass ikut `/`, perubahan
  berikutnya lewat skrip pcbnew (FootprintLoad, salin ref/posisi/rotasi/net),
  bukan sinkronisasi ulang; verifikasi
  `cek_board.py` atau `kicad-cli pcb drc --schematic-parity` → 0.
- E. Tugas 5: jalur dan footprint dikunci, salinan acuan disimpan, autoroute
  satu percobaan (`maxPasses`, bukan `attempts` > 1); sesudahnya bandingkan
  segmen terkunci (0 hilang/berubah), hapus segmen nol-panjang dan tak
  terkunci di net manual, tuang zona, `cek_board.py` LULUS.

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-16 | sonnet | haiku | 8/10 | B: keputusan rotasi ditunda; D: jalur pengganti sinkronisasi ulang tidak disebut. Di luar rubrik: klaim memeriksa berkas tanpa akses. SKILL.md: aturan 6 putuskan rotasi saat itu, aturan 5 prosedur skrip pengganti sync, aturan 10 klaim sebatas yang dilakukan; tugas 2 minta keputusan akhir |
| 2026-10-16 | sonnet | haiku | 10/10 | Lulus. Di luar rubrik (tidak mengubah SKILL.md): klaim isi berkas yang tidak dibuka di tugas 3, urutan simpan/muat ulang sesudah Delete tidak ditulis, klaim daya backlight dari ingatan |
