const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Bedah Paper Lueken 2023";

const GELAP = "1F2A44";
const AKSEN = "B8432F";
const ABU = "5F6B7A";
const TIPIS = "EEF1F5";
const FONT = "Arial";

const judul = (slide, teks) =>
  slide.addText(teks, { x: 0.5, y: 0.35, w: 9, h: 0.9, fontFace: FONT, fontSize: 26, bold: true, color: GELAP, margin: 0, valign: "top" });

const sumber = (slide, teks) =>
  slide.addText(teks, { x: 0.5, y: 5.1, w: 9, h: 0.35, fontFace: FONT, fontSize: 9, color: ABU, italic: true, margin: 0 });

const butir = (slide, items, opt = {}) =>
  slide.addText(
    items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 } })),
    { x: 0.5, y: 1.4, w: 9, h: 3.5, fontFace: FONT, fontSize: 16, color: GELAP, margin: 0, valign: "top", ...opt }
  );

const gambar = (slide, path, x, y, w, h, keterangan) => {
  slide.addImage({ path, x, y, w, h });
  slide.addText(keterangan, { x, y: y + h + 0.08, w, h: 0.45, fontFace: FONT, fontSize: 10, color: ABU, margin: 0, valign: "top" });
};

const angkaBesar = (slide, x, y, angka, label) => {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w: 2.1, h: 1.55, fill: { color: TIPIS }, line: { color: TIPIS }, rectRadius: 0.1 });
  slide.addText(angka, { x, y: y + 0.12, w: 2.1, h: 0.8, fontFace: FONT, fontSize: 34, bold: true, color: AKSEN, align: "center", margin: 0 });
  slide.addText(label, { x: x + 0.1, y: y + 0.9, w: 1.9, h: 0.55, fontFace: FONT, fontSize: 11, color: ABU, align: "center", valign: "top", margin: 0 });
};

const sel = (t) => ({ text: t, options: { bold: true, fill: { color: TIPIS } } });
const SUMBER = "Sumber: M. Lueken dkk., Sensors, vol. 23, no. 12, art. 5618, 2023. DOI 10.3390/s23125618 (open access, CC BY)";

{
  const s = pres.addSlide();
  s.background = { color: GELAP };
  s.addText("Bedah Paper", { x: 0.6, y: 0.6, w: 8.8, h: 0.5, fontFace: FONT, fontSize: 16, color: "C9D1E0", margin: 0 });
  s.addText("Automated Signal Quality Assessment of Single-Lead ECG Recordings for Early Detection of Silent Atrial Fibrillation", {
    x: 0.6, y: 1.15, w: 8.8, h: 1.7, fontFace: FONT, fontSize: 24, bold: true, color: "FFFFFF", margin: 0, valign: "top",
  });
  s.addText("Lueken, Gramlich, Leonhardt, Marx, Zink (RWTH Aachen)\nSensors, vol. 23, no. 12, 2023, open access", {
    x: 0.6, y: 2.95, w: 8.8, h: 0.8, fontFace: FONT, fontSize: 13, color: "C9D1E0", margin: 0, valign: "top",
  });
  s.addText("Muhammad Rafi Rizaldi, NRP 3123600001\nBimbingan Proyek Akhir, 15 Oktober 2026", {
    x: 0.6, y: 4.2, w: 8.8, h: 0.8, fontFace: FONT, fontSize: 13, color: "FFFFFF", margin: 0, valign: "top",
  });
  s.addNotes("Paper ini dipilih karena menilai kualitas sinyal ECG single-lead secara otomatis sebelum sinyal dipakai mendeteksi aritmia, persis kebutuhan minggu ini untuk rekaman sinyal tubuh. Terbit 2023, open access, 20 sitasi di Scopus per 15 Oktober 2026.");
}

