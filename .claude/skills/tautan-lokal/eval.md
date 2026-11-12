# Eval: tautan-lokal

Penilai: model berbeda dari penulis. Skor 0-10; lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah, tanpa akses repo. Penulis tidak
menjalankan perintah: hasil yang belum diamati ditulis `[N]` atau "belum
dijalankan", bukan sebagai fakta.

## Tugas uji

1. User: "bikinin indeks rujukan, tiap rujukan ada link ke PDF yang udah
   kudownload di `laporan/pustaka/`, outputnya PDF ya". Fakta: user membuka
   dokumen di Chrome. Tulis respons pertama ke user sebelum membuat apa pun.
2. Indeks disimpan di `laporan/pustaka/indeks.html`. Tulis markup HTML yang
   dibutuhkan agar tautan ke `laporan/pustaka/tran_2025.pdf` halaman PDF
   ke-12 (nomor tercetak jurnal hlm. 541) bekerja sesuai SKILL.md.
3. Tulis urutan langkah verifikasi yang akan kamu jalankan sebelum
   menyerahkan indeks itu. Alat yang tersedia: Bash, Playwright MCP
   (`browser_navigate`, `browser_evaluate`, `browser_click`), TaskStop.
4. Semua langkah tugas 3 sudah berhasil: 12 tautan HEAD 200
   `application/pdf`, satu klik membuka `tran_2025.pdf#page=12` lewat server
   lokal. Tulis laporan akhir ke user (maksimal 6 kalimat).
5. Sebuah indeks LaTeX memakai `\href{tran_2025.pdf}{...}`. User melapor teks
   tautannya tidak bisa diklik di Chrome. Jelaskan penyebabnya dalam paling
   banyak dua kalimat.

## Rubrik (tiap butir 2 poin)

- A. Format (tugas 1): menyebut tautan ke berkas lokal dari PDF tidak jalan
  di Chrome dan merekomendasikan HTML; meminta user memilih format (tidak
  memutuskan sendiri "saya buat HTML"); perilaku HTML (bisa diklik, tab
  baru, lompat halaman) ditulis sebagai rancangan yang akan diuji, tidak
  sebagai hasil pasti; tidak mengusulkan Artifact/halaman claude.ai.
- B. Tautan (tugas 2): href relatif persis `tran_2025.pdf#page=12`; ada
  `<base target="_blank">` di `<head>` atau `target="_blank"` pada tautan;
  tidak memakai `file://`, path absolut, atau `#page=541`.
- C. Verifikasi (tugas 3): memuat kelimanya, yaitu server lokal
  `http.server` (bukan `file:`), navigasi ke halaman lewat `http://127.0.0.1`,
  cek HEAD/fetch untuk SETIAP tautan dengan status 200 dan tipe PDF, minimal
  satu klik dengan pengecekan tab baru ber-URL `#page=` sementara tab indeks
  tetap, dan menghentikan server.
- D. Laporan (tugas 4): menyebut yang terbukti (12 tautan, klik lewat server
  lokal) DAN yang belum (klik dari `file://` di Chrome user dan/atau lompatan
  halaman), meminta user mencoba satu tautan, dan tidak menulis "semua
  tautan bisa diklik" tanpa syarat; paling banyak 6 kalimat.
- E. Penyebab (tugas 5): menyebut hyperref mengubah tautan `.pdf` menjadi
  `/GoToR` (tautan ke PDF lain) DAN viewer PDF Chrome tidak menjalankannya;
  paling banyak dua kalimat.

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-11-12 | sonnet | haiku | **10/10** | LULUS putaran 1. Di luar rubrik: tugas 1 menyebut HTML "bisa diklik" sebelum diuji; tugas 1 memutuskan format sendiri padahal user meminta PDF. SKILL.md aturan 1 dipertegas (user memilih, tanpa janji bisa diklik), aturan 2 dan 4 ditambah tab baru (`<base target="_blank">`, permintaan user); rubrik A, B, C disesuaikan. Eval ulang wajib |
| 2026-11-12 | sonnet | haiku | 9/10 | A: tugas 1 menulis "tiap rujukan membuka PDF-nya di tab baru, bisa langsung ke halaman tertentu" sebagai hasil sebelum diuji; penilai mencatat aturan ambigu (frasa "bisa diklik" tidak harfiah). SKILL.md aturan 1: perilaku sebelum diuji ditulis sebagai rancangan yang akan diuji, dengan contoh; rubrik A disamakan |
| 2026-11-12 | sonnet | haiku | **10/10** | LULUS putaran 3. Tugas 1 menyerahkan pilihan format ke user dan menulis perilaku HTML sebagai rancangan yang akan diuji. Di luar rubrik: tidak ada |
