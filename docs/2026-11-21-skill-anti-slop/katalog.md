# Katalog pola tulisan AI untuk penyuntingan buku PA (riset bahan skill)

Kondisi riset: 21 Nov 2026. Semua sumber diunduh sebagai data ke
`src/<owner>__<repo>/` dan `src/wikipedia/signs.wiki`. Tidak ada skrip dari repo
sumber yang dijalankan. `scripts/periksa.py` milik naskah-id diunduh sebagai teks
(`periksa.py.txt`) hanya untuk membaca tabel regex-nya.

Kode sumber yang dipakai di seluruh dokumen:

| Kode | Sumber |
|---|---|
| BS | alvinindra/bahasa-skills (modul `bahasa-inti` dan `bahasa-peneliti`) |
| NI | nothinx/naskah-id |
| HI | adhiprib/humanizer-indonesia |
| HU | blader/humanizer (v4.0.0) |
| SS | hardikpandya/stop-slop |
| WP | Wikipedia:Signs of AI writing (revisi per Nov 2026) |
| NP | skill rumah `narasi-pa` yang sudah ada di repo (bukan sumber riset, dicantumkan agar tumpang tindih terlihat) |

Contoh kalimat Tell dan Perbaikan di bagian B ditulis dengan gaya buku PA (ECG,
ESP32-S3, TinyML). **Semua angka dan kunci `\cite` di contoh adalah ilustrasi, bukan
data repo.** Contoh perbaikan sudah mematuhi aturan rumah (tanpa titik dua, titik
koma, em dash di paragraf, istilah teknis `\textit{}`, desimal koma, `~\cite{}`).

---

## A. Profil sumber

### A1. alvinindra/bahasa-skills (BS)

- **Isi.** Paket skill penulisan bahasa Indonesia anti-slop: `bahasa-inti` (Sepuluh
  Larangan Keras L1 sampai L10, kewajiban, kaidah tersering, `frasa-terlarang.md`
  sekitar 100 frasa, `kata-baku.md`, `padanan-istilah.md`, `ejaan-eyd.md`), lalu
  modul kategori `bahasa-marketing`, `bahasa-website`, `bahasa-seo`, dan
  `bahasa-peneliti`. Folder `sumber/` mendokumentasikan rujukan riset beserta catatan
  keandalan.
- **Lisensi.** Tidak ada berkas LICENSE di repo dan API GitHub melaporkan lisensi
  kosong. Secara hukum berarti hak cipta penuh pada pemilik. Aman dijadikan rujukan
  gagasan, tidak aman disalin verbatim ke skill rumah.
- **Relevan untuk karya ilmiah.** `bahasa-peneliti/SKILL.md` (ragam resmi, kata ganti,
  kalimat efektif berprioritas data kesalahan skripsi 34 % struktur, 21 % ejaan,
  18 % diksi, larangan pembuka "era globalisasi", tabel anti-slop akademik, struktur
  IMRaD, kejujuran sitasi), `references/kalimat-akademik.md` (subjek berkata depan,
  kehematan, keparalelan, kelogisan, diksi), `references/struktur-sitasi.md` (tinjauan
  pustaka sebagai sintesis). Dari `bahasa-inti`: L1 sampai L9, `frasa-terlarang.md`
  bagian 1, 2, 3, 5, 6, 7, dan tabel kalke.
- **Catatan keandalan dari sumbernya sendiri.** `sumber/ai-slop.md` mengakui tidak ada
  daftar frasa AI Indonesia terkurasi saat riset (Agustus 2026). Daftarnya disusun dari
  (1) butir terkonfirmasi, (2) kalke daftar Inggris, (3) pola keluaran LLM yang
  dikenali. Satu-satunya penanda khas Indonesia yang tervalidasi penutur asli adalah
  "hiruk pikuk". Belum ada studi korpus kosakata berlebih untuk bahasa Indonesia.
- **Skrip.** Tidak ada skrip. Hanya `.github/workflows/release.yml` dan manifest plugin.

### A2. nothinx/naskah-id (NI)

- **Isi.** Skill penyuntingan karya ilmiah Indonesia (EYD V, KBBI) dengan kontrak
  tegas: angka, hasil, nama, dan sitasi tidak diubah, rujukan tidak dikarang, batas
  perubahan per jenis pekerjaan (koreksi, sunting, tulis ulang, tulis). Rujukan
  terpisah per masalah: `pola-ai.md` (katalog AI-01 sampai AI-19 plus pola tanpa
  kode), `kalimat-efektif.md` (KE-01 sampai KE-17, NM-01, KL-01), `ejaan-eyd-v.md`
  (EJ-01 sampai EJ-10), `istilah.md` (keputusan padanan berbasis keterpakaian
  terukur), `pertahankan.md` (konvensi yang jangan dikoreksi), `bagian-naskah.md`,
  `sitasi.md`, `singkatan.md`, `KONTRAK.md`.
- **Lisensi.** MIT (berkas LICENSE, frontmatter `license: MIT`).
- **Relevan.** Paling relevan dari semua sumber untuk genre ini. Labelnya memisahkan
  K (kaidah, wajib), G (gaya), dan AI (klise mesin, "satu kemunculan belum masalah").
  `pertahankan.md` melindungi pasif di Metode, "penelitian ini" sebagai subjek,
  istilah asing lazim bidang, hedging sah, "signifikan" statistik. `istilah.md`
  memuat data pangsa judul OpenAlex untuk bidang teknik (mikrokontroler 91 %,
  *noise* 90 %, *timer* 87 %, catu daya dan *power supply* 50:50).
- **Skrip (tidak dijalankan).** `scripts/periksa.py` (pemeriksa regex K/G/AI, banding
  angka dan sitasi asli lawan draf, `--banding`), `scripts/openalex.py` (memanggil
  OpenAlex dan Crossref lewat jaringan), `evals/jalankan.py`, `evals/banding.py`,
  `.github/workflows/periksa.yml`. `.mcp.json` mendaftarkan server MCP HTTP
  `mcp.consensus.app` dan `api.alphaxiv.org`. Tidak dipasang, tidak dipakai.

### A3. adhiprib/humanizer-indonesia (HI)

- **Isi.** Skill penyuntingan agar teks Indonesia tidak kaku, versi 1.7.2 (18 Nov
  2026). `references/id-ai-tells.md` adalah katalog tell Indonesia (A sintaksis,
  B leksikal, C kohesi, D wacana, E ambang metrik, F positif palsu, G register yang
  dikecualikan). `SKILL.md` (74 KB) berisi alur delapan langkah, Langkah 5b uji
  kalke, 5c uji personifikasi dan register, 5d fusi kalimat terfragmentasi, sebelas
  pemeriksaan wajib saat mengaudit suntingan model lain, dan "Kaidah yang sering
  terlewat". Banyak contoh berasal dari teks teknik (termal, nuklir, *machine
  learning*), jadi dekat dengan genre PA.
- **Lisensi.** MIT.
- **Relevan.** Katalog A sampai D dan F, Langkah 5b, 5c, 5d, sebelas pemeriksaan
  (angka, rujukan silang `Tabel \d+\.\d+`, sitasi, persamaan), dan kaidah
  (tanda hubung bentuk ulang, *oleh* sesudah pasif berpelaku, *Sedangkan* bukan
  pembuka kalimat, *linear*, peluluhan KTSP). Prinsip penting: "metrik itu syarat
  perlu, bukan syarat cukup" dan "tulis ulang, jangan pangkas".
- **Tidak relevan.** Preset suara pribadi penulis repo (`voice-prib-id.md`), kalibrasi
  GPTZero, bagian Detektor pihak ketiga, dan "Menghindari sterilitas" (repo sendiri
  menyatakan teks teknis yang netral adalah suara manusia yang benar).
- **Skrip (tidak dijalankan).** `scripts/metrik.py` (metrik gaya stdlib, ambang
  dikalibrasi ke korpus pemilik repo), `portable/buat_paket.py` (pembuat paket untuk
  ChatGPT/Gemini).

### A4. blader/humanizer (HU)

- **Isi.** Skill bahasa Inggris v4.0.0, 26 pola dalam enam kelompok (A staging, B ritme
  menurut aturan, C inflasi dan otoritas pinjaman, D format menurut aturan, E sisa
  obrolan dan draf, F pembaca yang salah). Diturunkan dari WP. Setiap pola punya tanda
  kekuatan ("§1 sampai §5 cukup satu kali", "*weak alone*").
- **Lisensi.** MIT.
- **Relevan.** Kerangka penjelasan "mengapa" (model memilih opsi yang cocok untuk
  pembaca terluas), §1 Not X but Y, §5 berdebat dengan lawan yang tidak ada, §6 triad,
  §9 qualifier bertumpuk, §12 kosakata AI, §13 signifikansi digelembungkan, §14
  asosiasi kabur, §15 frasa *-ing* dangkal, §17 otoritas pinjaman, §18 menghindari
  *is/has*, §19 bold dekoratif, §24 heading diulang di kalimat pertama, §25 menulis
  tentang dokumen. Bagian "When not to act" (cari gerombolan tell, bukan tell tunggal).
- **Skrip.** `scripts/validate-package.py` (validasi paket), `package.json`. Tidak
  dijalankan.

### A5. hardikpandya/stop-slop (SS)

- **Isi.** Skill pendek bahasa Inggris untuk prosa esai/blog: delapan aturan inti,
  `phrases.md` (pembuka basa-basi, penopang penekanan, jargon bisnis, adverbia,
  meta-komentar), `structures.md` (kontras biner, daftar negatif, fragmentasi
  dramatis, setup retoris, *false agency*, narator berjarak, pasif, pembuka *Wh-*),
  skor lima dimensi (di bawah 35/50 direvisi).
- **Lisensi.** MIT.
- **Relevan.** Kontras biner dan *false agency* (personifikasi), meta-komentar,
  deklaratif kabur ("implikasinya signifikan"), *lazy extremes*. Sebagian besar sisanya
  bertentangan dengan register skripsi (lihat D).
- **Skrip.** Tidak ada.

### A6. Wikipedia:Signs of AI writing (WP)

- **Isi.** Halaman panduan WikiProject AI Cleanup (`action=raw`, sekitar 183 KB).
  Kelompok Content (signifikansi dan warisan digelembungkan, analisis dangkal *-ing*,
  asosiasi kabur, atribusi kabur, kesimpulan "tantangan dan prospek"), Language
  (kosakata AI per era model, penghindaran kopula, paralelisme negatif, *rule of
  three*), Style (Title Case, bold, daftar berlabel, emoji, kutip keriting),
  Citations (DOI tak valid, DOI menuju artikel lain, buku tanpa halaman), Signs of
  human writing, Ineffective indicators, Historical indicators (em dash 2022 sampai
  Sep 2026, ringkasan bagian, keragaman leksikal).
- **Lisensi.** CC BY-SA 4.0 (teks Wikipedia). Kutipan verbatim di skill rumah wajib
  atribusi dan berbagi serupa. Parafrase gagasan aman.
