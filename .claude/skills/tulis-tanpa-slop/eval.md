# Eval: tulis-tanpa-slop

Penilai: model berbeda dari penulis. Skor 0-10; lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah, tanpa akses repo. Penulis tidak
menjalankan perintah. Setiap jawaban berupa kalimat atau paragraf LaTeX hasil
suntingan, lalu satu kalimat alasan.

## Tugas uji

1. Sunting kalimat ini: `DS2 tidak diberi \textit{jitter} dan karena itu
   mewakili anotasi tanpa \textit{error} segmentasi. Angka DS2 pada bab ini
   karena itu bukan data uji yang sepenuhnya belum tersentuh.`
2. Sunting paragraf ini: `Setiap rekaman DS1 ditumpuk menjadi tiga salinan,
   yaitu satu salinan bersih dan dua salinan bergeser. Lima rekaman DS1, yaitu
   101, 114, 201, 220, dan 223, dipisahkan sebagai data validasi. Pembagian
   memakai dua himpunan, yaitu DS1 dan DS2.`
3. Sunting kalimat ini: `Berdasarkan Tabel~\ref{tab:latensi} menunjukkan
   bahwa latensi rata-rata 939~ms, sehingga target 2~detik terpenuhi.`
4. Sebuah sumber anti-slop menyarankan "pakai padanan Indonesia untuk istilah
   asing dan ganti em dash dengan titik dua". Sunting kalimat ini sesuai
   SKILL.md: `Model dijalankan pada \textit{board} ESP32-S3 — hasilnya
   dikirim melalui MQTT.`
5. Sunting kalimat dari bab metode ini bila perlu: `Rekaman dibagi menjadi DS1
   dan DS2 mengikuti pembagian \textit{inter-patient} de
   Chazal~\cite{dechazal_2004}.`

## Rubrik (tiap butir 2 poin)

- A. Tugas 1: tidak ada "karena itu" di tengah klausa; tidak ada koma
  sebelum "sehingga"; "DS2", \textit{jitter}, \textit{error} tetap; makna
  (DS2 tanpa jitter, angka DS2 bukan data uji yang belum tersentuh) tetap,
  dan hubungan sebab di kalimat kedua tetap tertulis dengan konjungsi atau
  penghubung sebab.
- B. Tugas 2: paling banyak satu "yaitu"; tanpa titik dua dan titik koma;
  angka 101, 114, 201, 220, 223, "tiga", "lima" dan nama DS1/DS2 tetap
  semua; tidak menambah fakta.
- C. Tugas 3: kalimat bersubjek ("Tabel~\ref{tab:latensi} menunjukkan ..."
  atau "Berdasarkan Tabel~\ref{tab:latensi}, latensi ..."); tanpa koma
  sebelum "sehingga"; 939~ms dan 2~detik tetap; `\ref{tab:latensi}` tetap.
- D. Tugas 4: \textit{board} tetap bahasa Inggris dan miring; em dash hilang
  dan diganti konjungsi (dengan atau tanpa koma) atau kalimat baru, bukan
  titik dua; ESP32-S3
  dan MQTT tetap; alasan menyebut aturan rumah menang atas saran sumber.
- E. Tugas 5: kalimat dibiarkan persis atau hampir persis (pasif di metode
  bukan slop), `\cite{dechazal_2004}` tetap; alasan menyebut pasif sah di
  metode atau tidak ada pola.

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-11-21 | sonnet | haiku | 8/10 | C: koma sebelum sehingga dipertahankan; aturan S-KOMA-SEHINGGA dinaikkan ke kebiasaan utama dengan contoh. D: rubrik menuntut koma sebelum konjungsi, padahal "..., dan" tanpa koma sah (EYD); rubrik D dilonggarkan. Di luar rubrik: hubungan sebab hilang saat membuang "karena itu"; aturan 1 dan rubrik A ditambah |
| 2026-11-21 | sonnet | haiku | 9/10 | A: satu "karena itu" sisipan dibiarkan karena "hanya sekali"; prinsip gerombolan bertabrakan dengan aturan posisi. SKILL.md: prinsip gerombolan tidak berlaku untuk pola posisi dan galat, aturan 1 menyebut satu kemunculan pun diubah, beserta pengecualian harfiahnya |
| 2026-11-21 | sonnet | haiku | 9/10 | Putaran 3, berhenti (Aturan keras 8, skor terbaik 9/10). A: hubungan sebab di kalimat kedua dibuang dengan dalih uji hapus, padahal aturan 1 mewajibkannya tetap tertulis. Usulan: prinsip uji hapus di SKILL.md menyebut eksplisit bahwa penghubung sebab-akibat memuat informasi. Menunggu keputusan user |
| 2026-11-21 | sonnet | haiku | 9/10 | Putaran 4 (izin user). Prinsip uji hapus ditambah kalimat bahwa penghubung sebab-akibat memuat informasi. A tetap 1/2: "karena itu" di kalimat kedua dibuang dengan alasan "tidak punya sebab yang bisa disebut ulang di dekatnya", padahal sebabnya kalimat persis sebelumnya. Penulis membaca "karena itu" sebagai rujukan ke dalam kalimat, bukan ke kalimat sebelumnya. Usulan bila dilanjutkan: aturan 1 diberi contoh dua kalimat ("X. Y karena itu Z." → "X. Akibatnya, Y Z."). Berhenti, skor datar empat putaran |
