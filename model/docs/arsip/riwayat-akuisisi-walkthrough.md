# Riwayat: Walkthrough akuisisi sinyal — dari elektroda ke grafik

**Dokumen sumber:** [`akuisisi-walkthrough.md`](../akuisisi-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## 14 Sep 2026 — pin OUTPUT AD8232 GPIO4 → GPIO8
- **Perubahan:** pin OUTPUT semula GPIO4, dipindah ke GPIO8 (ADC1_CH7).
- **Alasan / bukti:** jalur GPIO4 terbukti putus; gejala `dengung50` ~930 counts (pin
  mengambang menyerap jala-jala) langsung menjadi 0 setelah pindah pin. Gejalanya
  dipertahankan di tabel troubleshooting dokumen aktif §7.

## Arti LED: clipping
- **Perubahan:** clipping semula ditandai LED merah kedip. Penanda itu dicabut; merah
  kini hanya berarti "sedang merekam", dan clipping dibaca lewat `q`/`s`.
- **Alasan / bukti:** satu warna dengan dua arti membuat merah ambigu.

## Arti LED: keadaan biru (fase kalibrasi)
- **Perubahan:** dokumen menulis "tiga keadaan" (hijau/oranye/merah). Kode saat ini
  (`perbarui_led()` di `main.cpp`) punya keadaan keempat: biru selama fase kalibrasi
  (gerbang masuk HW-6). Prosedur rekam dan tabel troubleshooting dokumen aktif
  diperbarui mengikuti kode.
- **Alasan / bukti:** gerbang kalibrasi `bab3.tex` ditambahkan bersama modul MQTT.

## 15 Sep 2026 — rekaman tubuh dan lantai derau
- **Perubahan:** satu rekaman tubuh berhasil (`20260915-1130.csv`); enam rekaman
  berikutnya mati di 40–55 counts. Variabel dicoret satu per satu (elektroda, jack,
  kabel LO, modul+kabel, penempatan LA); sisa tersangka: header modul AD8232 belum
  disolder.
- **Alasan / bukti:** dokumen aktif menyajikan rekaman acuan (§8) dan gejala lantai
  derau sebagai baris troubleshooting (§7). Log lengkap ada di
  [`riwayat-status-fase.md`](riwayat-status-fase.md) (HW-5).