{
  const s = pres.addSlide();
  judul(s, "Skrining AF massal dengan alat single-lead gagal bila kualitas sinyal tidak dinilai");
  butir(s, [
    "AF sering tanpa gejala dan paroksismal, baru terdiagnosis saat terekam",
    "Skrining besar memakai stik ECG genggam single-lead, dipegang dua tangan",
    "Elektroda logam tanpa gel: impedansi kulit berubah, artefak gerak tinggi",
    "High-pass input alat mengubah morfologi: gelombang P tersamar noise",
    "Sinyal buruk berujung salah klasifikasi, beban klinisi naik",
    "Tujuan: indeks kualitas otomatis (AISQA) yang meniru penilaian ahli",
  ]);
  sumber(s, SUMBER);
  s.addNotes("Latar: AF 1 sampai 2% populasi, naik sampai 17,8% di atas 85 tahun, risiko stroke lima kali. Alat skrining single-lead mudah dipakai tetapi sinyalnya berbeda dari ECG konvensional. Paper memodelkan rantai pengukuran lalu membangun penilai kualitas berbasis machine learning.");
}

{
  const s = pres.addSlide();
  judul(s, "7.031 rekaman satu menit dari apotek, dinilai ahli dalam empat kelas kualitas");
  s.addTable(
    [
      [sel("Kualitas (ahli)"), sel("Irama normal"), sel("AF"), sel("Seluruh data")],
      ["Excellent (Q0)", "98,20%", "1,80%", "11,83% (832)"],
      ["Good (Q1)", "95,79%", "4,21%", "67,97% (4.779)"],
      ["Poor (Q2)", "88,24%", "11,76%", "19,10% (1.343)"],
      ["Uninterpretable (Q3)", "0%", "0%", "1,10% (77)"],
    ],
    { x: 0.5, y: 1.4, w: 9, colW: [2.6, 2.1, 1.9, 2.4], fontFace: FONT, fontSize: 12, color: GELAP, border: { type: "solid", color: "C9D1E0", pt: 0.75 }, rowH: 0.4, align: "center" }
  );
  butir(s, [
    "7.295 subjek usia 65 tahun ke atas, 90 apotek di Aachen, rekaman 60 detik, 200 Hz",
    "Alat sendiri menandai AF pada 6,08% rekaman (432 dari 7.107)",
    "Makin buruk kualitas, makin besar porsi rekaman yang ditandai AF",
  ], { y: 3.6, h: 1.4, fontSize: 14 });
  sumber(s, SUMBER);
  s.addNotes("Data dari studi skrining sebelumnya oleh tim yang sama. Ahli menilai irama dan kualitas bertahap; AF didefinisikan irama tak teratur minimal 30 detik tanpa gelombang P, atrial flutter ikut dihitung AF. Tabel 2 paper dipangkas ke kolom yang menjawab judul slide.");
}

{
  const s = pres.addSlide();
  judul(s, "Tiga gerbang preprocessing: artefak gerak, durasi 30 detik, deteksi puncak");
  butir(s, [
    "Jendela 5 detik, kira-kira 5 detak",
    "Korelasi FFT dan eCDF tiap jendela terhadap jendela lain, ambang 0,982",
    "Sisa rekaman harus 30 detik berurutan, sesuai pedoman ESC",
    "Balik polaritas bila alat dipegang terbalik (mean kurang dari median)",
    "R-peak dideteksi, median HR harus 40 sampai 150 bpm",
    "Lolos: 99,53% rekaman valid, 99,30% puncak terdeteksi",
  ], { w: 4.6, fontSize: 14 });
  gambar(s, "output/fig6_rantai.png", 5.4, 1.9, 4.1, 0.96, "Gambar 6 paper: rantai preprocessing sebelum ekstraksi fitur");
  sumber(s, SUMBER);
  s.addNotes("Tiga gerbang: artefak gerak, durasi minimal, dan deteksi puncak dengan rentang HR fisiologis. Dari 7.031 rekaman hanya 33 tidak valid dan 49 gagal deteksi puncak, kebanyakan dari kelas uninterpretable. Angka dari Tabel 3 paper.");
}