- **Relevan.** Peringatan metodologis paling kuat: detektor dan penilaian manusia
  hampir setara tebakan acak, tata bahasa sempurna dan prosa formal bukan penanda,
  transisi tunggal bukan penanda kuat. Catatan baru: model terbaru (Sep 2026 ke atas)
  dikunci tidak memakai em dash, dan akibatnya teks yang hanya memakai koma dan titik
  mulai menjadi penanda tersendiri (ditandai `{{cn}}`, belum bersumber).
- **Skrip.** Tidak ada.

---

## B. Katalog pola

Format tiap butir: **Tell** (contoh), **Mengapa**, **Perbaikan** (contoh), **Sumber**,
**Mesin?** (ya = regex atau daftar kata, sertakan pola; tidak = perlu penilaian).
Regex ditulis gaya Python, `(?i)` berarti tanpa membedakan kapital. Pemeriksa sebaiknya
membuang komentar `%`, argumen `\cite{}`, `\ref{}`, `\label{}`, lingkungan `table`,
`figure`, `equation`, dan `\caption` sebelum mencocokkan (inferensi).

Prinsip umum dari semua sumber: satu kemunculan biasanya belum masalah, gerombolan yang
masalah (HU "When not to act", HI "Cari gerombolan tell", NI "satu kemunculan saja
biasanya belum masalah", WP "Ineffective indicators").

### B1. Tingkat kata dan frasa

**B1.1 Pembuka kosmik atau zaman**
- Tell: "Di era digital yang berkembang pesat ini, teknologi kesehatan memegang peranan
  yang sangat penting dalam kehidupan manusia."
- Mengapa: kalimat bisa menempel pada topik apa pun, jadi tidak memberi informasi.
  Penelaah melewatkannya. Latar belakang skripsi Indonesia penuh pola ini (BS
  mencantumkan bukti repositori skripsi).
- Perbaikan: "Rekaman Holter hanya mencakup 24 sampai 48 jam~\cite{holter}, sehingga
  aritmia yang muncul jarang dapat terlewat." Bila fakta pengganti tidak ada di naskah,
  jangan mengarang, tandai `\PlaceholderData{...}`.
- Sumber: BS L1, `frasa-terlarang` §1, `bahasa-peneliti`; NI AI-01, AI-02; HI D1;
  SS ("In today's", "In a world where").
- Mesin: ya.
  `(?i)\bdi (era|zaman|tengah) (digital|modern|globalisasi|serba|teknologi|pesatnya|derasnya|revolusi)`
  · `(?i)\bseiring (dengan )?(perkembangan|kemajuan|berjalannya) (zaman|teknologi|waktu)`
  · `(?i)\bdewasa ini\b` · `(?i)\bdalam dunia \w+ yang (terus|semakin) berkembang`
  · `(?i)\bdalam beberapa tahun terakhir\b` (lemah, butuh angka di kalimat yang sama).

**B1.2 Penegas tanpa isi**
- Tell: "Tidak dapat dipungkiri bahwa pemantauan jantung kontinu sangat dibutuhkan."
- Mengapa: penegas menggantikan bukti. Bila klaim memang mapan, cukup rujukannya.
- Perbaikan: "Pemantauan jantung kontinu dibutuhkan karena sebagian aritmia muncul
  sesekali~\cite{kunci}."
- Sumber: BS L1; NI AI-03, AI-04; HI B2, D1.
- Mesin: ya. `(?i)\bt(idak|ak) (dapat|bisa) dipungkiri\b` · `(?i)\bseperti yang (kita )?(ketahui|diketahui)( bersama)?\b` · `(?i)\bsudah menjadi rahasia umum\b` · `(?i)\bsebagaimana kita ketahui\b`.

**B1.3 Kalimat meta dan nada ceramah**
- Tell: "Perlu diketahui bahwa sinyal ECG sangat rentan terhadap *noise*."
- Mengapa: kalimat tentang tulisan atau ajakan bicara, bukan tentang topik. Uji hapus,
  bila tidak ada informasi hilang, hapus.
- Perbaikan: "Sinyal ECG rentan terhadap \textit{noise} gerak dan \textit{baseline
  wander}."
- Sumber: BS L7; NI AI-11; HI 5c.3; HU §4, §25; SS meta-commentary.
- Mesin: ya. `(?i)\b(perlu|penting untuk) (diketahui|dicatat|dipahami|diingat|diperhatikan)( bahwa)?\b` · `(?i)\bpatut (dicatat|diperhatikan)\b` · `(?i)\bmari kita\b` · `(?i)\bperhatikan bahwa\b` · `(?i)\byang menarik(nya)? adalah\b`.

**B1.4 Kosakata slop dan kata bergengsi tanpa fungsi**
- Tell: "Penelitian ini menyelami lanskap TinyML yang krusial untuk menghadirkan solusi
  holistik dan komprehensif."
- Mengapa: kata yang frekuensinya melonjak karena mesin, bukan karena penutur. Di bahasa
  Inggris terbukti lewat studi korpus (BS mengutip Kobak dkk. 2025, *delves* rasio
  28,0). Versi Indonesianya adalah kalke kualitatif (BS mengakui ini).
- Perbaikan: "Penelitian ini menerapkan TinyML pada ESP32-S3 untuk mengklasifikasi
  aritmia langsung di perangkat."
- Sumber: BS L5 dan `frasa-terlarang` §6; HI B2, B3; HU §12; WP AI vocabulary.
- Mesin: ya, daftar kata di C, tetapi butuh penilaian makna harfiah atau teknis
  (*mengoptimalkan* sah bila memang ada optimasi, *tangguh* atau *robust* sah sebagai
  istilah teknis menurut HU §12, *mengimplementasikan* lazim di teknik walau HI B3
  menandainya).

**B1.5 Penguat kosong dan klaim digelembungkan**
- Tell: "Mikrokontroler memegang peranan yang sangat krusial dan menjadi kunci utama
  keberhasilan sistem."
- Mengapa: kata sifat menggantikan bukti. Penelaah bertanya "krusial dibanding apa".
- Perbaikan: "Mikrokontroler menjalankan prapemrosesan, inferensi, dan pengiriman data
  dalam satu siklus 2~detik." (contoh triplet ini sah karena tiga tugas nyata, lihat
  B2.3).
- Sumber: BS `bahasa-peneliti` tabel anti-slop; NI AI-07, AI-09; HI B2; HU §13;
  WP undue emphasis; SS vague declaratives; NP aturan 4.
- Mesin: ya. `(?i)\bmemegang peranan (yang )?(sangat )?(penting|krusial|vital|sentral|strategis)` · `(?i)\bberperan (sangat )?(vital|krusial)\b` · `(?i)\bmenjadi (kunci utama|faktor kunci)\b` · `(?i)\btak lepas dari\b|\btidak (dapat )?dipisahkan dari\b` · `(?i)\bsolusi (yang )?(inovatif|revolusioner|tepat guna)\b` · `(?i)\bsangat (efektif dan efisien|luar biasa)\b`.

**B1.6 "Signifikan" tanpa uji statistik**
- Tell: "Kuantisasi INT8 menurunkan akurasi secara tidak signifikan."
- Mengapa: dalam naskah kuantitatif "signifikan" bermakna statistik dan tidak bertingkat.
- Perbaikan: "Kuantisasi INT8 menurunkan akurasi 0,4 poin persentase, di bawah ambang
  1 poin yang ditetapkan."
- Sumber: BS; NI AI-12, `pertahankan.md`; HI B3; NP aturan 4.
- Mesin: ya untuk penandaan. `(?i)\bsangat signifikan\b` (pasti salah) · `(?i)\bsignifikan\b` tanpa `p\s*[<=>]` atau nama uji di kalimat yang sama (tinjau).

**B1.7 Kata mutlak**
- Tell: "Sistem ini selalu mampu mendeteksi aritmia secara pasti."
- Mengapa: klaim mutlak tanpa data di seluruh lingkupnya.
- Perbaikan: "Sistem mendeteksi 97,1 % detak aritmia pada data uji MIT-BIH."
- Sumber: BS diksi; HI B5; SS lazy extremes; NP aturan 4.
- Mesin: ya. `(?i)\b(pasti|selalu|tidak pernah|menjamin|dijamin|sempurna|tanpa cacat|tidak diragukan lagi|semua orang)\b`.

**B1.8 Transisi dan konektor klise berulang**
- Tell: "Selain itu, ... Oleh karena itu, ... Di sisi lain, ... Dengan demikian, ..."
  di awal hampir setiap kalimat atau paragraf.
- Mengapa: konektor yang terus muncul kehilangan fungsi. Bahasa Indonesia menyambung
  lewat pengulangan kata kunci dan klitik *-nya* (HI C1). Peringatan HI: suntingan yang
  membuang hampir semua penghubung justru terbaca lebih AI, jadi yang ditindak adalah
  kepadatan, bukan keberadaan.
- Perbaikan: "Bufer menampung 2.500 sampel. Isinya dikirim saat penuh, sehingga
  pengiriman tidak memblok akuisisi."
- Sumber: BS L6 (tiap transisi maksimal sekali per teks, tidak dua paragraf beruntun);
  NI AI-16, AI-17, AI-19 (ambang 3 dan 2 kali); HI C1 (lebih dari 3 per 100 kata atau
  lebih dari 50 % paragraf dibuka konektor); HI 5c.3 (*Konsekuensinya*); WP (transisi
  tunggal bukan penanda kuat); NP aturan 8 (rotasi lima jenis pembuka).
- Mesin: ya, hitungan. Daftar: `Selain itu|Tidak hanya itu|Terlebih lagi|Lebih lanjut|Tak kalah penting|Namun demikian|Oleh karena itu|Oleh sebab itu|Dengan demikian|Di sisi lain|Sementara itu|Selanjutnya|Secara keseluruhan|Pada akhirnya|Dengan kata lain|Konsekuensinya` di awal kalimat. Ambang usulan (inferensi, gabungan HI dan NI): lebih dari 3 per 100 kata, atau satu konektor yang sama lebih dari 2 kali per subbab, atau dua paragraf beruntun dibuka konektor.

**B1.9 "Hal ini" dan penunjuk kabur**
- Tell: "Akurasi turun pada data sinyal tubuh. Hal ini disebabkan oleh *noise* gerak."
- Mengapa: pembaca harus menebak apa yang ditunjuk.
- Perbaikan: "Akurasi turun pada data sinyal tubuh. Penurunan tersebut berasal dari
  \textit{noise} gerak."
- Sumber: NI AI-15 (ambang 3); HI A5 contoh; NP aturan 8.
- Mesin: ya. `(?i)\bhal (ini|tersebut)\b` hitung, tandai bila 3 atau lebih per subbab.

**B1.10 Kata payung kosong**
- Tell: "Kinerja model dipengaruhi berbagai aspek dan faktor-faktor tertentu."
- Mengapa: menunda isi, variabelnya tidak disebut.
- Perbaikan: "Kinerja model dipengaruhi panjang \textit{window}, kuantisasi, dan
  galat penempatan R-\textit{peak}."
- Sumber: NI pola "Kata payung kosong"; BS (berbagai macam).
- Mesin: ya. `(?i)\bberbagai (aspek|faktor|bidang|kalangan|hal|dimensi)\b` · `(?i)\bfaktor-faktor tertentu\b` · `(?i)\bperan strategis\b`.

