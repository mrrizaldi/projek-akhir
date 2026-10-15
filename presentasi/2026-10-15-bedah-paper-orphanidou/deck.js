const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Bedah Paper Orphanidou 2015";

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

const angkaBesar = (slide, x, y, angka, label) => {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w: 2.1, h: 1.55, fill: { color: TIPIS }, line: { color: TIPIS }, rectRadius: 0.1 });
  slide.addText(angka, { x, y: y + 0.12, w: 2.1, h: 0.8, fontFace: FONT, fontSize: 36, bold: true, color: AKSEN, align: "center", margin: 0 });
  slide.addText(label, { x: x + 0.1, y: y + 0.9, w: 1.9, h: 0.55, fontFace: FONT, fontSize: 11, color: ABU, align: "center", valign: "top", margin: 0 });
};

const SUMBER = "Sumber: C. Orphanidou dkk., IEEE J. Biomed. Health Inform., vol. 19, no. 3, hlm. 832–838, 2015. DOI 10.1109/JBHI.2014.2338351";

{
  const s = pres.addSlide();
  s.background = { color: GELAP };
  s.addText("Bedah Paper", { x: 0.6, y: 0.6, w: 8.8, h: 0.5, fontFace: FONT, fontSize: 16, color: "C9D1E0", margin: 0 });
  s.addText("Signal-Quality Indices for the Electrocardiogram and Photoplethysmogram: Derivation and Applications to Wireless Monitoring", {
    x: 0.6, y: 1.15, w: 8.8, h: 1.7, fontFace: FONT, fontSize: 24, bold: true, color: "FFFFFF", margin: 0, valign: "top",
  });
  s.addText("Orphanidou, Bonnici, Charlton, Clifton, Vallance, Tarassenko (Oxford)\nIEEE Journal of Biomedical and Health Informatics, vol. 19, no. 3, Mei 2015", {
    x: 0.6, y: 2.95, w: 8.8, h: 0.8, fontFace: FONT, fontSize: 13, color: "C9D1E0", margin: 0, valign: "top",
  });
  s.addText("Muhammad Rafi Rizaldi, NRP 3123600001\nBimbingan Proyek Akhir, 15 Oktober 2026", {
    x: 0.6, y: 4.2, w: 8.8, h: 0.8, fontFace: FONT, fontSize: 13, color: "FFFFFF", margin: 0, valign: "top",
  });
  s.addNotes("Paper ini dipilih karena menjawab kebutuhan minggu ini: menilai kualitas tiap segmen rekaman sinyal tubuh dari perangkat wearable sebelum dipakai. Disitasi 353 kali menurut Scopus per 15 Oktober 2026.");
}

{
  const s = pres.addSlide();
  judul(s, "Sinyal wearable pasien bergerak lebih kotor daripada sinyal monitor ranjang");
  butir(s, [
    "Artefak gerak memicu alarm palsu, lalu alarm fatigue di bangsal",
    "Algoritma deteksi artefak yang ada spesifik satu setting klinis",
    "Pengolahan sinyal mahal daya, padahal baterai wearable terbatas",
    "Dibutuhkan penilaian real-time: segmen ini layak dihitung HR atau tidak",
    "Keluaran biner: “good” atau “bad”, agar mudah dipakai",
  ]);
  sumber(s, SUMBER);
  s.addNotes("Masalah yang diangkat: data dari pasien ambulatori jauh lebih berartefak. Deteksi artefak yang dipublikasikan umumnya dikode keras untuk satu jenis data dan monitor tertentu, jadi sulit dipakai ulang. Paper ini menawarkan satu indeks kualitas sinyal (SQI) sederhana dan dua aplikasinya: hemat daya dan estimasi laju napas.");
}