{
  const s = pres.addSlide();
  judul(s, "Deteksi artefak gerak dirancang agar tidak menganggap AF sebagai artefak");
  butir(s, [
    "Artefak gerak mengubah spektrum dan distribusi amplitudo jendela",
    "AF mengubah interval RR, bukan spektrum atau distribusi amplitudo",
    "Ambang 0,982 dipilih agar artefak terbuang dan pola AF lolos",
    "Rekaman AF bersih tetap di atas ambang sepanjang 60 detik",
  ], { w: 5.3, fontSize: 15 });
  gambar(s, "output/fig7_artefak.png", 6.3, 1.25, 2.85, 3.28, "Gambar 7 paper: sinus dengan artefak awal (atas), AF tanpa artefak (bawah)");
  sumber(s, SUMBER);
  s.addNotes("Ini pembeda utama dari SQI berbasis keteraturan interval RR: korelasi FFT dan eCDF antar jendela peka pada artefak tetapi tidak pada irama tak teratur. Untuk sistem yang mengklasifikasi aritmia, penyaring kualitas harus seperti ini supaya segmen aritmia tidak dibuang sebelum sampai ke model.");
}

{
  const s = pres.addSlide();
  judul(s, "22 fitur empat domain, termasuk jarak ke prototipe denyut berkualitas excellent");
  butir(s, [
    "Statistik: mean, median, deviasi, skewness, kurtosis",
    "Waktu: mean HR, SDNN, coverage, konsistensi eCDF dan sinyal",
    "Frekuensi: konsistensi FFT, basSQI, qrsSQI, pliSQI, SNR, mean SQI",
    "Morfologi: amplitudo R, deviasi template, jarak Euclid, L1, DTW, korelasi",
    "Prototipe dari klaster DTW kelas excellent, dua klaster memuat 90% varians",
  ], { w: 4.6, fontSize: 14 });
  gambar(s, "output/fig8_prototipe.png", 5.6, 1.3, 3.6, 2.96, "Gambar 8 paper: empat klaster prototipe denyut dari rekaman excellent");
  sumber(s, SUMBER);
  s.addNotes("Fitur dihitung sekali per rekaman, vektor 22 dimensi. basSQI, qrsSQI, pliSQI mengikuti Clifford 2012. Prototipe dibuat dari denyut rata-rata rekaman excellent, diklaster k-means dengan jarak DTW. Daftar lengkap di Tabel 4 paper.");
}

{
  const s = pres.addSlide();
  judul(s, "Regresi Gaussian process mencapai korelasi 0,75 saat latih dan 0,60 saat uji");
  angkaBesar(s, 0.5, 1.5, "0,752", "korelasi Pearson, latih dan validasi 5 lipatan");
  angkaBesar(s, 2.8, 1.5, "0,604", "korelasi Pearson, data uji 20%");
  angkaBesar(s, 5.1, 1.5, "98,01%", "balanced accuracy latih, interpretable vs tidak");
  angkaBesar(s, 7.4, 1.5, "94,99%", "balanced accuracy uji");
  butir(s, [
    "Kernel eksponensial terbaik: RMSE 0,396 latih, 0,468 uji pada skala 0 sampai 3",
    "Distribusi AISQA naik monoton mengikuti kelas ahli, tetapi tumpang tindih",
    "Label ahli berbasis aturan heuristik, batas antar kelas tidak tajam",
  ], { y: 3.4, h: 1.5, fontSize: 15 });
  sumber(s, SUMBER);
  s.addNotes("Hasil Tabel 5 dan Gambar 9 paper. Korelasi uji turun ke 0,60 karena subjektivitas label ahli dan jumlah kelas uninterpretable yang kecil. Paper menyebut AISQA sebagai interpolasi yang menghaluskan keputusan ahli berdasarkan ciri sinyal objektif.");
}

