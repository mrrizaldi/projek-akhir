# Dokumen kerja lintas komponen

**Isi:** dokumen yang **masih berlaku dan berjalan**: daftar kerja, riset yang
aksinya belum diputuskan, dan rencana yang belum selesai. Dokumen di folder ini
boleh diperbarui.
**Arsip:** dokumen yang sudah selesai dipindah ke [`arsip/`](arsip/README.md)
lewat `git mv`. Isi arsip adalah catatan historis dan tidak berlaku sebagai
acuan kerja.

| Tanggal | Dokumen | Isi | Status |
|---|---|---|---|
| 2026-11-01 | [celah-target](2026-11-01-celah-target.md) | Celah terhadap target Bab 1, Bab 3, dan PRD: target yang belum diukur, target dengan cakupan sempit, temuan firmware terbuka | Daftar kerja aktif; butir dicoret saat ditutup |
| 2026-11-01 | [crosscheck-metrik-bab4](2026-11-01-crosscheck-metrik-bab4.md) | Crosscheck metrik dan cara ukur Bab 4 terhadap standar (AAMI EC57, MLPerf Tiny, IEC 60601, IETF IPPM, ITU-T G.1010/H.810), laporan rinci per kategori di subfolder | Menunggu empat keputusan user (bagian 4), lalu aksi A–D |

## Kapan dokumen dipindah ke arsip

1. Seluruh aksinya sudah dikerjakan atau ditolak user, dan hasilnya sudah
   tercatat di dokumen yang berlaku (README komponen, walkthrough, `CLAUDE.md`,
   atau buku).
2. Pindahkan dengan `git mv docs/<berkas> docs/arsip/`, hapus barisnya dari
   tabel di atas, dan tambahkan barisnya ke tabel `arsip/README.md` beserta
   status akhir.
3. Dokumen model dan hardware mengikuti pola yang sama di
   [`model/docs/`](../model/docs/README.md) dan
   [`model/docs/arsip/`](../model/docs/arsip/README.md).