**B1.11 Atribusi kabur**
- Tell: "Banyak penelitian menunjukkan bahwa CNN satu dimensi unggul untuk ECG."
- Mengapa: otoritas tanpa nama menopang klaim. WP juga mencatat penggelembungan jumlah
  sumber (satu sumber ditulis "banyak penelitian").
- Perbaikan: "CNN satu dimensi mencapai akurasi di atas 95 % pada MIT-BIH~\cite{a,b}."
  Bila rujukan belum ada, tandai, jangan mengarang.
- Sumber: BS L8; NI; HI B5; HU §17; WP vague attributions.
- Mesin: ya. `(?i)\b(banyak|sejumlah|berbagai|beberapa) (penelitian|studi|peneliti|ahli|literatur)\b|\bpara ahli\b` tanpa `\cite` di kalimat yang sama.

**B1.12 Penutup ritual**
- Tell: "Dengan demikian dapat disimpulkan bahwa sistem yang dirancang sangat penting
  bagi kesehatan masyarakat."
- Mengapa: paragraf ditutup dengan mengulang isinya atau dengan pujian kosong.
- Perbaikan: hapus kalimatnya bila paragraf sudah memuat temuan, atau tutup dengan
  konsekuensi konkret "Latensi 1,2~detik ini masih di bawah batas peringatan 5~detik."
- Sumber: BS L2, `frasa-terlarang` §3; NI AI-18, KE (Dengan demikian dapat disimpulkan);
  HI D2; HU §2, §13; WP section summaries.
- Mesin: ya. `(?i)\bdengan demikian,? dapat disimpulkan( bahwa)?\b` · `(?i)\bsecara keseluruhan\b` · `(?i)\bdemikianlah\b` · `(?i)\bsebagai (kesimpulan|penutup)\b` · `(?i)\bmasa depan \w+ (terlihat )?(sangat )?menjanjikan\b` · `(?i)\bsemoga\b`.

**B1.13 Residu chatbot dan jejak alat**
- Tell: "Tentu, berikut revisi subbab pengujian latensi." atau `【4†source】`,
  `oaicite`, `[cite: 1]` yang ikut tersalin.
- Mengapa: sisa percakapan, tanda paling jelas dan paling mudah terlewat (HU §22).
- Perbaikan: hapus pembungkus, pertahankan isinya.
- Sumber: BS `frasa-terlarang` §7; HI D11; HU §22, §23; WP collaborative communication,
  phrasal templates.
- Mesin: ya. `(?i)\b(tentu|baik),? berikut\b` · `(?i)\bsemoga (membantu|bermanfaat)\b` · `(?i)\bjangan ragu untuk\b` · `contentReference|oaicite|turn0search|\[cite:\s*\d+\]|【|】` · placeholder `\[(Nama|Tanggal|Tahun|NAMA)[^\]]*\]`.

**B1.14 Pleonasme**
- Tell: "Data adalah merupakan hasil rekaman yang disebabkan karena kebutuhan uji."
- Mengapa: kaidah, bukan khas AI, tetapi sering menyertai prosa mesin dan terjemahan.
- Perbaikan: "Data ini hasil rekaman untuk kebutuhan uji."
- Sumber: NI KE-02 sampai KE-09; BS kehematan; HI B1.
- Mesin: ya (regex NI). `(?i)\badalah merupakan\b` · `(?i)\b(agar supaya|demi untuk|sejak dari)\b` · `(?i)\bsangat\s+\w+\s+sekali\b` · `(?i)\b(para|banyak|berbagai|beberapa)\s+(\w+)-\2\b` · `(?i)\bberbagai macam\b` · `(?i)\b(naik ke atas|turun ke bawah|mundur ke belakang|maju ke depan)\b` · `(?i)\bdisebabkan karena\b` · `(?i)\bdalam rangka untuk\b` · `(?i)\bberdasarkan (pada|kepada)\b` · `(?i)\bseperti\b[^.;]{1,80}?\b(dan lain-lain|dll\.?|dan sebagainya|dsb\.?)`.

### B2. Tingkat kalimat

**B2.1 Paralelisme negatif dan kontras formulaik**
- Tell: "Sistem ini tidak hanya mendeteksi aritmia, tetapi juga menghadirkan pemantauan
  yang komprehensif." atau "Edge computing bukan lagi pilihan, melainkan keharusan."
- Mengapa: separuh negatif menyebut hal yang tidak pernah diklaim siapa pun, sehingga
  separuh positif terdengar lebih besar tanpa menambah klaim. Pola AI nomor satu
  menurut BS dan HU.
- Perbaikan: "Sistem mendeteksi aritmia di perangkat dan mengirim ringkasannya ke
  \textit{dashboard}."
- Catatan: NI menegaskan "bukan hanya ..., tetapi juga ..." adalah konjungsi baku. Yang
  ditindak pemakaian berulang atau separuh negatif yang kosong.
- Sumber: BS L3; NI AI-10, `pertahankan.md`; HI D7; HU §1; SS binary contrasts; WP
  negative parallelisms.
- Mesin: ya. `(?i)\b(bukan|tidak) (hanya|sekadar|cuma)\b[^.]{1,80}?\b(tetapi|namun|melainkan) (juga)?\b` · `(?i)\blebih dari sekadar\b` · `(?i)\bbukan lagi\b[^.]{1,40}?\bmelainkan\b` · `(?i)\bbukan tentang\b[^.]{1,60}?\bmelainkan\b`.

**B2.2 Penyangkalan antisipatif (berdebat dengan lawan yang tidak ada)**
- Tell: "Akurasi model mencapai 98 %. Ini bukan berarti sistem siap dipakai di klinik."
- Mengapa: menyangkal kesimpulan yang tidak diajukan pembaca. HI menilai ini slop paling
  mudah dikenali, sasaran nol per dokumen.
- Perbaikan: "Akurasi model 98 % diukur pada data MIT-BIH, sedangkan validasi klinis
  belum dilakukan."
- Sumber: HI D7, 5c.4; HU §5; SS ("doesn't mean X").
- Mesin: ya. `(?i)\b(ini|hal ini|itu)? ?bukan berarti\b` · `(?i),\s*bukan berarti\b`. Kecualikan "tidak berarti" dalam makna statistik.

**B2.3 Triplet (rule of three)**
- Tell: "Sistem yang dirancang bersifat efektif, efisien, dan andal."
- Mengapa: tiga sifat terdengar lengkap tetapi jarang dibuktikan satu per satu.
- Perbaikan: "Sistem mengonsumsi 180~mA saat inferensi dan bertahan 9~jam dengan
  baterai 2.000~mAh." Tiga butir yang semuanya bermakna (tiga metrik, tiga kelas) tetap
  sah. HI memberi empat tindakan (buang butir tanpa informasi, nyatakan hierarki
  tersembunyi, pindahkan butir berbeda hubungan ke kalimat sendiri, pecah kompetensi
  gabungan) dan patokan tentatif sekitar 1,5 triplet per 1.000 kata. Triplet dalam
  kurung tetap triplet.
- Sumber: BS L4; NI; HI D3; HU §6; SS; WP rule of three.
- Mesin: sebagian. Heuristik `\b(\w+), (\w+),? dan (\w+)\b` dengan ketiganya kata sifat
  dari daftar (efektif, efisien, andal, akurat, cepat, tepat, aman, nyaman, murah,
  inovatif, optimal, terjangkau, berkelanjutan), hitung kepadatan per 1.000 kata.
  Keputusan tetap penilaian.

**B2.4 Subjek hilang karena kata depan**
- Tell: "Berdasarkan Tabel~4.2 menunjukkan bahwa latensi rata-rata 1,2~detik." atau
  "Pada Gambar~3.5 memperlihatkan alur prapemrosesan."
- Mengapa: kata depan mengubah calon subjek menjadi keterangan, kalimat tidak bersubjek.
  Kesalahan struktur adalah kesalahan terbesar skripsi (34 %).
- Perbaikan: "Tabel~4.2 menunjukkan latensi rata-rata 1,2~detik." atau "Berdasarkan
  Tabel~4.2, latensi rata-rata 1,2~detik."
- Sumber: BS `kalimat-akademik` §1; NI KE-01; HI A6. Pola "Berdasarkan Tabel" juga
  dibatasi NP aturan 2.
- Mesin: ya (regex NI KE-01, disesuaikan untuk awal kalimat).
  `(?:^|(?<=[.!?])\s+)(?:Dari|Dalam|Pada|Bagi|Menurut|Berdasarkan)\s(?:(?!\b(?:penulis|peneliti)\b)[^.?!,;:]){1,60}?\s(?:menunjukkan|membahas|memperlihatkan|menjelaskan|mengatakan|menyatakan|menggambarkan|menyajikan|menyimpulkan|membuktikan)\b`.

**B2.5 Konjungsi berpasangan**
- Tell: "Meskipun akurasinya tinggi, tetapi galat masih muncul pada kelas minoritas."
  atau "Berdasarkan uraian tersebut, maka diperlukan sistem pemantauan kontinu."
- Mengapa: dua konjungsi untuk satu hubungan. Kaidah, sering muncul pada kalke.
- Perbaikan: "Meskipun akurasinya tinggi, galat masih muncul pada kelas minoritas."
- Sumber: BS; NI KE-14, KE-15; HI A7.
- Mesin: ya. `(?i)\b(meskipun|walaupun|walau|biarpun|kendatipun)\b[^.;]{1,120}?,\s*(tetapi|namun)\b` · `(?:^|(?<=[.!?])\s+)(Karena|Sebab|Oleh karena|Berdasarkan|Mengingat)\b[^.;]{1,120}?,\s*maka\b`.

**B2.6 "Sehingga" dan "Sedangkan" sebagai pembuka kalimat, koma sebelum "sehingga"**
- Tell: "Bufer penuh dalam 10~detik. Sehingga data harus segera dikirim."
- Mengapa: keduanya konjungsi intrakalimat. EYD V tanda koma kaidah 4 (koma tidak
  dipakai bila induk mendahului anak kalimat).
- Perbaikan: "Bufer penuh dalam 10~detik sehingga datanya harus segera dikirim." atau
  "Akibatnya, data harus segera dikirim."
- Sumber: NI KE-16, EJ-10; HI kaidah *Sedangkan*; NP aturan 5 (batas "sehingga").
- Mesin: ya. `(?:^|(?<=[.!?])\s+)(Sehingga|Sedangkan)\b` · `,\s+sehingga\b`.

**B2.7 Kopula dihindari atau kopula default**
- Tell (dihindari): "ESP32-S3 berperan sebagai otak dari keseluruhan sistem." Tell
  (default): setiap paragraf dibuka "X merupakan ...".
- Mengapa: model mengganti "adalah" dan "punya" dengan "berperan sebagai, hadir sebagai,
  menawarkan, dilengkapi dengan" (WP mencatat penurunan lebih dari 10 % *is/are* di
  tulisan akademik 2023). Sebaliknya HI A5 mencatat *merupakan* sebagai kopula default
  model Indonesia.
- Perbaikan: "ESP32-S3 adalah pengendali utama sistem." Untuk definisi sejati
  *merupakan* atau *adalah* tetap sah (HI F5).