{
  const s = pres.addSlide();
  judul(s, "3.000 segmen 10 detik dilabeli manual oleh tiga penilai");
  s.addTable(
    [
      [
        { text: "Basis data", options: { bold: true, fill: { color: TIPIS } } },
        { text: "Sinyal", options: { bold: true, fill: { color: TIPIS } } },
        { text: "Sumber", options: { bold: true, fill: { color: TIPIS } } },
        { text: "Segmen", options: { bold: true, fill: { color: TIPIS } } },
      ],
      ["PhysioNet/CinC 2011", "ECG lead I, 500 Hz, 16 bit", "1.500 rekaman 12 lead", "500"],
      ["JR Oxford, Dyna-Vision", "ECG 100 Hz, elektroda basah", "11 pasien, 123 jam", "500"],
      ["JR Oxford, Equivital", "ECG 256 Hz, sabuk dada", "7 pasien, 63 jam", "500"],
      ["JR Oxford, dua sensor PPG", "PPG 75 Hz, probe jari", "19 pasien, 194 jam", "1.500"],
    ],
    { x: 0.5, y: 1.4, w: 9, colW: [2.4, 2.6, 2.3, 1.7], fontFace: FONT, fontSize: 12, color: GELAP, border: { type: "solid", color: "C9D1E0", pt: 0.75 }, rowH: 0.42 }
  );
  butir(s, [
    "Dua penilai: segmen “clinically usable” bila HR bisa dihitung yakin",
    "Penilai ketiga memutus 12,2% ECG dan 13,6% PPG yang tidak sepakat",
    "66% segmen ECG dan 55,2% segmen PPG dinilai layak pakai",
  ], { y: 3.75, h: 1.3, fontSize: 14 });
  sumber(s, SUMBER);
  s.addNotes("Data campuran: satu basis data publik dan satu studi kelayakan di RS John Radcliffe pada pasien dewasa yang bisa berjalan sendiri (skor ambulatori rata-rata 4,5 dari 5). Label dibuat tiga tahap: layak klinis atau tidak, anotasi R-peak manual, lalu pembanding keluaran detektor. Segmen dengan lebih dari satu R-peak terlewat atau salah deteksi diberi label bad.");
}

{
  const s = pres.addSlide();
  judul(s, "Tiga aturan fisiologis menyaring segmen sebelum pencocokan template");
  butir(s, [
    "Deteksi R-peak dengan Hamilton dan Tompkins, puncak PPG detektor tiga titik",
    "Aturan 1: HR hasil ekstrapolasi 10 detik di rentang 40 sampai 180 bpm",
    "Aturan 2: tidak ada jeda antar puncak lebih dari 3 detik",
    "Aturan 3: rasio interval RR terbesar terhadap terkecil di bawah 2,2",
    "Gagal satu aturan saja: segmen langsung “bad”",
    "Lolos ketiganya: lanjut pencocokan template QRS adaptif",
  ], { w: 5.4, fontSize: 15 });
  s.addImage({ path: "output/fig1_flowchart.png", x: 6.0, y: 1.35, w: 3.3, h: 3.47 });
  s.addText("Gambar 1 paper", { x: 6.0, y: 4.9, w: 3.3, h: 0.2, fontFace: FONT, fontSize: 9, color: ABU, align: "center", margin: 0 });
  sumber(s, SUMBER);
  s.addNotes("Aturan dibuat sengaja konservatif. Batas 2,2 memberi toleransi satu detak terlewat, karena HR tidak diharapkan berubah lebih dari 10% dalam 10 detik. Ketiga aturan murah secara komputasi dan bisa dijalankan di mikrokontroler.");
}

{
  const s = pres.addSlide();
  judul(s, "Keteraturan morfologi diukur lewat korelasi tiap QRS dengan template rata-rata");
  butir(s, [
    "Lebar jendela QRS = median interval RR, berpusat di tiap R-peak",
    "Template = rata-rata semua QRS dalam segmen",
    "Hitung koefisien korelasi tiap QRS terhadap template",
    "SQI = rata-rata korelasi seluruh segmen",
    "Ambang dicari di 1.000 segmen latih, validasi silang 5 lipatan, uji di 500",
  ], { w: 4.6, fontSize: 15 });
  s.addImage({ path: "output/fig2_template.png", x: 5.4, y: 1.45, w: 4.1, h: 2.32 });
  s.addText("Gambar 2 paper: ECG “good” (atas) dan “bad” (bawah) beserta template-nya", {
    x: 5.4, y: 3.85, w: 4.1, h: 0.5, fontFace: FONT, fontSize: 10, color: ABU, margin: 0, valign: "top",
  });
  sumber(s, SUMBER);
  s.addNotes("Pencocokan template mencari keteraturan, bukan bentuk QRS tertentu, sehingga tidak bergantung morfologi pasien. Segmen berartefak menghasilkan QRS yang tidak seragam, korelasinya rendah. Ambang korelasi diuji dari 0,5 sampai 1.");
}

