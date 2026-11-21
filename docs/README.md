# Dokumen kerja lintas komponen

**Isi:** dokumen yang **masih berlaku dan berjalan**: daftar kerja, riset yang
aksinya belum diputuskan, dan rencana yang belum selesai. Dokumen di folder ini
boleh diperbarui.
**Riwayat:** dokumen yang selesai dihapus; riwayatnya ada di git. Rencana lama ada di tag git `pra-bersih`; dokumen arsip yang dipangkas dapat dipulihkan dari induk commit `0c87f78` (`docs/arsip/`) dan `830bd3e` (`model/docs/arsip/`) dengan `git show <commit>^:<path>`.

| Tanggal | Dokumen | Isi | Status |
|---|---|---|---|
| 2026-11-01 | [celah-target](2026-11-01-celah-target.md) | Celah terhadap target Bab 1, Bab 3, dan PRD: target yang belum diukur, target dengan cakupan sempit, temuan firmware terbuka | Daftar kerja aktif; butir dicoret saat ditutup |
| 2026-11-01 | [crosscheck-metrik-bab4](2026-11-01-crosscheck-metrik-bab4.md) | Crosscheck metrik dan cara ukur Bab 4 terhadap standar (AAMI EC57, MLPerf Tiny, IEC 60601, IETF IPPM, ITU-T G.1010/H.810), laporan rinci per kategori di subfolder | A4–A8 diterapkan di `progres-pa-1`; A9, B, dan butir pipeline/daya ditunda (bagian 4) |
| 2026-11-21 | [skill-anti-slop](2026-11-21-skill-anti-slop.md) | Kandidat skill luar untuk penulisan laporan tanpa pola tulisan AI, benturannya dengan aturan repo, rencana distilasi ke `narasi-pa` | Uji coba progres-pa-1 Bab 2–4 selesai, eval skill 10/10; menunggu tinjauan user, sisa di §Sisa pekerjaan |
| 2026-11-21 | [pekerjaan-ditunda](2026-11-21-pekerjaan-ditunda.md) | Daftar tunggal pekerjaan yang belum dieksekusi dari sesi pipeline Word, anti-slop, rilis, dan skill | Berjalan |
| 2026-11-21 | [rencana-rework-skill-codebase](2026-11-21-rencana-rework-skill-codebase.md) | Rework skill (ekstraksi ke repo skill user, format eval skill-creator, validator CI) dan pembersihan docs serta kode | Gelombang 0–4 selesai; sisa di pekerjaan-ditunda |

## Kapan dokumen selesai

1. Seluruh aksinya sudah dikerjakan atau ditolak user, dan hasilnya sudah
   tercatat di dokumen yang berlaku (README komponen, walkthrough, `CLAUDE.md`,
   atau buku).
2. Pindahkan dulu fakta yang masih berlaku (lokasi data, cara memulihkan,
   nilai konfigurasi) ke README atau walkthrough komponennya.
3. Hapus berkasnya (dengan persetujuan user) dan barisnya di tabel indeks.
