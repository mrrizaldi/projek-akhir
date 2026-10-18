---
name: kicad-pcb-pa
description: Wajib dipakai saat membuat, menyunting, merute, atau memeriksa PCB/skematik KiCad di repo PA (hardware/mainboard, berkas KiCad dari teman, server MCP kicad, skrip pcbnew, Freerouting). Keputusan desain ditanyakan dulu, format KiCad 9 dijaga, posisi pad dibaca bukan ditebak, nama net cocok dengan skematik, dan board baru dianggap selesai bila cek_board.py LULUS.
---

# KiCad PCB PA

Asal (16 Okt 2026, pembuatan `hardware/mainboard`): user menangkap bahwa
keputusan desain (katoda D1, BLK TFT, ukuran SMD, saklar daya) diisi sendiri
tanpa ditanya. Pemeriksaan mesin menangkap sisanya: skematik dari server MCP
tidak terbaca KiCad 9, rotasi 180° membalik katoda D2 sehingga VBOOST
terhubung pendek ke +5V, 117 `net_conflict` karena nama net tanpa `/`,
skrip pcbnew segfault sesudah `Remove`, dan autoroute best-of-N gagal.
Sesudah layout pertama, user menangkap tiga hal lagi: teks ref/value melintang
terhadap header dan bertumpuk, tidak ada ruang untuk holder 18650, dan jalur
0,25 mm/clearance 0,2 mm terlalu sempit dengan komponen berdempetan.

## Aturan

1. **Keputusan desain milik user.** Sebelum menempatkan komponen, tanyakan
   setiap pilihan yang tidak tertulis di `hardware/mainboard/README.md`,
   `firmware/include/perangkat.h`, atau dokumen rev di `model/docs/arsip/`:
   ke mana pin opsional disambung (BLK, SDN, CS), pull-up, posisi saklar,
   ukuran footprint pasif, jumlah pin header modul, dan perubahan topologi
   catu. Setiap pertanyaan berisi ≥ 2 opsi, akibat tiap opsi, dan
   rekomendasi beserta alasannya. Data yang tidak bisa diukur (jumlah kaki
   saklar, tegangan lampu, urutan pin modul) juga ditanyakan atau ditulis
   sebagai butir "belum terverifikasi", tidak pernah dikarang.

2. **Format KiCad 9.** KiCad terpasang 9.0.2. Skematik baru dari server MCP
   berkepala `(version 20260101) (generator_version "10.0")` dan ditolak KiCad
   9 (`Failed to load schematic`): ganti jadi `(version 20250114)` dan
   `(generator_version "9.0")`. Simbol berformat KiCad 10 (library Espressif
   terbaru): hapus `in_pos_files`, `show_name`, `do_not_autoplace`,
   `duplicate_pin_numbers_are_jumpers`, dan pindahkan `(hide yes)` milik
   property ke dalam `effects`. Berkas KiCad 10 dari teman dibaca sebagai teks
   saja. Bukti terbaca: `kicad-cli sch export netlist` dan
   `kicad-cli sym export svg` sukses.

3. **Footprint dari sumber resmi, lalu dicek fisik.** Ambil dulu dari library
   resmi pembuat (`gh api repos/espressif/kicad-libraries/...`). Lubang untuk
   pin header 0,64 mm minimal 1,0 mm (footprint Espressif memakai 0,8 mm).
   Urutan pad fisik dicocokkan dengan gambar pinout resmi lewat skrip
   (urutkan per kolom dengan `round(x)`, karena pad bisa bergeser 0,004 mm).
   Ukuran modul yang hanya dari listing penjual masuk "belum terverifikasi".

4. **Skematik lewat MCP.** Jangan memberi nama net kosong (`""` membuat label
   kosong): pin yang tidak dipakai diberi no-connect. Bila ERC mengeluh
   "does not include the symbol library", salin
   `/usr/share/kicad/template/sym-lib-table` ke `~/.config/kicad/9.0/` hanya
   bila berkas itu belum ada. Path library proyek ditulis `${KIPRJMOD}/...`.

