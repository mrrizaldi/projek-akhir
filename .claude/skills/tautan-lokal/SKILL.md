---
name: tautan-lokal
description: Wajib dipakai saat membuat dokumen yang berisi tautan ke berkas lokal (indeks rujukan ke PDF di laporan/pustaka, daftar bukti ke rekaman/grafik, indeks berkas apa pun) untuk dibuka user. Tautan lokal dibuat di HTML, bukan PDF, relatif terhadap letak dokumen, dan diklik sungguhan sebelum diserahkan; yang tidak bisa diklik sendiri disebut belum terbukti.
---

# Dokumen bertautan ke berkas lokal

Asal aturan: 12 Nov 2026 indeks rujukan pengukuran dibuat sebagai PDF LaTeX
dengan tautan ke PDF lokal. User membukanya di Chrome dan teks tautannya
tidak bisa diklik, dua kali berturut-turut, padahal laporan akhir menyebut
tautannya sudah diperiksa. Pemeriksaannya hanya membaca anotasi di berkas,
bukan mengklik di viewer user.

## Aturan

1. **Format = HTML, bukan PDF.** Viewer PDF Chrome hanya menjalankan tautan
   `http`, `https`, dan `mailto`. Tautan ke berkas lokal dari dalam PDF mati
   di Chrome, apa pun bentuknya:
   - `\href{berkas.pdf}` dan `\href{file:...}` di hyperref otomatis menjadi
     aksi `/GoToR` (PDF ke PDF lain), yang hanya didukung Evince/Okular/Acrobat.
   - URI `file:///...` yang ditulis manual (`\pdfstartlink user{... /S/URI ...}`)
     juga diblok Chrome.
   Halaman HTML lokal yang menaut ke berkas lokal bisa diklik di Chrome, dan
   Chrome membaca `#page=N` saat membuka PDF tujuan. Kalau user meminta PDF,
   jelaskan batas ini satu kalimat, rekomendasikan HTML, lalu biarkan user
   memilih (format adalah keputusan user, jangan memutuskan sendiri).
   Jangan menyerahkan PDF bertautan lokal sambil menyebutnya bisa diklik.
   Perilaku HTML (bisa diklik, tab baru, lompat ke halaman) sebelum diuji
   ditulis sebagai rancangan yang akan diuji ("akan saya buat agar ..., lalu
   saya uji klik sebelum diserahkan"), bukan sebagai hasil ("tiap rujukan
   membuka PDF di tab baru").
2. **Tautan relatif, dokumen di folder target.** Simpan HTML di folder yang
   sama dengan berkas tujuan (indeks pustaka: `laporan/pustaka/`), lalu tulis
   `<a href="tran_2025.pdf#page=12">`. Path absolut `file:///home/...` tidak
   dipakai: rusak saat folder dipindah dan tidak bisa diuji lewat server.
   Nomor halaman yang ditaut = urutan halaman di berkas (hlm. PDF), bukan
   nomor tercetak jurnal. Pasang `<base target="_blank">` di `<head>` supaya
   setiap tautan terbuka di tab baru dan halaman indeks tidak tergantikan
   (permintaan user 12 Nov 2026).
3. **Bukan Artifact.** Halaman claude.ai tidak bisa membuka disk user, jadi
   indeks tautan lokal tidak dipublikasikan sebagai Artifact.
4. **Klik sendiri sebelum menyerahkan.** Playwright MCP memblok protokol
   `file:`, jadi uji lewat server lokal:
   1. `cd <folder dokumen> && python3 -m http.server 8765 --bind 127.0.0.1`
      (Bash `run_in_background`).
   2. `browser_navigate` ke `http://127.0.0.1:8765/<dokumen>.html`.
   3. `browser_evaluate`: `fetch(a.href, {method:'HEAD'})` untuk SETIAP
      tautan lokal; semua harus `200` dengan `content-type` yang sesuai
      (`application/pdf`).
   4. `browser_click` minimal satu tautan, lalu pastikan tab baru terbuka
      dengan URL `.../<berkas>.pdf#page=N` dan tab indeks tetap di halaman
      indeks.
   5. Hentikan server (`TaskStop`).
5. **Laporan memisahkan yang terbukti dan yang belum.** Terbukti: jumlah
   tautan dan status HEAD-nya, satu klik lewat server lokal. Belum terbukti:
   klik dari `file://` di browser user dan lompatan ke halaman tujuan.
   Minta user mengklik satu tautan. Kata "bisa diklik" tanpa syarat hanya
   boleh dipakai untuk hal yang sudah diklik.