{
  const s = pres.addSlide();
  judul(s, "SQI mencapai sensitivitas 94% dan spesifisitas 97% untuk ECG");
  angkaBesar(s, 0.5, 1.5, "0,66", "ambang korelasi ECG");
  angkaBesar(s, 2.8, 1.5, "94%", "sensitivitas ECG, segmen bad terdeteksi");
  angkaBesar(s, 5.1, 1.5, "97%", "spesifisitas ECG, segmen good dipertahankan");
  angkaBesar(s, 7.4, 1.5, "99%", "cocok atau lebih konservatif dari anotasi manual");
  butir(s, [
    "PPG: ambang 0,86, sensitivitas 91%, spesifisitas 95%",
    "Konservatif: lebih memilih membuang segmen daripada meloloskan artefak",
    "Kinerja terikat pada detektor puncak yang dipakai",
  ], { y: 3.4, h: 1.5, fontSize: 15 });
  sumber(s, SUMBER);
  s.addNotes("Sensitivitas di sini adalah proporsi segmen bad yang benar dikenali bad, spesifisitas proporsi segmen good yang benar dikenali good. Untuk PPG hasilnya sedikit lebih rendah karena morfologinya lebih bervariasi.");
}

{
  const s = pres.addSlide();
  judul(s, "Duty cycling berbasis SQI memangkas waktu rekam 79 sampai 94% dengan rugi HR 4 sampai 5%");
  butir(s, [
    "Skenario: satu HR andal dari 10 detik “good” cukup per jendela 5 menit",
    "Strategi A: rekam maksimal 150 detik, berhenti begitu segmen good ditemukan",
    "Strategi B: begitu segmen good ditemukan, jeda 290 detik",
  ], { h: 1.4, fontSize: 14 });
  s.addTable(
    [
      [
        { text: "Basis data", options: { bold: true, fill: { color: TIPIS } } },
        { text: "HR andal, kontinu", options: { bold: true, fill: { color: TIPIS } } },
        { text: "HR andal, Strategi A", options: { bold: true, fill: { color: TIPIS } } },
        { text: "Waktu rekam, Strategi A", options: { bold: true, fill: { color: TIPIS } } },
      ],
      ["ECG Dyna-Vision", "77%", "72%", "18%"],
      ["ECG Equivital", "94%", "90%", "6%"],
      ["PPG Nonin", "71%", "67%", "21%"],
      ["PPG Equivital", "97%", "93%", "7%"],
    ],
    { x: 0.5, y: 2.9, w: 9, colW: [2.4, 2.2, 2.2, 2.2], fontFace: FONT, fontSize: 12, color: GELAP, border: { type: "solid", color: "C9D1E0", pt: 0.75 }, rowH: 0.38, align: "center" }
  );
  s.addText("Strategi B lengkap di paper, Tabel I. Rekaman kontinu pun hanya memberi HR andal di 71 sampai 97% jendela.", {
    x: 0.5, y: 4.85, w: 9, h: 0.3, fontFace: FONT, fontSize: 10, color: ABU, margin: 0,
  });
  sumber(s, SUMBER);
  s.addNotes("Daya diasumsikan sebanding waktu rekam. Yang menarik: bahkan rekaman kontinu tidak mencapai 100% jendela andal karena artefak panjang, jadi rugi 4 sampai 5% akibat duty cycling kecil dibanding rugi akibat artefak itu sendiri. Pengujian retrospektif pada seluruh rekaman, jendela SQI 10 detik digeser 1 detik.");
}

