---
name: kicad-pcb-pa
description: Lapisan khusus repo PA untuk pekerjaan PCB/skematik KiCad di hardware/mainboard. Dipakai saat membuat, menyunting, merute, atau memeriksa PCB, skematik, netlist, DRC, atau Gerber mainboard PA, saat membaca berkas KiCad kiriman teman, atau saat user mengetik "bikin PCB", "rute ulang mainboard", "cek_board", "tata_letak.py", "tuang zona", "profil JLCPCB", "lebar jalur", "autoroute gagal", "ubah pin PCB", "skematik tidak kebaca KiCad". Memuat skill user kicad-mcp-pcb lebih dulu lalu menambahkan lokasi berkas, skrip pemeriksa, profil JLCPCB, daftar net daya, dan catatan footprint papan PA. Bukan untuk firmware atau laporan.
---

# KiCad PCB PA

Muat skill user `kicad-mcp-pcb` lebih dulu; skill ini hanya menambah hal khusus repo PA.

## Dokumen yang dibaca sebelum bertanya ke user

Baca `hardware/mainboard/README.md` (peta pin, urutan pin header, catu daya, layout, netclass, footprint, daftar "Yang belum terverifikasi") dan `firmware/include/perangkat.h` (pin map tunggal firmware). Tanyakan ke user hanya pilihan yang keduanya tidak menetapkan, karena keputusan desain milik user.

## Lokasi

Semua berkas papan ada di `hardware/mainboard/`:

| Berkas | Fungsi |
|---|---|
| `mainboard.kicad_pro`, `.kicad_sch`, `.kicad_pcb` | proyek KiCad 9.0.2, netclass ada di `.kicad_pro` |
| `tata_letak.py` | alat layout, dijalankan dengan `/usr/bin/python3` dari `hardware/mainboard/` |
| `cek_board.py` | pemeriksa penentu "selesai" |
| `cek_tata_letak.py` | pemeriksa pcbnew (lebar, courtyard, teks), dipanggil `cek_board.py` |
| `ekspor_fab.sh` | zip Gerber JLCPCB |

Simpan setiap skrip layout baru sebagai perintah di `tata_letak.py`, bukan di scratchpad, karena papan ini sudah beberapa kali dirute ulang dan scratchpad hilang antar sesi.

Berkas KiCad 10 dari teman dibaca sebagai teks saja. Skematik rev2 teman (KiCad 10.0.6, PCB-nya kosong) hanya acuan rangkaian; perbedaannya terhadap mainboard ini ada di tabel README bagian "Perbedaan terhadap skematik rev2".

## Perintah `tata_letak.py`

Perintahnya `hapus`, `rute`, `bersih`, `solid`, `tuang`, `teks`, `ukiran`; urutan rute ulang penuh ada di README bagian "Mengubah desain".

Jalankan `tuang` sebagai langkah tersendiri tepat sebelum setiap `kicad-cli pcb drc`, karena `kicad-cli` tidak menuang zona:

```bash
cd hardware/mainboard
/usr/bin/python3 tata_letak.py tuang
kicad-cli pcb drc --schematic-parity --severity-all -o /tmp/drc.rpt mainboard.kicad_pcb
```

Penerapan perubahan skematik ke board lewat skrip pcbnew sesuai skill user ("Net names match the schematic"), bukan F8 dan bukan `sync_schematic_to_board`, supaya nama net tetap `/NAMA`.

## Selesai = `cek_board.py` LULUS

```bash
python3 hardware/mainboard/cek_board.py
```

Yang diperiksa: peta pin terhadap netlist (`PIN_U1` dan `PIN_LAIN` di skrip), `+5V` hanya menyentuh `U1`, `C1`, `C2`, `D2` (`BOLEH_5V`), ERC, DRC error, unconnected, paritas skematik, lalu `cek_tata_letak.py` (lebar per netclass, courtyard ≥ 1 mm, teks). Baris terakhir yang diharapkan `LULUS`; tempel keluarannya di pesan commit.

Perbarui `PIN_U1` dan `PIN_LAIN` bersamaan dengan `firmware/include/perangkat.h` dan tabel peta pin di README setiap kali pin berpindah, karena skrip keluar dengan kode 1 bila satu pin saja menyimpang dari peta. Bila `cek_board.py` atau `cek_tata_letak.py` diubah, tambahkan satu uji negatif (papan yang sengaja dirusak harus gagal).

## Profil JLCPCB: "ideal teknis"

Profil ini pilihan user: lebar dari kebutuhan arus IPC-2221, jarak dan ring dari rekomendasi JLCPCB, bukan batas minimum JLCPCB. Profil yang lebih tebal atau cara fabrikasi lain ditanyakan dulu.

| Netclass | Net | Lebar | Clearance | Via (pad/lubang) |
|---|---|---|---|---|
| `Default` | sinyal digital, `+3V3`, GND | 0,3 mm | 0,35 mm | 0,9/0,4 mm |
| `ECG` | `/ECG_*` | 0,4 mm | 0,35 mm | 0,9/0,4 mm |
| `Power` | net daya di bawah | 1,0 mm | 0,35 mm | 1,2/0,6 mm |

Net daya (netclass `Power`): `/+5V /VBOOST /VSYS /VSW /VCHG /VBAT_OUT /VBAT_SENSE /BAT+ /BAT-`. Cabang gate dan stub di net ini ikut 1,0 mm. `+3V3` (keluaran regulator DevKit, arus kecil) termasuk `Default`, jadi 0,3 mm.

Ring PTH ≥ 0,25 mm, jarak antar-courtyard ≥ 1,0 mm, silkscreen referensi ≥ 1,0 mm. Di sela dua pin satu kolom U1 (pitch 2,54 mm) jalur `+3V3` butuh celah 0,3 + 2 × 0,35 = 1,0 mm; pad U1 oval 2,0 × 1,5 mm menyisakan 1,04 mm.

## Catatan footprint dan hal yang belum terbukti

Perubahan bentuk pad footprint dicatat di `hardware/mainboard/README.md` bagian "Footprint ESP32-S3-DevKitC-1". Dimensi, urutan pin modul, ruang mekanik, dan perilaku rangkaian yang belum diuji masuk bagian "Yang belum terverifikasi" di README yang sama, beserta cara mengecek tiap butir.