- Sumber: BS `frasa-terlarang` §5; HI A5; HU §18; WP copulatives.
- Mesin: sebagian. `(?i)\b(berperan|bertindak|hadir|berdiri) sebagai\b|\bmenjadi wadah bagi\b` · hitung paragraf yang kalimat pertamanya memuat `\bmerupakan\b` (tinjau bila lebih dari separuh).

**B2.8 Nominalisasi dan verba ringan**
- Tell: "Peneliti melakukan pengukuran terhadap arus yang mengalami peningkatan sebesar
  12 %."
- Mengapa: penyebab kekakuan nomor satu menurut HI. Bukan larangan mutlak di ragam
  ilmiah (BS, NI) bila nomina memang pokok bahasan.
- Perbaikan: "Arus terukur naik 12 %."
- Sumber: BS kewajiban 3, `kalimat-akademik` §2; NI NM-01; HI A1 (ambang lebih dari 1
  per 100 kata).
- Mesin: ya. `(?i)\b(melakukan|mengalami|memberikan|mengadakan|melaksanakan)\s+(pe\w{3,}an|ke\w{3,}an)\b` · `(?i)\bmemberikan (pengaruh|kontribusi) terhadap\b` · `(?i)\btelah dilakukan pe\w+an terhadap\b`.

**B2.9 Pasif refleks bertumpuk**
- Tell: "Pengujian dilakukan dengan menggunakan board. Hasil diperoleh setelah
  pengujian dilakukan. Grafik ditampilkan pada Gambar~4.1."
- Mengapa: pasif sah di Metode dan Hasil (NI, HI F1), yang jadi tell adalah tumpukan
  *dilakukan, diperoleh, ditampilkan* dan pasif plus nominalisasi.
- Perbaikan: "Pengujian memakai \textit{board} N16R8, dan hasilnya tersaji pada
  Gambar~4.1."
- Sumber: HI A2 (rasio pasif lebih dari 60 % di luar Metode); NI pasif bertumpuk.
- Mesin: sebagian. Hitung `(?i)\bdi\w+kan\b|\bdi\w+i\b` per kalimat, tandai paragraf
  dengan `\bdilakukan\b` 2 kali atau lebih (ambang inferensi).

**B2.10 Klausa ekor penafsiran**
- Tell: "Latensi inferensi 38~ms, yang menunjukkan keandalan sistem dalam pemantauan
  waktu nyata."
- Mengapa: padanan frasa *-ing* Inggris yang menempelkan makna atau signifikansi pada
  fakta sederhana tanpa dasar.
- Perbaikan: "Latensi inferensi 38~ms, jauh di bawah periode \textit{window} 2~detik."
- Sumber: BS `frasa-terlarang` §5 (klausa ekor); HU §15; WP superficial analyses.
- Mesin: sebagian. `(?i),\s*(yang )?(menunjukkan|mencerminkan|menegaskan|menandakan|menggarisbawahi|menyoroti|menjadikannya)\b` lalu tinjau apakah yang menyusul fakta atau penilaian.

**B2.11 Pembuka kalimat monoton dan penanda arah**
- Tell: "Hasilnya jelas." "Pertanyaannya sederhana." "Kemudian ada tantangan konsumsi
  daya." diulang di beberapa subbab.
- Mengapa: kalimat yang hanya mengumumkan topik atau memanggungkan poin. Sumber kalimat
  AI terbanyak pada uji HI.
- Perbaikan: satukan dengan fakta pertama, "Konsumsi daya menjadi kendala karena
  modul WiFi menarik arus puncak 310~mA."
- Sumber: HI 5c.3, 5c.5, D8; HU §4, §7; SS throat-clearing.
- Mesin: sebagian. Daftar dari HI: `Pertanyaannya sederhana|Gagasannya sederhana|Hasilnya tegas|Prosedurnya begini|Cara membacanya begini|Mari kita lihat|Perhatikan bahwa|Tiga hal langsung terlihat|Konsekuensinya,|Di situlah`. Pembuka berulang dapat dihitung (tiga kata pertama kalimat yang sama lebih dari 2 kali per bab). Penanda arah umum perlu penilaian.

**B2.12 Ritme seragam atau terfragmentasi**
- Tell: deret kalimat 20 sampai 28 kata berpola sama, atau deret kalimat pendek satu
  klausa.
- Mengapa: model cenderung ritme datar. HI menemukan kedua arah sama kentaranya.
- Perbaikan: kalimat temuan pendek, sebab-akibat lebih panjang, gabungkan fragmen dengan
  konjungsi bermakna (*karena, sehingga, sedangkan, meskipun*), bukan koma dan *dan*.
- Sumber: BS kewajiban 5; NI KL-01 (lebih dari 35 kata); HI A4 (rerata lebih dari 24,
  simpangan baku kurang dari 6), 5d (rerata kurang dari 16 dan lebih dari 30 % kalimat
  10 kata ke bawah); HU §2; SS; NP aturan 5 (15 sampai 30 kata).
- Mesin: ya (metrik panjang kalimat per paragraf dan per subbab).

**B2.13 Fragmen dramatis dan penutup satu baris**
- Tell: "Hasilnya? Sangat memuaskan." atau "Sederhana, tetapi efektif."
- Mengapa: meminta pembaca berhenti pada klaim alih-alih menambah fakta.
- Perbaikan: "Seluruh 12 skenario uji memenuhi target latensi."
- Sumber: HU §2, §3; SS dramatic fragmentation, rhetorical setups.
- Mesin: sebagian. Kalimat kurang dari 5 kata di akhir paragraf, atau tanda `?` di badan
  paragraf (lihat B3.14).

**B2.14 Modalitas bertumpuk dan derajat kepastian bergeser**
- Tell: "Penambahan filter mungkin dapat berpotensi meningkatkan akurasi." atau
  sebaliknya "Hasil ini membuktikan bahwa \textit{jitter} menyebabkan kenaikan F1."
- Mengapa: satu klausa cukup satu penanda ketidakpastian. Penyuntingan tidak boleh
  menggeser jenjang *menunjukkan* (fakta), *mengindikasikan* (inferensi), *diduga*
  (hipotesis) ke arah mana pun (HI B4).
- Perbaikan: "Penambahan filter berpotensi meningkatkan akurasi." · "Pada tiga
  \textit{seed}, \textit{jitter} diikuti kenaikan F1 sebesar 0,012."
- Sumber: BS L8, `kalimat-akademik` §5; NI KK-01, `pertahankan.md` hedging sah;
  HI B4; HU §9; NP aturan 4.
- Mesin: ya untuk penandaan. `(?i)\b(mungkin|dapat|bisa|cenderung|berpotensi|kemungkinan|diduga)\s+(mungkin|dapat|bisa|cenderung|berpotensi|kemungkinan)\b` · `(?i)\bmembuktikan\b` (cek kekuatan klaim).

**B2.15 Rantai "yang"**
- Tell: "Sistem yang dirancang yang memakai sensor yang dipasang pada dada yang ..."
- Mengapa: klausa relatif bertumpuk menghilangkan induk kalimat.
- Perbaikan: pecah menjadi dua kalimat.
- Sumber: NI pola Rantai "yang".
- Mesin: ya. Tiga `\byang\b` atau lebih dalam jendela 15 kata tanpa koma.

**B2.16 Personifikasi benda mati (false agency)**
- Tell: "Model cukup cerdas untuk mengenali detak ektopik, sedangkan ESP32-S3 bekerja
  keras menjaga data tetap aman."
- Mengapa: benda mati diberi watak, niat, atau emosi. HI menilainya tell paling kentara
  pada teks teknis dan tidak terlihat oleh skrip mana pun.
- Perbaikan: "Model mengklasifikasi detak ektopik dengan \textit{recall} 0,91. Data
  disimpan ke LittleFS sebelum dikirim."
- Catatan: metafora mati yang baku di literatur teknik tetap boleh (*sinyal merambat*,
  *gradien lenyap*). Saran SS "sebut manusianya atau pakai *you*" tidak berlaku (D).
- Sumber: HI 5c.1; SS false agency.
- Mesin: tidak (daftar kata watak seperti *cerdas, malas, berani, tahu, berusaha,
  bekerja keras* bisa membantu menandai, tetapi keputusan penilaian).

**B2.17 Asosiasi kabur**
- Tell: "Penurunan akurasi berkaitan dengan kualitas elektroda."
- Mengapa: menyatakan dua hal terhubung tanpa menyebut hubungannya.
- Perbaikan: "Akurasi turun 4 poin saat impedansi elektroda di atas 50~k$\Omega$."
  Bila hubungannya memang tidak diketahui, pertahankan rumusan kabur dan nyatakan
  sebagai dugaan.
- Sumber: HU §14; WP vague connection.
- Mesin: sebagian. `(?i)\b(berkaitan|terkait|berhubungan|terhubung|berasosiasi) dengan\b` untuk ditinjau.

### B3. Tingkat paragraf dan struktur

**B3.1 Kalimat tentang dokumen**
- Tell: "Subbab ini akan membahas perancangan perangkat keras." atau "Tulisan ini
  membahas ..."
- Mengapa: dokumen menjelaskan dirinya, bukan topiknya.
- Perbaikan: langsung isi, "Perangkat keras terdiri atas ESP32-S3, AD8232, dan
  INA219."
- Sumber: BS L7; HU §25; SS meta-commentary; HI 5b (dokumen dijadikan pelaku).
  Sudah diwajibkan NP aturan 7 (N-META).
- Mesin: ya. `(?i)\b(bab|subbab|bagian|butir|tulisan|artikel) ini (akan )?(membahas|memaparkan|menguraikan|menjelaskan|bertujuan)\b` · `(?i)\bpada (bab|subbab|bagian) ini akan\b`.

**B3.2 Heading diulang di kalimat pertama**
- Tell: `\subsection{Pengujian Latensi}` lalu "Pengujian latensi merupakan pengujian
  untuk mengukur latensi sistem."
- Mengapa: kalimat pertama mengulang judul sebelum isi dimulai.
- Perbaikan: "Latensi diukur dari detak terakhir dalam \textit{window} sampai alarm
  berbunyi."
- Sumber: HU §24.
- Mesin: sebagian. Tandai bila lebih dari separuh kata isi judul muncul di kalimat
  pertama yang memuat "merupakan" atau "adalah" (heuristik inferensi).

**B3.3 Ringkasan di akhir tiap paragraf**
- Tell: setiap paragraf diakhiri "Hal ini membuktikan bahwa sistem bekerja dengan baik."
- Mengapa: mengulang isi paragraf. Simpulan cukup di Bab 5.
- Perbaikan: hapus, atau ganti dengan konsekuensi yang belum disebut.
- Sumber: NI AI-18; HI D2; HU §2; WP section summaries.
- Mesin: sebagian. Pola B1.12 di kalimat terakhir paragraf, ditambah
  `(?i)\bhal ini (membuktikan|menunjukkan) bahwa\b` di posisi akhir.

**B3.4 Paragraf terlalu rapi**
- Tell: setiap paragraf berpola kalimat tesis, tiga pendukung, kalimat simpul.
- Mengapa: struktur sempurna terasa algoritmik (HI D5).
- Perbaikan: pertahankan kalimat klaim di awal (NP aturan 6), buang kalimat simpul
  ritual, biarkan jumlah kalimat pendukung mengikuti isi.