5. **Nama net board = nama net skematik.** Sinkronisasi MCP menamai net tanpa
   `/`, sedangkan label lokal KiCad memberi `/NAMA`. Akibatnya parity
   melapor `net_conflict` dan F8 di GUI akan mengacak net. Sesudah
   sinkronisasi pertama: ganti nama net board ke `/NAMA`, beri pad NC net
   `unconnected-(REF-PIN-PadN)` dengan `/` di nama pin ditulis `{slash}`, dan
   ubah pola netclass ke `/NAMA`. Sesudah itu MCP `sync_schematic_to_board`
   tidak dipakai lagi. Setiap perubahan skematik berikutnya (komponen baru,
   footprint diganti, net pin diganti) diterapkan ke board dengan skrip
   pcbnew: `FootprintLoad` footprint baru, salin ref, value, posisi, rotasi,
   dan net per nomor pad, hapus yang lama, lalu buktikan dengan
   `--schematic-parity` = 0.

6. **Posisi pad dibaca, tidak ditebak.** Sesudah menempatkan atau memutar
   footprint, cetak koordinat dan net tiap pad sebelum merute. Rotasi 180°
   memindahkan pad 1 ke sisi seberang: `D_SMA` di rot 180 punya katoda (pad 1)
   di kanan, dan `CP_Radial` di rot 180 punya pad 2 di kiri. Bila pad jatuh di
   sisi yang salah, putuskan saat itu juga dan tulis keputusannya: ganti
   rotasi sehingga pad menghadap arah net (sebut rotasi barunya dan koordinat
   pad hasilnya), lalu cetak ulang. Jalur tidak dibelokkan mengitari komponen
   untuk menutupi rotasi yang keliru.

7. **Skrip pcbnew.** Pakai `/usr/bin/python3` (`python3` di PATH bukan Python
   sistem). Jangan `board.Remove()` lalu memakai board di skrip yang sama
   (berakhir `SwigPyObject` atau segfault). Hapus dengan `board.Delete()` di
   skrip terpisah, simpan, lalu muat ulang. Sesudah `SetNetname`, peta
   `GetNetsByName()` masih memakai nama lama, jadi ambil net dari
   `pad.GetNet()`. `kicad-cli pcb drc` tidak menuang zona: jalankan
   `pcbnew.ZONE_FILLER(b).Fill(b.Zones())` di skrip sebelum DRC.

8. **Rute manual dulu, autoroute sesudahnya.** Jalur analog dan daya dirute
   manual lalu dikunci (`SetLocked(True)` untuk jalur dan footprint), dan
   board disalin sebagai acuan. Autoroute MCP dijalankan dengan satu percobaan
   (`maxPasses`), karena `attempts` > 1 gagal menyalin SES milik root dari
   docker. Sesudahnya: bandingkan segmen terkunci dengan salinan acuan
   (harus 0 hilang/berubah), lalu hapus segmen nol-panjang dan segmen tak
   terkunci di net yang sudah dirute manual. Freerouting bisa melapor sukses
   sambil meninggalkan sambungan yang tidak dirute (18 Okt 2026: +3V3 sisi kiri
   tidak tersambung ke U1): baca `unconnected` di DRC sesudah setiap
   autoroute, dan sambungan yang tersisa dirute manual lalu dikunci.
   Alat layout (posisi, rute manual, bersih, tuang, teks) disimpan di repo
   (`hardware/mainboard/tata_letak.py`), bukan di scratchpad: scratchpad
   hilang antar-sesi dan papan ini sudah dirute ulang empat kali.

9. **Selesai = `cek_board.py` LULUS.** `python3 hardware/mainboard/cek_board.py`
   (peta pin vs netlist, +5V tidak menyentuh GPIO, ERC, DRC error,
   unconnected, paritas, lalu `cek_tata_letak.py`: lebar, courtyard, teks). Peta pin di skrip diperbarui bersamaan dengan
   perubahan pin. Jalankan juga `kicad-cli pcb drc --severity-all` dan baca
   setiap temuan. Bukti di pesan commit adalah keluaran skrip ini, ditambah
   satu uji negatif bila skrip diubah.

10. **Klaim sebatas yang dilakukan.** Jangan menulis "sudah dicek" untuk
    berkas yang tidak dibuka atau perintah yang tidak dijalankan. Yang belum
    dilakukan ditulis sebagai langkah ("baca X", "jalankan Y"), dan keluarannya
    `[N]`.