{
  const s = pres.addSlide();
  judul(s, "AISQA lebih berkorelasi dengan salah klasifikasi alat daripada penilaian ahli");
  butir(s, [
    "3,16% rekaman (222) diputus salah oleh alat dibanding diagnosis ahli",
    "Korelasi salah klasifikasi: penilaian ahli 0,2717, AISQA 0,3664",
    "ROC interpretable vs tidak: semua fitur AUC 0,99742",
    "Fitur frekuensi saja AUC 0,94272, fitur morfologi 0,9936",
    "Setara acuan Clifford dkk. 2012 pada ECG 12 lead",
  ], { w: 4.6, fontSize: 14 });
  gambar(s, "output/fig13_roc.png", 5.6, 1.3, 3.6, 2.7, "Gambar 13 paper: ROC per kelompok fitur dibanding acuan Clifford dkk.");
  sumber(s, SUMBER);
  s.addNotes("Makin buruk kualitas, makin besar peluang alat salah. Ambang AISQA bisa dipakai memicu pengulangan pengukuran: Gambar 12 paper menunjukkan trade-off antara persentase pengulangan dan salah klasifikasi yang tersisa. Fitur frekuensi sendirian lemah karena ambang kerasnya tidak cocok untuk rantai pengukuran alat ini.");
}

{
  const s = pres.addSlide();
  judul(s, "Gerbang kualitas paper ini aman untuk sistem yang mengklasifikasi aritmia");
  butir(s, [
    "Sama dengan PA: single-lead, R-peak Pan dan Tompkins, rekaman 200 Hz",
    "Bisa diadopsi di firmware: HR 40 sampai 150, segmen minimal 30 detik, cek polaritas",
    "Artefak per jendela 5 detik lewat korelasi FFT dan eCDF, bukan keteraturan RR",
    "Jadi segmen aritmia tidak dibuang, berbeda dari SQI berbasis template QRS",
    "Fitur ringan untuk ESP32: basSQI, qrsSQI, pliSQI, SNR; regresi 22 fitur terlalu berat",
    "High-pass AD8232 juga mengubah morfologi, pengaruhnya perlu diukur di rekaman resmi",
  ]);
  sumber(s, SUMBER);
  s.addNotes("Usulan konkret: tiga gerbang preprocessing paper ini dipasang sebagai penyaring rekaman sinyal tubuh, autokorelasi 30 detik yang sudah ada dibandingkan dengan korelasi FFT dan eCDF per jendela 5 detik pada rekaman resmi. Bagian regresi tidak ditiru; cukup ambang per fitur.");
}

{
  const s = pres.addSlide();
  s.background = { color: GELAP };
  s.addText("Kesimpulan", { x: 0.6, y: 0.5, w: 8.8, h: 0.7, fontFace: FONT, fontSize: 26, bold: true, color: "FFFFFF", margin: 0 });
  s.addText(
    [
      "Penilai kualitas sinyal single-lead berbasis 22 fitur multi-domain: korelasi 0,60 dengan ahli pada data uji, AUC 0,997 untuk memisahkan rekaman tak terbaca.",
      "Indeks kualitas berkorelasi dengan salah klasifikasi AF alat, sehingga bisa memicu pengulangan pengukuran.",
      "Keterbatasan: alat genggam satu menit, bukan wearable kontinu; label ahli subjektif; hanya 77 rekaman tak terbaca; belum divalidasi prospektif.",
      "Untuk PA: adopsi tiga gerbang preprocessing dan deteksi artefak yang tidak membuang irama tak teratur.",
    ].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1, paraSpaceAfter: 12 } })),
    { x: 0.6, y: 1.4, w: 8.8, h: 3.4, fontFace: FONT, fontSize: 15, color: "FFFFFF", margin: 0, valign: "top" }
  );
  s.addText(SUMBER, { x: 0.6, y: 5.0, w: 8.8, h: 0.4, fontFace: FONT, fontSize: 9, color: "C9D1E0", italic: true, margin: 0 });
  s.addNotes("Tindak lanjut: pasang gerbang HR, durasi, dan polaritas di firmware; uji deteksi artefak jendela 5 detik melawan autokorelasi 30 detik pada rekaman resmi; ukur efek high-pass AD8232 pada morfologi.");
}

pres.writeFile({ fileName: "output/deck.pptx" }).then((f) => console.log("tersimpan", f));