- Sumber: HI D5.
- Mesin: tidak.

**B3.5 Seksi tantangan dan prospek generik, saran generik**
- Tell: "Meskipun memiliki beberapa keterbatasan, sistem ini tetap memiliki prospek
  yang menjanjikan." atau Saran "Perlu dilakukan penelitian lebih lanjut."
- Mengapa: rumus "despite its challenges" dan saran tanpa arah.
- Perbaikan: "Konsumsi daya belum diukur dengan baterai, sehingga daya tahan 9~jam
  masih perkiraan dari arus rata-rata." · "Uji sinyal tubuh perlu diperluas ke subjek
  dengan riwayat aritmia."
- Sumber: WP outline-like conclusions; HU §13; BS `frasa-terlarang` §3,
  `struktur-sitasi`; NI `bagian-naskah` (Simpulan).
- Mesin: sebagian. `(?i)\bmeskipun (memiliki|terdapat) (beberapa |berbagai )?(keterbatasan|kekurangan|tantangan)\b` · `(?i)\bperlu (dilakukan )?penelitian lebih lanjut\b` (tinjau apakah arahnya disebut).

**B3.6 Tinjauan pustaka berupa daftar per sumber**
- Tell: "Menurut Ahmad~\cite{a}, ... Senada dengan itu, Budi~\cite{b} ... Menurut
  Citra~\cite{c}, ..."
- Mengapa: tiap kalimat dibuka nama, hubungan antartemuan hanya "senada". Sintesis
  tidak terjadi.
- Perbaikan: "Klasifikasi aritmia di mikrokontroler umumnya memakai CNN satu dimensi
  dengan kuantisasi INT8~\cite{a,b}, sedangkan pendekatan LSTM membutuhkan memori
  lebih besar~\cite{c}."
- Catatan: contoh sumber memakai gaya APA (Nama, tahun). Buku PA memakai sitasi
  bernomor, jadi polanya menjadi "Menurut X~\cite{}" dan "Penelitian X~\cite{}"
  (inferensi). Bila struktur Penelitian Terkait per paper memang konvensi kampus
  (subbab per judul paper di buku-pa), aturan ini berlaku di paragraf sintesis, bukan
  di subbab per paper.
- Sumber: BS `struktur-sitasi`; NI `bagian-naskah`; HI D9 (metrik menghitung 3 atau
  lebih kalimat "Menurut Nama").
- Mesin: ya. Hitung kalimat yang dibuka `(?i)^(Menurut|Penelitian oleh|Penelitian)\s+\S+.*~?\\cite` lebih dari 2 per subbab · `(?i)\b(senada|sejalan) dengan (itu|hal tersebut)\b`.

**B3.7 Latar belakang dari kosmos ke topik**
- Tell: paragraf pertama Bab 1 dimulai dari teknologi informasi umum, lalu kesehatan,
  lalu jantung, baru topik.
- Mengapa: slop akademik klasik Indonesia (BS).
- Perbaikan: kalimat pertama memuat data atau masalah spesifik, urutan fenomena berdata,
  yang sudah diketahui, celah, tujuan.
- Sumber: BS `bahasa-peneliti`; NI `bagian-naskah` (Pendahuluan).
- Mesin: tidak (B1.1 menangkap sebagian kalimat pembukanya).

**B3.8 Daftar berpoin untuk argumen, label tebal plus titik dua**
- Tell: `\item \textbf{Efisiensi:} sistem sangat efisien ...` untuk pembahasan.
- Mengapa: kerangka yang dipaksa menjadi tulisan. Naskah ilmiah Indonesia menyampaikan
  argumen dalam paragraf (NI).
- Perbaikan: paragraf dengan kalimat topik. Daftar tetap dipakai untuk enumerasi sejati
  (langkah, spesifikasi), sesuai NP aturan 5.
- Sumber: NI daftar bertitik; HI D6; BS L10; HU §19; WP inline-header lists.
- Mesin: ya. `\\item\s*\\textbf\{[^}]*\}\s*:?` dan `\\textbf\{` di dalam paragraf biasa
  (bold dekoratif).

**B3.9 Enumerasi bersandar "seperti"**
- Tell: "Sistem memakai komponen seperti ESP32-S3, AD8232, INA219, buzzer, dan lain
  sebagainya."
- Mengapa: kalimat gemuk, dan "seperti" menyiratkan daftar tidak lengkap tanpa dasar
  (WP juga mencatat *such as* sebelum daftar lengkap).
- Perbaikan: "Sistem terdiri atas ESP32-S3, AD8232, INA219, dan \textit{buzzer}." Fungsi
  rujukan ("seperti yang ditunjukkan Gambar~3.2") tetap sah (HI F6).
- Sumber: HI D4 (lebih dari 1 per 1.000 kata); NI KE-09; WP.
- Mesin: ya. `(?i)\b(seperti|antara lain|misalnya|di antaranya)\s+[^.]{0,60},[^.]{0,60}\bdan\b` dikecualikan bila diikuti `yang (ditunjukkan|terlihat|disajikan)`.

**B3.10 Rentang semu "mulai dari X hingga Y"**
- Tell: "Sistem dapat dipakai mulai dari rumah sakit hingga rumah pasien."
- Mengapa: X dan Y bukan ujung satu skala.
- Perbaikan: "Sistem dapat dipakai di rumah sakit dan di rumah pasien." Rentang nyata
  ("frekuensi 0,5 hingga 40~Hz") tetap sah.