{
  const s = pres.addSlide();
  judul(s, "SQI yang sama menurunkan galat estimasi laju napas dari PPG");
  butir(s, [
    "Jendela 60 detik dikelaskan menurut durasi artefak kontinu di dalamnya",
    "Galat absolut rata-rata turun seiring artefak yang diizinkan makin pendek",
    "Tanpa artefak hanya 6.953 estimasi (31%), semua jendela 22.172 (100%)",
    "Trade-off: estimasi lebih jarang tetapi lebih andal, dipilih sesuai akuitas pasien",
  ], { w: 5.0, fontSize: 15 });
  s.addImage({ path: "output/fig6_mae.png", x: 5.8, y: 1.4, w: 3.7, h: 1.81 });
  s.addText("Gambar 6 paper: galat absolut rata-rata laju napas (bpm) per kelas durasi artefak", {
    x: 5.8, y: 3.32, w: 3.7, h: 0.5, fontFace: FONT, fontSize: 10, color: ABU, margin: 0, valign: "top",
  });
  sumber(s, SUMBER);
  s.addNotes("Bagian ini di luar fokus PA karena memakai PPG dan laju napas, tetapi polanya sama: kualitas sinyal menentukan seberapa sering kita boleh percaya pada turunan sinyal. Angka dari Tabel II paper.");
}

{
  const s = pres.addSlide();
  judul(s, "Tiga aturan kelayakan dan korelasi template bisa dipakai pada rekaman sinyal tubuh PA");
  butir(s, [
    "Sudah ada di PA: detektor R-peak dan autokorelasi per jendela 30 detik",
    "Bisa diadopsi langsung: aturan HR 40 sampai 180, jeda 3 detik, rasio RR 2,2",
    "Beda: paper mengkorelasikan tiap QRS ke template, PA mengautokorelasi jendela",
    "Jendela 10 detik paper lebih peka ke artefak pendek daripada 30 detik",
    "Duty cycling paper menguatkan rencana hemat daya saat WiFi mati",
    "Awas: paper menyatakan SQI ini cenderung gagal pada fibrilasi atrium",
  ]);
  sumber(s, SUMBER);
  s.addNotes("Poin terakhir penting untuk PA yang justru mengklasifikasi aritmia: aturan rasio RR dan korelasi template menolak irama tak teratur sebagai bad. Kalau diadopsi mentah, segmen aritmia bisa dibuang sebelum sampai ke model. Perlu dipisahkan antara artefak dan irama tak teratur, misalnya SQI hanya memveto bila morfologi QRS rusak, bukan bila intervalnya tak teratur.");
}

{
  const s = pres.addSlide();
  s.background = { color: GELAP };
  s.addText("Kesimpulan", { x: 0.6, y: 0.5, w: 8.8, h: 0.7, fontFace: FONT, fontSize: 26, bold: true, color: "FFFFFF", margin: 0 });
  s.addText(
    [
      "SQI sederhana, real-time, dan tidak bergantung morfologi pasien: sensitivitas 94%, spesifisitas 97% pada ECG wearable.",
      "Dua aplikasi terbukti: hemat daya hingga 94% waktu rekam, dan estimasi laju napas lebih andal.",
      "Keterbatasan: terikat detektor puncak, data rawat inap, dan belum menangani fibrilasi atrium.",
      "Untuk PA: adopsi aturan kelayakan di firmware, bandingkan autokorelasi 30 detik dengan korelasi template 10 detik pada rekaman resmi.",
    ].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1, paraSpaceAfter: 12 } })),
    { x: 0.6, y: 1.4, w: 8.8, h: 3.4, fontFace: FONT, fontSize: 15, color: "FFFFFF", margin: 0, valign: "top" }
  );
  s.addText(SUMBER, { x: 0.6, y: 5.0, w: 8.8, h: 0.4, fontFace: FONT, fontSize: 9, color: "C9D1E0", italic: true, margin: 0 });
  s.addNotes("Tindak lanjut yang diusulkan: pasang tiga aturan kelayakan sebagai penyaring pertama rekaman sinyal tubuh, lalu uji apakah korelasi template memberi hasil lebih baik daripada autokorelasi pada rekaman resmi yang akan diambil.");
}

pres.writeFile({ fileName: "output/deck.pptx" }).then((f) => console.log("tersimpan", f));