11. **Lebar dan jarak untuk pabrik, bukan batas minimum.** Profil papan PA
    untuk JLCPCB (pilihan user 18 Okt 2026): sinyal dan GND 0,5 mm, EKG
    0,6 mm, daya 1,5 mm (cabang gate dan stub di net daya ikut), clearance
    0,35 mm, via 1,2/0,6 mm (daya 1,4/0,7 mm), jarak antar-courtyard ≥ 1,0 mm.
    Jalur yang harus lewat di sela dua pin dan tidak muat boleh menyempit
    ke 0,4 mm hanya di segmen sela itu (segmen dipecah: lebar penuh, 0,4 mm di
    sela, lebar penuh); pengecualian ini dicatat di README dan diterima
    `cek_tata_letak.py` hanya dalam 1 mm dari pad U1. "Net daya" = net di
    netclass `Power` (`/+5V /VBOOST /VSYS /VSW /VCHG /VBAT_OUT /VBAT_SENSE
    /BAT+ /BAT-`), yaitu jalur arus baterai/boost; `+3V3` (keluaran regulator
    DevKit, arus beban kecil) termasuk Default 0,5 mm. Cara fabrikasi lain
    (etching sendiri) ditanyakan dulu dan angkanya ikut jawaban user. Sebelum
    menggambar jalur, hitung celah dengan lebar jalur DAN lebar pad: jalur
    lewat di antara dua pad berjarak p butuh `p − pad ≥ lebar + 2 × clearance`
    (pad bulat 1,7 mm di pitch 2,54 hanya menyisakan 0,84 mm; pad oval
    2,0 × 1,4 mm menyisakan 1,14 mm). Mengubah bentuk/ukuran pad footprint
    resmi untuk celah ini boleh tanpa bertanya selama lubang dan posisi pad
    tidak berubah dan ring ≥ 0,2 mm; perubahannya dicatat di README bagian
    footprint. Pad GND yang hanya mendapat satu spoke
    thermal disambung solid ke zona.

12. **Ruang mekanik dipesan sebelum layout.** Baterai, holder, modul yang
    berbaring di atas papan, dan konektor yang perlu dijangkau tangan
    ditanyakan dulu: jenis (berkabel atau kaki PCB), sisi papan, dan
    ukurannya. Ruangnya dipesan sebagai rule area "dilarang footprint",
    ditambah garis dan teks silkscreen, lalu dibuktikan dengan uji negatif
    (footprint yang dipindah ke dalamnya ditolak DRC). Ukuran area = ukuran
    yang diukur user + margin 1,5 mm tiap sisi. Bila ukuran belum diukur,
    tanyakan; sementara itu pakai ukuran khas + margin (holder 18650 ±77 ×
    21 mm → area 80 × 24 mm), sebut angka itu "ukuran khas, belum diukur",
    dan masukkan ke "Yang belum terverifikasi". Jangan menyebutnya ukuran
    terukur.

13. **Teks searah header, tidak bertumpuk.** Referensi di silkscreen (tinggi
    ≥ 0,8 mm) dan value di Fab, sejajar sumbu baris pin (mendatar untuk header
    mendatar, tegak untuk header tegak), di sisi yang berlawanan, dekat
    footprint-nya sendiri, tidak di atas pad, tidak keluar tepi, dan tidak
    menumpuk teks lain di silk maupun Fab. Value yang panjang diputuskan
    dengan urutan tetap ini dan keputusannya ditulis: (1) pindah ke baris
    kedua/ketiga di sisi yang sama, maksimal 4 mm dari footprint; (2) kecilkan
    sampai 0,4 mm (Fab tidak dicetak, jadi boleh di bawah 0,8 mm); (3) taruh di
    tengah badan footprint searah barisan pin. Ref silk tidak pernah di bawah
    0,8 mm; bila tidak muat searah header, putar tegak lurus dan tulis sebagai
    pengecualian beserta alasannya. Tidak ada teks yang disembunyikan
    diam-diam.
    Teks bebas footprint (`PCB_TEXT`) tidak bisa disembunyikan di KiCad 9
    (`SetVisible(False)` tidak tersimpan), jadi duplikat `${REFERENCE}`
    dihapus. `cek_tata_letak.py` memeriksa aturan 11–13.

14. **Yang tidak terbukti ditulis.** Dimensi fisik, urutan pin modul,
    perilaku rangkaian yang belum diuji di breadboard, dan tegangan komponen
    yang tidak diketahui masuk "Yang belum terverifikasi" di
    `hardware/mainboard/README.md`, dengan cara mengeceknya.