- Sumber: HI D12. Lihat konflik di D (aturan rumah menganjurkan "mulai dari ... hingga
  ..." sebagai pengganti titik dua).
- Mesin: ya untuk penandaan. `(?i)\bmulai dari\b[^.]{1,60}?\b(hingga|sampai)\b`, tinjau apakah kedua ujung berangka atau berskala.

**B3.11 Rujukan spasial semu**
- Tell: "Hasil pengujian dapat dilihat pada tabel di bawah ini."
- Mengapa: posisi float LaTeX berpindah. Rujuk dengan nomor.
- Perbaikan: "Tabel~\ref{tab:latensi} menyajikan hasil pengujian latensi."
- Sumber: HI D10, kaidah "Rujuk tabel dan gambar dengan nomornya".
- Mesin: ya. `(?i)\b(tabel|gambar|grafik|diagram|persamaan)\s+(berikut( ini)?|di (atas|bawah)( ini)?)\b` · `(?i)\bsebagai berikut\b` (lemah).

**B3.12 Paragraf fakta berderet dan mekanisme urutan buku teks**
- Tell: paragraf Bab 2 yang mendaftar spesifikasi ESP32-S3 berurutan (inti, frekuensi,
  SRAM, PSRAM, WiFi) tanpa kaitan ke kebutuhan sistem.
- Mengapa: tetap terbaca AI walau kalimatnya bersih (HI, satu teks uji, tentatif).
- Perbaikan: ikat fakta pada klaim yang sudah ada di naskah dengan *karena* atau
  *sehingga*, "PSRAM 8~MB dipilih karena bufer rekaman 30~menit membutuhkan sekitar
  1,8~MB." Jangan menambah fakta baru.
- Sumber: HI D13, 5c.6.
- Mesin: tidak.

**B3.13 Format dekoratif**
- Tell: `\textbf{}` acak di tengah paragraf, emoji, garis pemisah, judul bergaya artikel
  populer ("Mengapa ESP32? Jawabannya Mengejutkan").
- Mengapa: format menurut aturan, bukan menurut isi.
- Perbaikan: bold hanya untuk istilah yang sedang didefinisikan, judul deskriptif.
- Sumber: BS L10; HI D11; HU §19, §20; WP style.
- Mesin: ya. `\\textbf\{` di paragraf · rentang emoji Unicode `[\U0001F300-\U0001FAFF☀-➿]` · `\\hrule|\\rule\{\\linewidth\}`.

**B3.14 Pertanyaan retoris**
- Tell: "Lalu, bagaimana jika sinyal terganggu saat pasien bergerak?"
- Mengapa: setup retoris, nada ceramah atau blog.
- Perbaikan: "Sinyal yang terganggu gerak ditandai \textit{lead-off} dan tidak
  diklasifikasi."
- Sumber: BS §1 (Pernahkah Anda, Tahukah Anda); HI D11; SS rhetorical setups.
- Mesin: ya. Tanda `?` di badan paragraf di luar kutipan dan rumusan masalah.

### B4. Register

**B4.1 Kata ganti orang pertama dan kedua**
- Tell: "Kami merancang sistem ini agar Anda dapat memantau jantung kapan saja."
- Mengapa: ragam ilmiah bertumpu pada gagasan, bukan penulis. Aturan rumah: penulis satu
  orang, tanpa "kami".
- Perbaikan: "Sistem dirancang untuk memantau detak jantung secara kontinu."
- Sumber: BS `bahasa-peneliti` (pasif plus "penelitian ini"); NI (satu sudut pandang per
  naskah); HI kaidah kata ganti.
- Mesin: ya. `(?i)\b(kami|kita|saya|anda|kamu|aku)\b` (kecualikan kutipan langsung).

**B4.2 Nada promosi**
- Tell: "Kini hadir sebagai solusi tepat, sistem ini dirancang khusus untuk memberikan
  hasil yang maksimal."
- Mengapa: register iklan dalam teks teknik.
- Perbaikan: "Sistem mengklasifikasi lima kelas detak AAMI di perangkat tanpa koneksi
  internet."
- Sumber: BS §4, §5 (jembatan solusi robotik); WP promotional language; HU §16.
- Mesin: ya. `(?i)\b(kini|telah) hadir\b` · `(?i)\bsolusi (terbaik|tepat|lengkap|terpercaya|jitu)\b` · `(?i)\bdirancang khusus\b` · `(?i)\bhasil (yang )?(maksimal|optimal)\b` · `(?i)\btak perlu (khawatir|pusing) lagi\b` · `(?i)\bmempermudah (hidup|kehidupan)\b` · `(?i)\b(revolusioner|terobosan baru|pengubah permainan|game changer)\b`.

**B4.3 Kolokial**
- Tell: "Prosesnya gampang dan nggak ribet, nilai F1 berayun dari 0,85 sampai 0,92."
- Mengapa: register percakapan di naskah resmi.
- Perbaikan: "Nilai F1 berfluktuasi antara 0,85 dan 0,92."
- Sumber: BS diksi akademik; HI 5c.2.
- Mesin: ya. `(?i)\b(bikin|banget|nggak|ngga|gak|kayak|gampang|ribet|gimana|aja|nembus|muter|jadul|goyangan|tukar guling)\b`.

**B4.4 Kata emosional dan evaluatif**
- Tell: "Hasilnya sangat mengejutkan dan luar biasa memuaskan."
- Mengapa: laporkan angka, biarkan pembaca menilai.
- Perbaikan: "Akurasi pada data sinyal tubuh 0,93, lebih tinggi dari perkiraan 0,88."
- Sumber: BS `kalimat-akademik` §5, `bahasa-peneliti`; SS telling instead of showing.
- Mesin: ya. `(?i)\b(mencengangkan|mengejutkan|luar biasa|sayangnya|menakjubkan|sangat menarik|memuaskan)\b`.

**B4.5 Koreksi berlebih ke register birokratis**
- Tell: "Adapun dalam rangka guna mengetahui kinerja sistem, maka dilaksanakan
  kegiatan pengujian."
- Mengapa: HI memperingatkan agar kalke dan kolokial tidak ditukar register birokratis.
- Perbaikan: "Kinerja sistem diuji dengan rekaman sinyal tubuh S01."
- Sumber: HI rambu 5b dan 5c; NI pembuka "Adapun", "dalam rangka".
- Mesin: ya. `(?:^|(?<=[.!?])\s+)Adapun\b` · `(?i)\bdalam rangka\b` · `(?i)\bguna (mengetahui|meningkatkan)\b`.

### B5. Kalke Inggris dan terjemahan khas Indonesia

**B5.1 "di mana" atau "dimana" sebagai penghubung**
- Tell: "Data diambil dari MIT-BIH, di mana setiap rekaman berdurasi 30~menit."
- Mengapa: tiruan *where*, *in which*. Paling sering muncul pada teks yang disunting
  model (HI).
- Perbaikan: "Data diambil dari MIT-BIH. Setiap rekamannya berdurasi 30~menit."
- Sumber: BS; NI AI-14, EJ-01; HI A3, kaidah.
- Mesin: ya. `(?i)\bdimana\b` · `(?<=\w)[,]?\s+di mana\s+(?!pun\b|saja\b)(?!.{0,80}\?)(?=[a-z])` (regex NI AI-14).

**B5.2 "yang mana"**
- Tell: "Filter dipasang sebelum CNN, yang mana hal ini mengurangi \textit{noise}."
- Mengapa: tiruan *which*.
- Perbaikan: "Filter dipasang sebelum CNN untuk mengurangi \textit{noise}."
- Sumber: BS; NI AI-13; HI A3.
- Mesin: ya. `(?i)\byang mana\b`.

**B5.3 Frasa verba kalke**
- Tell: "Kuantisasi memainkan peran penting dalam memperkecil model. Pengujian mengambil
  tempat di laboratorium."
- Mengapa: terjemahan harfiah *play a role*, *take place*, *it is important to*.
- Perbaikan: "Kuantisasi berperan memperkecil model. Pengujian berlangsung di
  laboratorium."
- Sumber: NI AI-05, AI-06, AI-08, nominalisasi kalke; HI 5b.
- Mesin: ya. `(?i)\bmemainkan perana?n?\b` · `(?i)\bmengambil tempat\b` · `(?i)\badalah penting untuk\b|\bitu adalah mungkin\b` · `(?i)\bmembuat keputusan\b` (lemah) · `(?i)\bmemberikan kontribusi\b`.

**B5.4 Pengisi kalke**
- Tell: "Dalam hal ini, model dilatih dengan data DS1. Dalam konteks ini, ..."
- Mengapa: dari *in this case*, *in terms of*. Biasanya bisa dihapus.
- Perbaikan: "Model dilatih dengan data DS1."
- Sumber: NI pengisi "dalam hal ini"; BS kalke (*dalam hal*, *berbicara tentang*, *pada
  akhir hari*, *membuat masuk akal*).
- Mesin: ya. `(?i)\bdalam (hal|kasus|konteks) ini\b` · `(?i)\bberbicara (tentang|soal)\b` · `(?i)\bpada akhir hari\b` · `(?i)\bmembuat masuk akal\b`.

**B5.5 Klausa partisip di depan kalimat (dangling)**
- Tell: "Menggunakan kuantisasi INT8, ukuran model berkurang menjadi 48~kB."
- Mengapa: kalke *Using X, ...*. Subjek induk (ukuran model) bukan pelaku "menggunakan".
- Perbaikan: "Kuantisasi INT8 memperkecil model menjadi 48~kB."
- Sumber: HI 5b (*Living in Bogor, I ...*).
- Mesin: sebagian. `(?:^|(?<=[.!?])\s+)(Menggunakan|Memanfaatkan|Dengan menggunakan|Mempertimbangkan|Mengingat)\s[^,]{3,60},` lalu tinjau subjek induk.

**B5.6 Dokumen atau penelitian sebagai pelaku**
- Tell: "Tulisan ini membahas ..." atau "Paper ini mengusulkan ..."
- Mengapa: HI menganggapnya kalke *This paper discusses*. NI `pertahankan.md` justru
  menyatakan "Penelitian ini bertujuan ..." pola baku Indonesia.
- Perbaikan: pertahankan "Penelitian ini" sebagai subjek tujuan atau temuan (NI).
  "Tulisan ini membahas" di badan bab ditangani B3.1.
- Sumber: HI 5b; NI `pertahankan.md` (pertentangan antar sumber, perlu keputusan user).
- Mesin: sebagian (lihat B3.1).

**B5.7 Istilah teknis diterjemahkan harfiah, kata bentukan tidak hidup**
- Tell: "Dilakukan sapuan parameter pada ukuran jendela." (*parameter sweep*,
  *window*).
- Mengapa: terjemahan kata per kata yang tidak dipakai di lapangan.
- Perbaikan sesuai aturan rumah: "Ukuran \textit{window} divariasikan dalam ablasi."
- Sumber: HI 5b; NI `istilah.md` (padanan ditolak bila tidak dipakai pembaca bidang).
- Mesin: sebagian. Daftar terjemahan terlarang rumah (penyangga, purwarupa, pustaka
  untuk *library*, papan untuk *board*, penanda waktu) sudah diperiksa `cek_tabel.py`
  N-ISTILAH. Terjemahan harfiah baru perlu penilaian.

**B5.8 Kolokasi salah dan kiasan halus**
- Tell: "Model ini bekerja paling baik dan paling kokoh, dan selisih akurasinya
  menyempit."
- Mengapa: kalke *performs best*, *most robust*, *the gap narrows*.
- Perbaikan: "Model ini mencapai F1 tertinggi, dan selisih akurasinya menurun dari
  0,03 menjadi 0,01."
- Sumber: HI 5b.
- Mesin: tidak.

**B5.9 Imbuhan Indonesia pada kata asing**
- Tell: "Model di-deploy ke ESP32-S3 setelah meng-compile firmware."
- Mengapa: NI menetapkan imbuhan pada kata asing memakai tanda hubung dan kata asing
  dimiringkan. HI menandai verba Inggris yang dipaksa berimbuhan *me-*.
- Perbaikan: "Model dipasang ke ESP32-S3 setelah \textit{firmware} dikompilasi." atau
  "di-\textit{deploy}" bila istilah asingnya dipertahankan.
- Sumber: NI `istilah.md`; HI 5b.
- Mesin: ya. `(?i)\b(di|me|meng|ter)-?(deploy|upload|download|compile|flash|install|train|update|reset|setting)\b` tanpa `\textit`.

**B5.10 Perangkai kalke dan kaidah perbandingan**
- Tell: "Akurasi CNN lebih baik dari LSTM, dan perbedaan antara INT8 dengan float32
  kecil."
- Mengapa: kaidah perangkai baku sering dilanggar terjemahan.
- Perbaikan: "Akurasi CNN lebih baik daripada LSTM, dan perbedaan antara INT8 dan
  \textit{float32} kecil."
- Sumber: NI KE-11, KE-12, KE-13, KE-17.
- Mesin: ya. `(?i)\blebih\s+(?!dari\b)\w+\s+dari\b(?!\s+(pada|sekadar)\b)` · `(?i)\bantara\s+(?!lain\b)[^.,;]{1,40}?\sdengan\b` · `(?i)\bbaik\s[^.,;]{1,40}?\sataupun\b` · `(?i)\bbukan\s(?!hanya\b|saja\b|sekadar\b)[^.;]{1,60}?,\s*tetapi\b`.

### B6. Rujukan, angka, dan tanda baca

**B6.1 Rujukan fiktif atau dari ingatan**
- Tell: entri `.bib` dengan DOI yang menuju artikel lain, buku tanpa halaman, penulis
  nyata dengan judul yang tidak ada.
- Mengapa: kegagalan terburuk tulisan berbantuan AI. WP memberi contoh DOI IEEE yang
  menuju artikel tak terkait.
- Perbaikan: rujukan hanya dari sumber yang diberikan user atau dibuka dan diverifikasi.
  Kekosongan ditandai penanda rumah, bukan diisi tebakan.
- Sumber: BS `bahasa-peneliti`, `struktur-sitasi`; NI KONTRAK pasal 3; WP citations.
- Mesin: sebagian. Kunci `\cite` yang tidak ada di `.bib` (peringatan BibTeX), entri
  `@book` tanpa `pages`, DOI yang tidak diselesaikan. Kebenaran isi rujukan tetap
  pemeriksaan manual.

**B6.2 Angka, sitasi, dan rujukan silang berubah saat menyunting**
- Tell: setelah dirapikan, "0,9712" menjadi "sekitar 97 %", satu `\cite` hilang karena
  kalimatnya digabung.
- Mengapa: model meringkas sampai makna bergeser. HI menyebut pemeriksaan rujukan silang
  sebagai yang paling sering menyelamatkan dokumen teknis.
- Perbaikan: himpunan angka, `\cite`, `\ref`, `\label` sebelum dan sesudah harus sama.
- Sumber: NI KONTRAK pasal 4, `periksa.py --banding`; HI prinsip 2, sebelas pemeriksaan;
  NP aturan 12.
- Mesin: ya (banding himpunan, normalisasi `{,}` ke `,` dulu).

**B6.3 Desimal titik dan satuan**
- Tell: "Arus rata-rata 0.18A pada tegangan 3.3 Volt."
- Mengapa: aturan rumah dan EYD V.
- Perbaikan: "Arus rata-rata 0,18~A pada tegangan 3,3~V."
- Sumber: NI EJ-07, EJ-08, EJ-09; BS `kalimat-akademik` §7.
- Mesin: ya. `\b\d+\.\d{1,4}\b` di prosa (kecualikan versi perangkat lunak, nomor
  subbab, `\ref`) · `(?<![\d.,])\d+(?:[.,]\d+)?(V|mV|mA|kW|Hz|kHz|MHz|kB|MB|ms)\b` · `\d\s?(Volt|Ampere|Watt|Hertz|Celcius)\b`.

**B6.4 Em dash, en dash, kutip keriting**
- Tell: "Sistem ini cepat — dan hemat daya." atau `---` di paragraf LaTeX, atau kutip
  “...” di sumber `.tex`.
- Mengapa: em dash sebagai tanda baca gaya adalah penanda kuat lama (WP: 2022 sampai
  Sep 2026). Aturan rumah melarangnya di paragraf.
- Perbaikan: konjungsi ("yang", "sehingga", "karena") atau koma.
- Sumber: BS L10; HI prinsip 4; HU §8, §21; SS; WP historical em dash.
- Mesin: ya. `—|–` · `(?<!-)---(?!-)` di paragraf · `[“”‘’]` di berkas `.tex`.

**B6.5 Klaim celah tanpa cek literatur**
- Tell: "Belum ada penelitian yang menerapkan TinyML untuk klasifikasi aritmia."
- Mengapa: klaim negatif mutlak yang hampir pasti salah.
- Perbaikan: "Penelitian sebelumnya~\cite{a,b} belum mengukur kinerja pada sinyal tubuh
  dari sensor AD8232."
- Sumber: NI `bagian-naskah`.
- Mesin: ya untuk penandaan. `(?i)\bbelum (ada|pernah ada) (penelitian|studi)\b`.

---

## C. Daftar frasa dan kata Indonesia (gabungan, tanpa duplikat)

Tag sumber: BS, NI, HI. Kata yang di BS diturunkan sebagai kalke daftar Inggris ditandai
"BS-k" (padanan *delve*, *landscape*, dan seterusnya dari WP/HU). Kolom "Catatan genre"
adalah inferensi penulis katalog untuk buku PA teknik.

### C1. Pembuka dan penegas

| Frasa | Sumber | Catatan genre |
|---|---|---|
| di era digital (yang serba cepat) ini, di era globalisasi, di era modern | BS, NI, HI | |
| di zaman (modern seperti) sekarang ini | BS | |
| seiring (dengan) perkembangan teknologi / zaman, seiring berjalannya waktu | BS, NI, HI | |
| di tengah pesatnya kemajuan teknologi, di tengah derasnya | NI, HI | |
| dewasa ini, belakangan ini (tanpa data) | BS, `bahasa-peneliti` | |
| tidak dapat dipungkiri (bahwa), tak bisa dimungkiri | BS, NI, HI | |
| seperti yang kita ketahui (bersama), sebagaimana kita ketahui bersama | BS, NI, HI | |
| sudah menjadi rahasia umum | NI | |
| dalam dunia X yang terus berkembang, dalam dunia yang serba cepat | BS, HI | |
| dalam beberapa tahun terakhir X mengalami pertumbuhan signifikan | BS | butuh angka dan rujukan |
| pernahkah Anda ..., tahukah Anda ..., siapa yang tidak mengenal ... | BS | |
| mari kita (menyelami / telusuri / bahas / lihat / mulai) | BS, NI, HI | |
| sebelum membahas lebih lanjut, mari kita pahami dulu apa itu X | BS | |
| artikel/bab/subbab/tulisan ini akan membahas | BS, NP | |
| berikut adalah beberapa hal yang perlu diketahui | BS | |
| X memainkan peran yang sangat penting dalam ... | BS, NI | |
| pendidikan/teknologi merupakan hal yang sangat penting | BS `bahasa-peneliti` | |

### C2. Transisi dan pengisi

| Frasa | Sumber | Catatan genre |
|---|---|---|
| selain itu, tidak hanya itu, terlebih lagi, lebih lanjut | BS, NI, HI | sah sekali-sekali, NP aturan 8 merotasi "Selain itu" |
| tak kalah penting, yang tidak kalah menarik | BS | |
| namun demikian | BS, NI (G), HI | ganti "Namun," |
| oleh karena itu, oleh sebab itu, dengan demikian | BS, NI, HI | baku, ditindak bila berulang |
| secara keseluruhan, pada akhirnya | BS, NI, HI | |
| di sisi lain (tanpa kontras nyata) | BS, HI | |
| sementara itu, adapun, selanjutnya | BS, NI (Adapun) | |
| dalam hal ini, dalam kasus ini, dalam konteks ini | BS, NI | |
| penting untuk dicatat/dipahami/diketahui bahwa, patut dicatat, perlu diingat bahwa, perlu diketahui bahwa | BS, NI, HI | |
| seperti yang telah disebutkan sebelumnya | BS | |
| dengan kata lain | BS, NI | |
| hal ini, hal tersebut (berulang) | NI | |
| konsekuensinya | HI | |
| senada dengan itu, sejalan dengan itu | HI | |
| pertanyaannya sederhana, gagasannya sederhana, hasilnya tegas, prosedurnya begini, cara membacanya begini, perhatikan bahwa, tiga hal langsung terlihat, di situlah ... yang sebenarnya | HI | |

### C3. Penutup

| Frasa | Sumber | Catatan genre |
|---|---|---|
| sebagai kesimpulan, kesimpulannya, sebagai penutup | BS, HI | judul "Kesimpulan" Bab 5 tetap sah |
| dengan demikian (dapat) disimpulkan bahwa | NI, HI | |
| demikianlah ..., nah, itulah tadi pembahasan ... | BS, `bahasa-peneliti` | |
| semoga (artikel ini) bermanfaat, semoga membantu | BS, HI | |
| jangan ragu untuk ... | BS, HI | |
| dengan memahami hal-hal di atas | BS | |
| masa depan X terlihat (sangat) menjanjikan | BS | |
| meski memiliki banyak tantangan, X tetap menjadi ...; dengan segala kelebihan dan kekurangannya | BS | |
| hal ini membuktikan bahwa (di akhir paragraf) | NI | |
| perlu (dilakukan) penelitian lebih lanjut (tanpa arah) | BS, NI | |

### C4. Penguat, klaim, dan kata payung

| Frasa | Sumber | Catatan genre |
|---|---|---|
| memegang peranan (yang sangat) penting / krusial / vital / sentral | BS, NI, HI | |
| berperan vital, aspek vital, sangat krusial, semakin krusial | BS, HI | |
| menjadi kunci utama, menjadi faktor kunci | HI | |
| tak lepas dari, tidak dapat dipisahkan dari (kehidupan) | BS, HI | |
| patut diperhatikan, menjadi sorotan | HI | |
| sangat signifikan, signifikan (tanpa uji) | BS, NI, HI | |
| solusi (yang) inovatif / revolusioner / terbaik / tepat / lengkap / jitu | BS, NI | |
| sangat efektif dan efisien; efektif, efisien, dan inovatif; cepat, tepat, dan akurat; aman, nyaman, dan andal | BS, NI, HI | triplet |
| luar biasa, mencengangkan, mengejutkan, sayangnya | BS | |
| pasti, selalu, tidak pernah, tanpa cacat, tidak diragukan lagi, semua orang | BS, HI | |
| para ahli menilai, sejumlah penelitian menunjukkan, banyak peneliti sepakat, berbagai studi menunjukkan, menurut berbagai sumber, banyak orang percaya, beberapa ahli berpendapat | BS, HI | |
| dapat dikatakan bahwa, cenderung, pada umumnya, relatif (bertumpuk) | BS | hedging tunggal sah (NI) |
| mungkin dapat (cenderung / berpotensi), diduga kemungkinan dapat | BS, NI, HI | |
| berbagai aspek, faktor-faktor tertentu, dimensi kehidupan, peran strategis | NI | |
| berbagai macam, segudang, sederet | BS, NI | |

### C5. Kosakata slop dan bergengsi

| Kata | Sumber | Catatan genre |
|---|---|---|
| hiruk pikuk | BS (satu-satunya yang tervalidasi penutur) | |
| lanskap (kiasan) | BS-k | |
| ranah ("dalam ranah X") | BS | |
| krusial | BS-k, HI | |
| menyelami, menggali lebih dalam, mengupas (tuntas) | BS-k, HI | *mengupas* bernada jurnalistik (HI) |
| menggarisbawahi, menyoroti (kiasan) | BS-k | |
| memanfaatkan, mendayagunakan, mengoptimalkan (kiasan) | BS, HI | *mengoptimalkan* sah bila ada optimasi |
| mengimplementasikan, merealisasikan, mengakomodasi | HI | lazim di teknik, nilai per kasus |
| memupuk, menumbuhkan (kiasan) | BS | |
| tangguh, kokoh (untuk perangkat lunak) | BS, HI (*paling kokoh*) | *robust* teknis boleh, tulis \textit{robust} bila istilah |
| mulus, tanpa hambatan, terintegrasi dengan mulus | BS | |
| menavigasi, mengarungi (kiasan) | BS-k | |
| memberdayakan, merampingkan (kiasan) | BS-k | |
| transformatif, mutakhir, tercanggih | BS | |
| holistik, sinergi, paradigma | BS, HI (holistik) | |
| komprehensif, esensial, fundamental, masif | HI | |
| semarak, dinamis (komunitas) | BS-k | |
| yang terus berkembang | BS-k | |
| bersemayam, terletak indah | BS-k | |
| memulai perjalanan | BS-k | |
| beresonansi, menggema (kiasan) | BS-k | |
| jalinan, permadani (kiasan) | BS-k | |
| garda terdepan, mercusuar (harapan) | BS | |
| membuka (memaksimalkan) potensi | BS-k | |
| bukti nyata (komitmen) | BS-k | |
| game changer, pengubah permainan, revolusioner, terobosan baru | BS | |

### C6. Frasa promosi (BS §4, relevan bila muncul di Bab 1 atau Abstrak)

kini hadir / telah hadir (sebagai solusi), tak perlu pusing / khawatir lagi, bawa X ke
level berikutnya, dirancang khusus untuk memenuhi kebutuhan, hasil (yang) maksimal /
optimal, meningkatkan efisiensi dan produktivitas (tanpa angka), pilihan tepat / cerdas,
pengalaman yang tak terlupakan, siap menemani, mempermudah hidup Anda, langkah awal
menuju kesuksesan. Semua BS.

### C7. Kalke dan perangkai

| Frasa | Sumber |
|---|---|
| di mana / dimana (penghubung), yang mana, dalam mana | BS, NI, HI |
| memainkan peran(an) | NI, HI |
| mengambil tempat | NI |
| adalah penting untuk, itu adalah mungkin untuk | NI |
| membuat keputusan | NI |
| memberikan kontribusi terhadap, memberikan pengaruh terhadap | NI, HI |
| melakukan analisis / pengukuran / perbandingan / pengujian terhadap, mengalami peningkatan / penurunan | BS, NI, HI |
| dalam hal (in terms of), berbicara tentang, pada akhir hari, membuat masuk akal, take-away / poin kunci | BS |
| ini bukan berarti, hal ini bukan berarti, X bukan berarti Y | HI |
| bukan hanya ... tetapi juga ..., bukan sekadar ... melainkan ..., lebih dari sekadar, X bukan lagi pilihan melainkan keharusan, bukan tentang X melainkan Y | BS, NI, HI |
| mulai dari X hingga Y (rentang semu) | HI |
| tabel di bawah ini, grafik di atas | HI |
| dikarenakan, berdasarkan pada, antara A dengan B, baik A ataupun B, lebih baik dari, daripada itu, sedangkan / sehingga (pembuka kalimat) | NI, HI |
| teknologi pemungkin, sapuan parameter, armada pembangkit, paling kokoh, bekerja paling baik, selisihnya menyempit | HI |

### C8. Residu mesin

Tentu, berikut ...; Semoga membantu; Jangan ragu untuk ...; `contentReference`,
`oaicite`, `[cite: 1]`, `【】`, `turn0search` (BS, HI). Placeholder isian yang lupa
diganti (WP).

---

## D. Konflik dengan aturan rumah dan butir yang dikecualikan

### D1. Konflik langsung dengan aturan rumah

| # | Aturan sumber | Sumber | Aturan rumah | Keputusan usulan |
|---|---|---|---|---|
| 1 | Ganti em dash dengan koma, titik dua, atau kurung; daftar "didahului titik dua, bukan digantung pada adalah" | HI prinsip 4, 5b teknik 1; HU §8; SS; BS ejaan (titik dua setelah pernyataan lengkap) | Tanpa titik dua di paragraf | Pengganti di skill rumah hanya konjungsi ("yaitu", "meliputi", "berupa"), koma, kurung, atau kalimat baru |
| 2 | Contoh perbaikan memakai titik dua ("... penanda keanggotaan marga: hanya warga ...") | NI AI-10, BS contoh | Sama | Contoh tidak disalin, ditulis ulang |
| 3 | Em dash boleh untuk rentang (2020—2025) di ragam non-resmi | BS L10, `ejaan-eyd` | Tanpa em dash di paragraf | Rentang ditulis "sampai" atau "hingga" |
| 4 | Pakai padanan LAZIM di semua ragam (unduh, berkas, perangkat keras, tautan, pembaruan, umpan balik) | BS `padanan-istilah` | Istilah teknis tetap Inggris dan miring, tidak diterjemahkan | Daftar padanan BS tidak dipakai. Yang tetap berlaku hanya "jangan pakai padanan kaku" |
| 5 | Padanan Indonesia dulu, istilah asing dalam kurung pada kemunculan pertama ("beban kognitif (*cognitive load*)"); HI "beri padanan dalam kurung tiap bab" | BS `bahasa-peneliti` no. 7; HI kaidah istilah asing | Inggris miring utama, terjemahan boleh sekali dalam kurung | Arah dibalik, istilah Inggris di luar kurung |
| 6 | Istilah asing miring setiap kali muncul | NI, HI | Kata adopsi tertentu tegak (bufer, `preprocessing`, `single-lead`, `flowchart`) | Daftar pengecualian rumah menang |
| 7 | "kami" sah untuk tim; *penulis* atau *peneliti* bila pelaku perlu disebut | HI kaidah kata ganti; NI; BS | Penulis satu mahasiswa, tanpa "kami" | "kami" dilarang. Pemakaian "penulis" belum diputuskan rumah, tanyakan user |
| 8 | Bilangan satu-dua kata ditulis huruf (3 kali menjadi tiga kali), dianggap bukan perubahan nilai | NI kontrak 3 | Angka tidak pernah berubah | Jangan ubah bentuk angka saat sunting, atau minta izin user, karena memecah pemeriksaan banding angka |
| 9 | "mulai dari X hingga Y" ditandai sebagai rentang semu | HI D12 | `laporan/CLAUDE.md` menganjurkan "mulai dari ... hingga ..." sebagai pengganti titik dua | Boleh hanya untuk rentang nyata berangka atau berskala, selain itu pakai "yaitu" atau "meliputi" |
| 10 | Judul pakai sentence case, Title Case adalah penanda AI | BS L10; HU §20; WP style | Judul bab/subbab buku-pa memakai Title Case (konvensi template) | Aturan Title Case dikecualikan |
| 11 | Penanda kekosongan `[RUJUKAN DIPERLUKAN: ...]` atau `[PERLU DATA: ...]` / `[PERLU RUJUKAN: ...]` | BS; NI | `\PlaceholderData{...}`, `PLACEHOLDER-DATA`, `PLACEHOLDER-GAMBAR` | Pakai penanda rumah |
| 12 | Gaya sitasi bawaan APA (Nama, tahun) dan contoh "Menurut Nama (tahun)" | BS; NI; HI D9 | `~\cite{}` bernomor | Pola sitasi formulaik disesuaikan ke bentuk bernomor |
| 13 | Transisi tertentu maksimal sekali per teks | BS L6 | Bukan aturan rumah, tetapi NP aturan 8 merotasi "Selain itu" dan "Dengan demikian" | NP menang, ambang kepadatan dari HI atau NI dipakai sebagai pemeriksaan |
| 14 | Wikipedia: model terbaru yang menghindari semua tanda baca alternatif (hanya koma dan titik) kini menjadi penanda baru | WP (`{{cn}}`, belum bersumber) | Tanpa titik dua, titik koma, em dash | Aturan rumah tetap. Inferensi: variasi struktur kalimat (anak kalimat, kurung, konjungsi) perlu dijaga supaya larangan tanda baca tidak menghasilkan ritme koma-titik yang datar |
| 15 | Abstrak 150 sampai 250 kata, lima unsur, tanpa sitasi | BS; NI | Struktur abstrak diatur skill `struktur-pa` | Tidak masuk skill baru, rujuk `struktur-pa` |

### D2. Butir yang tidak cocok untuk buku PA teknik (dikecualikan)

- **SS:** "kill all adverbs", "two items beat three", "use *you*", "put the reader in the
  room", "every sentence needs a human subject", "no passive constructions", larangan
  pembuka *Wh-*, skor 35/50. Gaya esai atau blog dan bertentangan dengan pasif yang sah
  di Metode serta larangan "kami".
- **BS kewajiban 4** "kalimat aktif sebagai bawaan". Tanpa "kami", pasif dan subjek
  benda adalah alat utama. NI dan HI F1 melindungi pasif di Metode dan Hasil.
- **HI "Menghindari sterilitas"** (opini, orang pertama, sedikit tidak rapi) dan preset
  suara pribadi. HI sendiri menyatakan teks teknis yang netral adalah suara manusia
  yang benar.
- **HI kalibrasi GPTZero dan ambang `metrik.py`** yang disetel ke korpus satu penulis.
  Tujuan skill rumah adalah keterbacaan, bukan lolos detektor (NI dan HI sama-sama
  menolak tujuan itu).
- **BS modul marketing, website/UX, SEO** seluruhnya, termasuk `frasa-terlarang` §4
  kecuali sebagai daftar frasa promosi yang harus nol.
- **HU §26** (menjawab pembaca yang sudah tahu konteks, untuk balasan pesan), §10
  (tanda hubung kata majemuk Inggris).
- **WP** bagian khusus wiki (edit summary, AfC, markup wikitext, utm_source, templat
  pemeliharaan, sumber sekunder dan notabilitas).
- **NI alat jaringan** (`openalex.py`, MCP Consensus dan alphaXiv). Bertentangan dengan
  kebiasaan rumah untuk tidak mengirim data ke layanan luar tanpa diminta. Data
  keterpakaian istilah di `istilah.md` tetap boleh dikutip sebagai bahan.
- **HI "bila" diganti "jika"** dan **"klaim kemampuan diberi *dapat*"**. Preferensi
  penulis HI, bukan kaidah. Tidak perlu diadopsi.

---

## E. Celah (tidak dicakup sumber mana pun untuk genre ini)

Semua butir di bawah adalah inferensi penulis katalog dari membandingkan isi sumber
dengan kebutuhan buku PA.

1. **LaTeX.** Tidak ada sumber yang menangani teks sumber `.tex`. Pemeriksa harus tahu
   cara membuang `\cite`, `\ref`, `\label`, `%`, lingkungan float, persamaan, dan
   `\textit{}` sebelum mencocokkan regex, serta mengenali `~` sebagai spasi tak putus
   dan `{,}` di mode matematika sebagai koma desimal. HI hanya menyinggung `0{,}5` dan
   hitungan `\begin{equation}`.
2. **Register per bab teknik.** Sumber membahas IMRaD jurnal, bukan struktur buku PA
   PENS (Bab 2 Teori Penunjang dan Penelitian Terkait, Bab 3 rancangan, Bab 4 hasil dan
   analisis). Pembedaan Bab 3 ditulis sebagai rancangan dan Bab 4 sebagai capaian,
   serta "belum diukur" untuk yang belum ada data, hanya ada di skill rumah
   (`narasi-pa` aturan 11, `struktur-pa`).
3. **Paragraf penjelas tabel dan gambar.** Sumber hanya berkata "jangan ulang seluruh
   tabel" dan "rujuk dengan nomor". Pola Temuan, Bukti, Makna, batas lima angka, dan
   angka wajib berpembanding hanya ada di `narasi-pa`.
4. **Bahasa teknik elektro dan *embedded*.** Tidak ada daftar tell khas deskripsi
   perangkat keras (mis. "otak dari sistem", "jantung dari rangkaian", "menjembatani",
   "mengorkestrasi", "secara *seamless*", "*real-time* yang andal" tanpa angka latensi,
   "hemat daya" tanpa mA). Ini kandidat daftar baru, perlu dikumpulkan dari draf nyata.
5. **Klaim kinerja tanpa kondisi uji.** Sumber menindak "signifikan" dan "membuktikan",
   tetapi tidak menuntut kondisi uji menempel pada klaim (sumber sinyal *replay* lawan
   sinyal tubuh, jumlah ulangan, data uji). Hanya ada di `narasi-pa` aturan 4.
6. **Penggunaan istilah Inggris di laporan Indonesia.** Semua sumber condong ke padanan
   Indonesia atau ke "ukur keterpakaian". Tidak ada yang membahas kebijakan "Inggris
   miring sebagai default" dan kesalahan khasnya (miring tidak konsisten, istilah sama
   kadang tegak, imbuhan pada kata miring, jamak "*sensor-sensor*", kapitalisasi
   istilah di awal kalimat).
7. **Label internal repo bocor ke teks cetak** (path berkas, nama skrip, "Fase n", nama
   env `PA_*`, rev PCB). Tidak ada di sumber. Mesin bisa memeriksa dengan regex
   `\bFase\s+[A-G0-9]\b|\bHW-\d|\bPA_[A-Z_]+|\.py\b|\.cpp\b|/` di prosa.
8. **Penanda ketidakpastian khas pengukuran** (ketelitian alat, jumlah sampel kecil,
   satu subjek). Sumber membahas hedging umum, bukan cara menulis keterbatasan
   pengukuran hardware secara jujur tanpa terdengar defensif.
9. **Konsistensi lintas bab dalam buku panjang.** NI dan HI menyarankan daftar istilah
   di depan, tetapi tidak ada mekanisme untuk singkatan yang didefinisikan ulang per
   bab, nomor `Tabel~\ref` yang diucapkan dengan kata, atau istilah yang berganti antara
   Bab 3 dan Bab 4. `narasi-pa` aturan 9 hanya menyuruh `grep`.
10. **Kalimat pengantar float dan *caption*.** Tidak ada sumber yang membahas *caption*
    yang berbunyi seperti kalimat AI ("Gambar ini menunjukkan ...") atau paragraf
    pengantar gambar yang hanya mengumumkan gambar.
11. **Validasi tell Indonesia.** Tidak ada studi korpus kosakata berlebih untuk bahasa
    Indonesia (BS mengakuinya). Ambang HI dikalibrasi ke satu penulis dan GPTZero, NI
    tidak memberi ambang kepadatan selain hitungan 2 atau 3. Ambang untuk skill rumah
    harus diukur dari buku-pa sendiri (mis. jalankan pemeriksa pada draf yang sudah
    disetujui user sebagai baseline) sebelum dijadikan batas keras.
12. **Eval.** Hanya NI yang punya `evals/cases.json`. Untuk aturan rumah no. 8 (eval
    10/10), kasus uji harus disusun dari kalimat buku-pa yang nyata dan berjawaban pasti
    (mis. regex KE-01, di mana, angka berubah), bukan dari contoh sumber.
