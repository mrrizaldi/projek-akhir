# Crosscheck metrik kualitas akuisisi ECG terhadap standar dan literatur

Lingkup: rantai AD8232 ke ADC 12-bit ESP32-S3 pada 360 Hz, Lead II, elektroda wet-gel, subjek sehat duduk diam, satu sesi 927 s. Kriteria yang diperiksa adalah kriteria offline Bab 4 dan gerbang real-time firmware (lihat `laporan/buku-pa/bab/bab4.tex` baris 580–611 dan 881).

Konvensi status sumber: **[TL]** = teks lengkap dibaca (PDF atau full text PMC/HTML penerbit), **[AB]** = hanya abstrak, **[SK]** = kutipan sekunder (isi standar/paper dikutip oleh sumber lain, teks aslinya tidak dibaca).

Konversi yang dipakai di bawah (dari angka di brief): 1 count = 0,757 mV / 1.100 ≈ 0,688 µV ekuivalen masukan. Skala penuh ADC 4.095 count ≈ 3,10 V di ADC ≈ 2,82 mV p-p ekuivalen masukan.

---

## 1. Tabel crosscheck

| # | Metrik / cara ukur kami | Praktik standar / literatur (sumber, halaman/tabel) | Status | Saran konkret |
|---|---|---|---|---|
| 1 | **Bandpass Butterworth kausal orde 4, 0,5–40 Hz** (fase tidak linear). | AHA 1990 (dikutip Buendía-Fuentes 2012): respons rata 1–30 Hz, −3 dB pada ≤0,67 Hz dan ≥150 Hz; HPF 0,5 Hz menggeser fase harmonik 1–6 dan mendistorsi ST [buendiafuentes2012, bagian Diskusi, TL]. Kligfield 2007 (AHA/ACCF/HRS): HPF 0,05 Hz, boleh dinaikkan ke 0,67 Hz hanya dengan filter digital linear zero-phase [SK, teks asli tidak terbaca]. Pita 0,5–40 Hz dipakai perangkat single-lead komersial pada CinC 2017 (AliveCor: "bandwidth 0.5-40 Hz and a ± 5 mV dynamic range", clifford2017 hlm. 1) [TL], BITalino (wagner2021 §2.2) [TL], dan sebagai pita SNR Joutsen 2024 (hlm. 5) [TL]. | **Beda tapi dapat dipertanggungjawabkan** | Nyatakan eksplisit di Bab 3/4: perangkat untuk **ritme/HR dan klasifikasi detak**, bukan analisis ST. Distorsi fase konsisten di data latih dan perangkat karena pelatihan memakai `sosfilt`/`lfilter` kausal yang sama (`model/src/preprocessing.py` baris 21–41; diperiksa). Rujuk CinC 2017 sebagai preseden pita 0,5–40 Hz single-lead. Jangan mengklaim kualitas diagnostik ST. |
| 2 | **Ayunan ADC absolut** (maks − min, count dan mV); <150 count = tak ada biopotensial; ECG sehat ≈2 mV ≈3.000 count. | Tidak ada SQI baku yang memakai ayunan absolut sebagai kriteria. Paling dekat: QC "low energy" Gajdzik 2026 (RMS bergerak 1 s < 25% median RMS ditandai invalid, hlm. 59–60) [TL]; Lueken 2023 memasukkan "mean R-peak amplitude" sebagai fitur (Tabel fitur, hlm. 12) [TL]. Standar mengukur **rentang dinamis**, bukan ayunan: IEC 60601-2-25 mensyaratkan rentang dinamis minimum ±5 mV tanpa clipping (Raus-Jarzabek 2025 §3.7) [TL, kutipan sekunder isi standar]; IEC 60601-2-27 punya butir 201.12.1.101.2 "Dynamic range and differential offset voltage" (Raus-Jarzabek 2025 §2.1) [TL; angka butir 2-27 tidak terbaca]. | **Sesuai sebagai detektor "ada sinyal"; Kurang untuk rentang dinamis** | Pertahankan ayunan sebagai gerbang "ada biopotensial". Tambahkan satu kalimat rentang dinamis: masukan efektif ≈2,82 mV p-p; dengan garis dasar ≈1.900 count (Bab 4 baris 624), ruang ke atas ≈(4.095−1.900)×0,688 µV ≈1,5 mV dan ke bawah ≈1,3 mV, jauh di bawah ±5 mV. Ini menjelaskan sampel jenuh di puncak R (ADC maks 4.095 di keempat rekaman). Lihat Celah 2. |
| 3 | **Dengung 50 Hz** = % energi pita 50 Hz terhadap energi pita ECG 0,5–40 Hz; lulus <15%. Firmware: dengung ≤500 count. | Konstruksi rasio **identik** dengan PLIratio = P(49–51 Hz)/P(0,5–40 Hz) pada Gajdzik 2026 (AD8232 + ADC 12-bit ESP32, gain ≈1.100; persamaan hlm. 59–60, Tabel 6 hlm. 62) [TL]. Nilai AD8232 di sana 0,0028–0,0046% (sinyal simulator, bukan tubuh), dan **tidak ada ambang lulus**. Kramer 2022 (ECGAssess) memakai SNR = P(2–40)/[P(0–2)+P(40–250)], ambang 0,5 dB dipilih visual dari data latih (§2.3.3) [TL]. Li 2008/Zhao 2018: interferensi jala-jala dideteksi tidak langsung lewat kSQI < 5 (Li 2008 §2.1.3; Zhao 2018 hlm. 5) [TL]. Syversen 2024: ambang PLI tempat SQI publik mulai menolak sinyal sangat bervariasi, 0,70–10,71 dB (Tabel 1, hlm. 3) [TL]. Rahman 2022: belum ada ambang SQI baku yang berlaku lintas dataset (§ Pendahuluan) [TL]. | **Beda tapi dapat dipertanggungjawabkan** | Rujuk Gajdzik 2026 sebagai preseden definisi. Tulis ambang 15% sebagai ambang empiris proyek (setara rasio pita ECG/50 Hz ≈ 8,2 dB) dan sebut bahwa literatur tidak memberi ambang baku. Lebih kuat lagi bila ambang 15% diturunkan dari data rekaman uji coba yang terganggu vs bersih (seperti ambang jenuh 0,1% yang sudah punya alasan data). Laporkan juga apakah rasio dihitung dari ADC mentah (sebelum bandpass): sebutkan di teks. |
| 4 | **R-peak Pan-Tompkins; proporsi interval RR setara 30–200 BPM > 90%** (atas seluruh rekaman atau per segmen). | Orphanidou 2015 (aturan feasibility per **jendela 10 s**): HR 40–180 bpm, jeda RR maks 3 s, rasio RR maks/min < 2,2 (hlm. 834) [TL]. Kramer 2022: HR 24–300 bpm per 10 s (§2.3.2) [TL]. Rentang 30–200 bpm adalah rentang minimum heart-rate meter ANSI/AAMI EC13 (edisi 1987 butir 3.2.7, dikutip lewat paten; WebSearch) [SK]. Li 2008 dan Clifford 2011 menghitung SQI per jendela 10 s (Li 2008 §2.1.1; Clifford 2011 hlm. 286) [TL]. | **Beda tapi dapat dipertanggungjawabkan** (rentang); **Kurang** (granularitas) | Rentang 30–200 sah, cocokkan ke EC13. Tambahkan evaluasi **per jendela 10 s** dengan tiga aturan Orphanidou, laporkan % jendela lulus. Murah: R-peak sudah ada. |
| 5 | **Autokorelasi energi pita QRS** (median per 30 s), lulus > 0,25. | Tidak ditemukan di literatur sebagai SQI baku. Pembanding terdekat: korelasi rata-rata tiap QRS terhadap template rata-rata per 10 s, ambang **0,66** (Orphanidou 2015 hlm. 835–836; Se 94%, Sp 97% terhadap anotasi manual) [TL]; bSQI = kesepakatan dua detektor dalam jendela 150 ms (Li 2008 §2.1.1) [TL]; qSQI Zhao 2018: optimal > 90% (hlm. 4) [TL]. | **Kurang, perlu ditambah** | Ambang 0,25 tidak punya rujukan dan R4 lolos tipis (0,28). Tambahkan korelasi template Orphanidou (ambang 0,66) sebagai SQI morfologi yang berujukan; autokorelasi boleh tetap sebagai metrik pelengkap. Bila ingin bSQI, Pan-Tompkins vs detektor kedua (mis. Hamilton) dengan toleransi 150 ms. |
| 6 | **Sampel jenuh** (di batas ADC) dilaporkan; ditandai bila > 0,1%. | Clifford 2011: pSQI = persentase sinyal yang tampak garis datar (dx/dt < 1 mV) (hlm. 286) [TL]; Kramer 2022: sinyal ditolak bila satu jendela 0,2 s seluruhnya konstan (§2.3.1) [TL]; Gajdzik 2026: sampel flatline/energi rendah ditandai invalid, segmen 10 s ditolak bila > 30% invalid (hlm. 59–60) [TL]. | **Sesuai** (semangatnya) | Pertahankan. Tambahkan deteksi flatline (run konstan ≥0,2 s) di samping hitungan rail, karena lead-off parsial bisa datar di nilai tengah, bukan di rail. |
| 7 | **Status Berhasil / Bersinyal / Gagal** per rekaman. | Skema bertingkat lazim: Zhao 2018 optimal/suspicious/unqualified (hlm. 4–6) [TL]; CinC 2011 acceptable/indeterminate/unacceptable (Silva 2011 hlm. 274; Clifford 2011 hlm. 286) [TL]. Unit penilaian di literatur = segmen 10 s, bukan seluruh rekaman. | **Sesuai** | Tambahkan ringkasan per segmen 10 s (% segmen per status) di samping status rekaman. |
| 8 | **Gerbang real-time**: lead-off AD8232, ayunan bersih ≥60 count (≈41 µV), dengung ≤500 count, kontak baik 60 s, RR 300–1.500 ms (40–200 bpm) dan \|ΔRR\| ≤ 200 ms selama 30 s. | RR 300–1.500 ms setara dengan aturan HR Orphanidou (40–180 bpm) [TL]. **Namun** syarat \|ΔRR\| ≤ 200 ms dan aturan berbasis keteraturan RR menolak ritme tidak teratur; Orphanidou sendiri menyatakan "the algorithm is unlikely to perform well on patients exhibiting atrial fibrillation" (hlm. 838) [TL]. Behar 2013 secara khusus membahas SQI saat aritmia [AB, judul saja; teks tidak terbaca]. | **Beda tapi dapat dipertanggungjawabkan** untuk subjek sehat; **berisiko** untuk tujuan klasifikasi aritmia | Nyatakan di Bab 3/4 bahwa gerbang ΔRR hanya dipakai untuk **fase kalibrasi** (bukan untuk menolak detak setelah kalibrasi, sesuai Bab 4 baris 881). Sebut batasannya: pasien AF/ektopik sering bisa tertahan di fase kalibrasi. |
| 9 | **Akurasi HR/R-peak**: tidak ada perangkat acuan, R-peak tidak divalidasi. | Standar: ANSI/AAMI EC13 akurasi HR ±10% atau ±5 bpm, mana yang lebih besar (Solbiati 2025 §2, Areia 2021 §Metode) [SK]; IEC 60601-2-27 butir 201.12.1.101.15 "HR range and accuracy, QRS detection range" (Raus-Jarzabek 2025 §2.1) [TL; angka butir tidak terbaca]. Praktik paper: rekaman simultan dengan acuan klinis + Bland-Altman/ICC (Wagner 2021: 23 subjek, duduk, ~35 menit, ICC > 0,9 dan LoA; §2.1, §4.3–4.4) [TL]; MAE ≤ 5 bpm sesuai EC13 (Areia 2021: 29 subjek) [TL]; Polar H10 vs Lead II, r > 0,99 (Chung 2026: 26 subjek) [TL]; deteksi RR dibandingkan **inspeksi visual ECG mentah**, kualitas RR = proporsi RR terdeteksi benar (Gilgen-Ammann 2019: 10 subjek; Polar H10 99,6%) [AB]; tanpa anotasi manual, Gajdzik 2026 memakai simulator pasien dan membandingkan jumlah detak terhadap jumlah nominal (deviasi −0,13% s.d. +0,21%, Tabel 3 hlm. 60–61) [TL]. Paper ESP32-S3 + AD8232 tanpa subjek dan tanpa acuan menulis eksplisit "Table 4 therefore records validation status rather than accuracy" (Torad 2026 §4) [TL]. | **Kurang, perlu ditambah** | Minimum yang bisa diterima tanpa alat baru: **anotasi manual R-peak** atas seluruh 927 s (≈1.200 detak, semi-otomatis: koreksi keluaran Pan-Tompkins pada plot) lalu hitung Se dan +P dengan toleransi 150 ms (gaya EC57/bSQI). Lebih baik: rekam ulang singkat simultan dengan Polar H10 (literatur memvalidasinya) dan laporkan Bland-Altman HR serta % jendela dalam ±5 bpm/±10% (EC13). Bila tidak sempat, tulis seperti Torad 2026: hasil = status fungsional, bukan akurasi. |
| 10 | **Derau intrinsik dan CMRR** tidak diukur. | IEC 60601-2-25: derau sistem ≤ 30 µV p-p dan ≤ 15 µV RMS dalam 10 s, masukan dihubung-singkat (Raus-Jarzabek 2025 §3.4) [TL, kutipan sekunder isi standar]; CMRR ≈ 89–90 dB pada 50/60 Hz (Raus-Jarzabek 2025 §1, mengutip Campillo) [TL, sekunder]. IEC 60601-2-27 punya rangkaian uji CMR (Figure 201.107) dan definisi CMR (201.3.201, hlm. 9 pratinjau) [TL pratinjau; angka tidak ada]. Joutsen 2024 mengukur derau p-p dan daya total pada kanal tanpa sinyal (Tabel 5) [TL]. | **Kurang, perlu ditambah** (derau); CMRR boleh dinyatakan tidak diuji | Uji bangku 10 s dengan IN+, IN−, dan RLD dihubung bersama (atau lewat jaringan resistor): hitung p-p dan RMS dalam µV ekuivalen masukan. Batas 30 µV p-p ≈ 44 count dan 15 µV RMS ≈ 22 count. Tanpa alat tambahan. CMRR: sebut spesifikasi datasheet AD8232 dan bahwa CMRR sistem tidak diuji. |

---

## 2. Daftar sumber

### Standar dan dokumen regulasi

**fda1998** — Guidance for Industry: Cardiac Monitor Guidance (including Cardiotachometer and Rate Alarm). FDA CDRH, 5 Nov 1998. URL: https://www.fda.gov/media/71947/download. Scopus: –. **[TL]**. PDF: `laporan/pustaka/belum-dirujuk/riset-pengukuran/akuisisi/fda_1998.pdf`.
- Kutipan (hlm. 1): "This guidance applies to most of the cardiac monitors covered by the ANSI/AAMI EC13-1992 standard for Cardiac Monitors, Heart Rate Meters, and Alarms (EC13 standard)."
- Kutipan (hlm. 1): pengecualian lingkup EC13 mencakup "devices for monitoring ambulatory ECG".
- Catatan: dokumen ini **tidak** memuat angka syarat EC13; ia hanya meminta uji kesesuaian EC13 atau uji banding dengan predicate.

**iec27_2011** — IEC 60601-2-27:2011 Ed. 3.0, Particular requirements for the basic safety and essential performance of electrocardiographic monitoring equipment. Pratinjau resmi (VDE). Scopus: –. **[TL pratinjau saja; butir angka berbayar]**. PDF: `.../akuisisi/iec_60601-2-27_2011_preview.pdf`.
- Kutipan (201.1.1 Scope, hlm. 7): "This standard is not applicable to electrocardiographic monitors for home use. However, MANUFACTURERS should consider using relevant clauses of this standard as appropriate for their INTENDED USE."
- Kutipan (hlm. 7): "Ambulatory ("Holter") monitors, fetal heart rate monitoring, pulse plethysmographic devices, and other ECG recording equipment are outside the scope of this particular standard."
- Daftar isi: Figure 201.106 High frequency response, Figure 201.107 Test circuit for COMMON MODE REJECTION, Figure 201.110 Test waveforms for T-wave rejection.

**rausjarzabek2025** — Raus-Jarzabek E, Czerw M, Skowronek A, Dąbrowska-Boruch A, Jamro E, Olejarczyk E. A Practical Guide to ECG Device Performance Testing According to International Standards. *Electronics* 14(19):3878, 2025. DOI 10.3390/electronics14193878. Scopus 105019201211. **[TL, HTML penerbit lewat browser; PDF tidak dapat diunduh (403)]**.
- Kutipan (§2.1): "The following three standards for ECG equipment are currently in force: 60601-2-25 (diagnostic electrocardiographs) [1], 60601-2-47 (ambulatory ECG) [2], and 60601-2-27 (ECG patient monitors) [3]."
- Daftar butir IEC 60601-2-27:2014 (§2.1): "201.12.1.101.2—Dynamic range and differential offset voltage; ... 201.12.1.101.8—Frequency and impulse response; ... 201.12.1.101.15—HR range and accuracy, QRS detection range."
- Kutipan (§3.4): "The peak-to-peak noise amplitude measured over the 10 s window must not exceed 30 microvolts (µV)." dan "The root mean square (RMS) noise over the same interval must be no greater than 15 µV."
- Kutipan (§3.7): "the standard specifies that ECG systems must possess a minimum dynamic range of ±5 millivolts." (konteks IEC 60601-2-25)
- Kutipan (§3.6.1): "the amplitude of the output for the 0.67 Hz and 40 Hz signals must not deviate by more than 10% from the amplitude observed at 10 Hz." (IEC 60601-2-25)
- Kutipan (§1): "a CMRR ≈ 93.7 dB (well above the 89 dB minimum), intrinsic channel noise ≈ 9 μVpp (<30 μV allowed)" (mengutip Campillo et al., konteks 60601-2-25).

**kligfield2007** — Kligfield P, et al. Recommendations for the standardization and interpretation of the electrocardiogram: Part I. *Circulation* 115:1306–1324, 2007. DOI 10.1161/CIRCULATIONAHA.106.180200. Scopus 33947712041. **[SK; teks asli diblokir Cloudflare di ahajournals, jacc.org, heartrhythmjournal, hrsonline]**. Isi yang beredar (ringkasan WebSearch, tidak diverifikasi verbatim): HPF 0,05 Hz; boleh 0,67 Hz atau lebih rendah bila filter digital linear zero-phase. Jangan dikutip angka atau kalimatnya di buku tanpa membaca aslinya.

**buendiafuentes2012** — Buendía-Fuentes F, Arnau-Vives MA, Arnau-Vives A, Jiménez-Jiménez Y, et al. High-Bandpass Filters in Electrocardiography: Source of Error in the Interpretation of the ST Segment. *ISRN Cardiology* 2012:706217. DOI 10.5402/2012/706217. PMC3388307. Scopus: tidak ditemukan. **[TL, full text PMC]**. Teks: `.../akuisisi/buendiafuentes_2012.txt`.
- Kutipan (Diskusi): "the AHA recommended a flat amplitude response (±6%, 0.5 dB) between 1 and 30 Hz, with an attenuation of −3 dB in frequencies ≤0.67 Hz and ≥150 Hz"
- Kutipan (Diskusi): "a 0.5 Hz high-pass filter induces discrete amplitude attenuation of the first harmonic, though primarily and most importantly it causes phase shifts in up to the fifth or sixth harmonic (phase nonlinearities)."
- Kutipan (Diskusi): "A bidirectional filter cannot happen in real time."

**aami_ec13** — ANSI/AAMI EC13:2002 Cardiac monitors, heart rate meters, and alarms. **[SK; berbayar]**.
- Via solbiati2025 (§2, Metode): "The standard defines a maximum tolerance of ±10% of the actual value or ±5 bpm, whichever is greater."
- Via areia2021 (Tujuan): "In line with the ... (ANSI/AAMI) EC13:2002 standard [27], we defined the MAE of the patch estimates to be clinically acceptable if the rates are within 5 beats per minute (bpm)".
- Rentang 30–200 bpm: hanya dari paten yang mengutip EC13 edisi 1987 butir 3.2.7 (hasil WebSearch, tidak dibaca langsung). Perlakukan sebagai belum terverifikasi.

### Signal Quality Index

**orphanidou2015** — Orphanidou C, Bonnici T, Charlton P, Clifton D, Vallance D, Tarassenko L. Signal-Quality Indices for the Electrocardiogram and Photoplethysmogram: Derivation and Applications to Wireless Monitoring. *IEEE J Biomed Health Inform* 19(3):832–838, 2015. DOI 10.1109/JBHI.2014.2338351. Scopus 84929377665. **[TL]**. PDF: `laporan/pustaka/orphanidou_2015.pdf`.
- hlm. 834: "Rule 1: The HR extrapolated from the 10-s sample must be between 40 and 180 beats per minute (bpm)."
- hlm. 834: "Rule 2: The maximum acceptable gap between successive R-peaks/PPG pulse-peaks is 3 s."
- hlm. 834: "Rule 3: The ratio of the maximum beat-to-beat interval to the minimum beat-to-beat interval within the sample should be less than 2.2."
- hlm. 834: label manual oleh dua asesor dan R-peak "manually identified by the two human experts using a custom annotation GUI".
- hlm. 836: "The optimum threshold for the average correlation coefficient was found to be 0.66 for the ECG SQI ... this corresponded to a sensitivity of 94% and specificity of 97%".
- hlm. 838: "the algorithm is unlikely to perform well on patients exhibiting atrial fibrillation (AF)".

**li2008** — Li Q, Mark RG, Clifford GD. Robust heart rate estimation from multiple asynchronous noisy sources using signal quality indices and a Kalman filter. *Physiol Meas* 29(1):15–32, 2008. DOI 10.1088/0967-3334/29/1/002. PMC2259026. Scopus 38049013310. **[TL, HTML PMC lewat browser; persamaan ambang sSQI (pers. 6) berupa gambar dan tidak terbaca]**.
- §2.1.1: "Nmatched is the number of beats that both algorithms agreed upon (within γ = 150 ms)"; jendela "w = 10 s long, centered ± 5 s around the kth beat".
- §2.1.3: "clean, sinus rhythm ECG generally has a kurtosis larger than 5 ... baseline wander and power-line interference have kurtosis lower than 5".
- §2.1.4: SDR = rasio daya "between 5 Hz and 14 Hz to the power between 5 Hz and 50 Hz".

**clifford2011** — Clifford GD, Lopez D, Li Q, Rezek I. Signal Quality Indices and Data Fusion for Determining Acceptability of Electrocardiograms Collected in Noisy Ambulatory Environments. *Computing in Cardiology* 38:285–288, 2011. Scopus 84859972933. **[TL]**. PDF: `.../akuisisi/clifford_2011.pdf`.
- hlm. 286: "Group 1 (acceptable): If ŝ ≥ 0.70, and N (F ) ≤ 1."
- hlm. 286: "3. fSQI: The ratio of power P (5-20Hz)/P (0-fn Hz)"; "6. pSQI: The percentage of the signal xm which appeared to be a flat line (dxm /dt < ǫ where ǫ =1mV)."
- Catatan: versi jurnal (Clifford et al. 2012, *Physiol Meas* 33(9):1419, Scopus 84866323283) tidak terbaca (berbayar).

**silva2011** — Silva I, Moody GB, Celi L. Improving the Quality of ECGs Collected Using Mobile Phones: The PhysioNet/Computing in Cardiology Challenge 2011. *Computing in Cardiology* 38:273–276, 2011. Scopus 84859998604. **[TL]**. PDF: `.../akuisisi/silva_2011.pdf`.
- hlm. 274: data "2,000 twelve-lead ECGs, each 10 seconds long, with standard diagnostic bandwidth (0.05-100 Hz)", "recorded at 500 samples per second".

**clifford2017** — Clifford GD, Liu C, Moody B, Lehman LH, Silva I, Li Q, Johnson AE, Mark RG. AF Classification from a Short Single Lead ECG Recording: the PhysioNet/Computing in Cardiology Challenge 2017. *Computing in Cardiology* 44, 2017. DOI 10.22489/CinC.2017.065-469. Scopus 85045094669. **[TL]**. PDF: `.../akuisisi/clifford_2017.pdf`.
- hlm. 1: data "stored as 300 Hz, 16-bit files with a bandwidth 0.5-40 Hz and a ± 5 mV dynamic range."
- hlm. 1–2: kelas "too noisy to be classified" dilabel ulang oleh pakar.

**zhao2018** — Zhao Z, Zhang Y. SQI Quality Evaluation Mechanism of Single-Lead ECG Signal Based on Simple Heuristic Fusion and Fuzzy Comprehensive Evaluation. *Front Physiol* 9:727, 2018. DOI 10.3389/fphys.2018.00727. Scopus 85048541168. **[TL]**. PDF: `.../akuisisi/zhao_2018.pdf`.
- hlm. 4: qSQI "optimal, qSQI > 90%; ECG suspicious, qSQI ∈ [60%, 90%]; unqualified, qSQI < 60%".
- hlm. 4–5: pSQI = P(5–15 Hz)/P(5–40 Hz); untuk HR 60–130 bpm "l1 = 0.5, l2 = 0.8; l3 = 0.4".
- hlm. 5: kSQI "optimal kSQI > 5"; basSQI = 1 − P(0–1 Hz)/P(0–40 Hz), "optimal, basSQI ∈ [0.95, 1]; ECG suspicious, basSQI ∈ [0.9, 0.95]; unqualified, basSQI < 0.9".

**behar2013** — Behar J, et al. ECG signal quality during arrhythmia and its application to false alarm reduction. *IEEE Trans Biomed Eng* 60(6):1660–1666, 2013. DOI 10.1109/TBME.2013.2240452. Scopus 84877912344. **[tidak dibaca; Scopus tidak mengembalikan abstrak, tidak OA]**. Dicatat hanya karena relevan dengan gerbang ΔRR.

**kramer2022** — Kramer L, Menon C, Elgendi M. ECGAssess: A Python-Based Toolbox to Assess ECG Lead Signal Quality. *Front Digit Health* 4:847555, 2022. DOI 10.3389/fdgth.2022.847555. PMC9120362. Scopus 85131240007. **[TL, full text PMC]**. Teks: `.../akuisisi/kramer_2022.txt`.
- §2.3.1: sinyal stasioner bila maks = min dalam jendela 0,2 s.
- §2.3.2: "If the heart rate was between 24 and 300 bpm, the signal was declared passed".
- §2.3.3: SNR = ΣPSD(2–40 Hz) / [ΣPSD(0–2 Hz) + ΣPSD(40–250 Hz)]; "Visually, the SNR threshold value of 0.5 dB is selected."

**rahman2022** — Rahman S, Karmakar C, Natgunanathan I, Yearwood J, Palaniswami M. Robustness of electrocardiogram signal quality indices. *J R Soc Interface* 19:20220012, 2022. DOI 10.1098/rsif.2022.0012. PMC9006023. Scopus 85128156811. **[TL, full text PMC]**. Teks: `.../akuisisi/rahman_2022.txt`.
- Pendahuluan: "A few researchers have sought to determine the standard threshold and window sizes for SSQI measurements in diverse datasets; however, they have not found a gold standard that works for multiple datasets".

**syversen2024** — Syversen AB, Zhang Z, Batty JA, Kaisti M, Jayne D, Wong DC. Assessment of ECG Signal Quality Index Algorithms Using Synthetic ECG Data. *Computing in Cardiology* 2024. DOI 10.22489/CinC.2024.270. Scopus 105028373590. **[TL]**. PDF: `.../akuisisi/syversen_2024.pdf`.
- Tabel 1 (hlm. 3): ambang PLI menuju "unacceptable": Orphanidou 4,13 dB, Zhao 10,71 dB, Kramer 0,70 dB, Elgendi 0,70 dB.
- hlm. 3: "the tested SQIs were inconsistent with each other and with an expert opinion."

**lueken2023** — Lueken M, Gramlich M, Leonhardt S, Marx N, Zink MD. Automated Signal Quality Assessment of Single-Lead ECG Recordings for Early Detection of Silent Atrial Fibrillation. *Sensors* 23:5618, 2023. DOI 10.3390/s23125618. Scopus 85163942520. **[TL]**. PDF: `laporan/pustaka/lueken_2023.pdf`.
- Tabel fitur (hlm. 12): basSQI dan qrsSQI "according to [15]" (Clifford 2012), "pliSQI SQI for power-line interference according to [38]", "mean R-peak amplitude".

### Pengukuran SNR dan interferensi jala-jala

**gajdzik2026** — Gajdzik F, Kimbar M, Krowicki P. Comparative assessment of AD8232- and MAX30003-based ECG acquisition paths using synthetic ECG signals. *Acta Bioeng Biomech* 28(3):54–69, 2026. DOI 10.37190/abb/231067. Scopus 105054295912. **[TL]**. PDF: `.../akuisisi/gajdzik_2026.pdf`.
- Tabel spesifikasi: AD8232 "Nominal voltage gain Approximately 1,100 V/V", ADC "12 bit" ESP32 dengan atenuasi 11 dB.
- hlm. 59–60: "P50 Hz denotes the power in the 49.00–51.00 Hz band corresponding to power-line interference"; PLIratio = P50Hz/PECG, PECG = daya 0,50–40,00 Hz.
- hlm. 59–60: sampel invalid bila "the RMS value fell below 25% of the median moving RMS"; "A 10 s segment was rejected if the proportion of samples marked as invalid exceeded 30%".
- hlm. 59–60: "Because no independent manual R-wave annotations were available, the QRS detector was validated by comparing the number of detected beats with the expected number derived from the nominal simulator heart rate".
- hlm. 62–63: "For AD8232, its values ranged from 0.0028% to 0.0046%" (PLIratio, sinyal simulator).
- Catatan: tidak ada subjek manusia; tidak ada ambang lulus PLIratio.

**joutsen2024** — Joutsen A, Cömert A, Kaappa E, Vanhatalo K, Riistama J, et al. ECG signal quality in intermittent long-term dry electrode recordings with controlled motion artifacts. *Sci Rep* 14:8882, 2024. DOI 10.1038/s41598-024-56595-0. Scopus 85190649731. **[TL]**. PDF: `laporan/pustaka/joutsen_2024.pdf`.
- hlm. 5: "The SNR assessments were conducted in this 0.5 to 40 Hz frequency range."; komponen 10 dan 50 Hz beserta harmonik pertama dikecualikan dari pita.
- hlm. 5: sinyal = rentang QRS dalam jendela 100 ms; derau = RMS kanal referensi 2 s; SNRdB = 20·log10(SNR).
- Subjek: 9 sukarelawan sehat (hlm. 3).

### Validasi perangkat ECG murah dan HR

**wagner2021** — Wagner RE, Plácido da Silva H, Gramann K. Validation of a Low-Cost Electrocardiography (ECG) System for Psychophysiological Research. *Sensors* 21:4485, 2021. DOI 10.3390/s21134485. PMC8271611. Scopus 85108887171. **[TL, full text PMC]**. Teks: `.../akuisisi/wagner_2021.txt`.
- §2.1: 23 peserta sehat; duduk diam ~35 menit; rekaman simultan BITalino vs BrainAmp-ExG.
- §2.2: "The BITalino ECG sensor has a bandwidth between 0.5 and 40 Hz."
- §2.4: R-peak otomatis lalu "false R-peaks were marked and rejected" (koreksi manual).
- §4.3: kriteria "the ICC should be higher than 90% for clinical measurements ... and the lower CI should be higher than 75%".

**chung2026** — Chung V, Chopin L, Karadayi J, et al. Validity of the Polar H10 for Continuous Measures of Heart Rate and Heart Rate Synchrony Analysis. *Sensors* 26:855, 2026. DOI 10.3390/s26030855. PMC12899868. Scopus 105030019450. **[TL, full text PMC]**. Teks: `.../akuisisi/chung_2026.txt`.
- 26 peserta duduk; acuan Lead II PowerLab 1.000 Hz; R-peak otomatis "and the ECG was visually inspected to correct for peak misidentification"; korelasi, konkordansi Lin, bias Bland-Altman.

**gilgenammann2019** — Gilgen-Ammann R, Schweizer T, Wyss T. RR interval signal quality of a heart rate monitor and an ECG Holter at rest and during exercise. *Eur J Appl Physiol* 119:1525–1532, 2019. DOI 10.1007/s00421-019-04142-5. Scopus 85064623069. **[AB; berbayar]**.
- Abstrak: "both measurement systems were compared against visual inspection of the raw electrocardiography signal. The missing and wrong R-wave peak detections were counted manually ... RR interval signal quality was defined as the relative number of correctly detected RR intervals." Polar H10 99,6%; 10 subjek.

**areia2021** — Areia CM, Santos M, Vollam S, Pimentel M, Young L, et al. A Chest Patch for Continuous Vital Sign Monitoring: Clinical Validation Study During Movement and Controlled Hypoxia. *J Med Internet Res* 23(9):e27547, 2021. DOI 10.2196/27547. Scopus 85115308718. **[TL, full text PMC]**. Teks: `.../akuisisi/areia_2021.txt`. Kutipan EC13 lihat aami_ec13. 29 peserta, acuan Philips MX450 3-lead.

**solbiati2025** — Solbiati S, Mozzini F, Sahler J, et al. Estimating Heart Rate from Inertial Sensors Embedded in Smart Eyewear: A Validation Study. *Sensors* 25:4531, 2025. DOI 10.3390/s25154531. Scopus 105013341608. **[TL, full text PMC]**. Teks: `.../akuisisi/solbiati_2025.txt`. Kutipan EC13 lihat aami_ec13.

**torad2026** — Torad MA, Ahmed HE, Torad AAM, et al. ESP32-S3-Based Multimodal Wearable for Remote Vital-Sign Acquisition ... An Engineering Proof of Concept. *Sensors* 26:6047, 2026. DOI 10.3390/s26196047. Scopus 105053670763. **[TL, full text PMC]**. Teks: `.../akuisisi/torad_2026.txt`.
- §4: "No quantitative reference-device agreement is reported for heart rate, SpO2, ECG waveform, or contact temperature." dan "The AD8232 leads-off and signal-acquisition paths were functionally verified, but no quantitative ECG waveform error is available. Table 4 therefore records validation status rather than accuracy."

**panwar2025** — Panwar A, Narendra M, Arya A, et al. Integrated portable ECG monitoring system with CNN classification for early arrhythmia detection. *Front Digit Health* 7:1535335, 2025. DOI 10.3389/fdgth.2025.1535335. Scopus 105001450460. **[TL, full text PMC]**. Teks: `.../akuisisi/panwar_2025.txt`. Contoh paper AD8232 yang tidak melaporkan validasi akuisisi terhadap acuan; klasifikasi hanya dievaluasi pada MIT-BIH. Berguna sebagai pembanding celah literatur, bukan rujukan metode.

### Dicari tetapi tidak terbaca
- Narasinghe 2025 (AD8232 vs BIOPAC MP160, eIT 2025, DOI 10.1109/eIT64391.2025.11103617, Scopus 105014910660) dan Mamee 2023 (AD8232 vs BioAmp EXG Pill, DOI 10.1109/ICSPC59664.2023.10420266, Scopus 85186731909): IEEE berbayar, hanya judul.
- Teks IEC 60601-2-27/-2-47/-2-25 lengkap dan AAMI EC13: berbayar.
- Datasheet AD8232 dari analog.com: unduhan gagal dari sandbox.

---

## 3. Celah terpenting (urut dari paling berisiko di sidang)

1. **Tidak ada validasi R-peak/HR terhadap kebenaran (ground truth).** Literatur validasi akuisisi selalu punya acuan: perangkat klinis simultan (Wagner 2021, Areia 2021, Chung 2026), inspeksi visual manual (Gilgen-Ammann 2019, Orphanidou 2015), atau simulator pasien (Gajdzik 2026). EC13 dan IEC 60601-2-27 butir 201.12.1.101.15 menguji akurasi HR (±10% atau ±5 bpm, kutipan sekunder). Pertanyaan "berapa akurasi deteksi detaknya?" hampir pasti muncul. Jalan termurah: anotasi manual atas 927 s yang sudah ada, lalu Se/+P dengan toleransi 150 ms. Bila tidak dikerjakan, tulis eksplisit seperti Torad 2026 bahwa hasil adalah status fungsional, bukan akurasi.
2. **Rentang dinamis ≈2,8 mV p-p, jauh di bawah ±5 mV.** IEC 60601-2-25 (via Raus-Jarzabek 2025 §3.7) dan perangkat single-lead CinC 2017 memakai ±5 mV. Dengan gain 1.100 dan garis dasar ≈1.900 count, puncak R menyentuh 4.095 di keempat rekaman resmi. Penguji yang menghitung gain × skala ADC akan menemukannya. Akui sebagai batasan rancangan (gain tetap modul AD8232), jelaskan bahwa sampel jenuh ≤0,010% dan tidak menggeser letak R-peak, dan sebut perbaikannya (gain lebih rendah atau garis dasar di tengah skala).
3. **Ambang 15% (dengung), 0,25 (autokorelasi), 90% (RR wajar) tanpa rujukan.** Literatur sendiri menyatakan tidak ada ambang baku (Rahman 2022) dan SQI publik tidak konsisten (Syversen 2024), jadi ambang sendiri sah, **asal asal-usulnya ditulis**. Autokorelasi 0,25 paling rawan (R4 = 0,28, dan bukan SQI yang dikenal). Tambahkan korelasi template Orphanidou (0,66) dan rujuk Gajdzik 2026 untuk definisi rasio 50 Hz.
4. **Unit penilaian = seluruh rekaman, bukan segmen 10 s.** Semua SQI baku (Orphanidou, Li, Clifford, Zhao, Kramer, Gajdzik) menilai per 10 s. Rekaman 300 s yang "Berhasil" bisa menyembunyikan menit buruk. Hitung ulang per 10 s dari data yang sudah ada dan laporkan % segmen lulus.
5. **Gerbang ΔRR ≤ 200 ms dan filter kausal 0,5 Hz bertentangan dengan tujuan aritmia jika tidak dibatasi.** ΔRR menolak ritme tak teratur (Orphanidou sendiri mengakui keterbatasan pada AF, hlm. 838). HPF 0,5 Hz non-linear phase mendistorsi ST (Buendía-Fuentes 2012). Keduanya dapat dipertahankan bila teks menyatakan: ΔRR hanya gerbang kalibrasi, dan perangkat tidak dipakai untuk analisis ST; distorsi fase identik antara data latih MIT-BIH dan perangkat.

Celah sekunder (tidak masuk lima besar): derau intrinsik belum diukur, padahal uji bangku 10 s dengan masukan dihubung-singkat cukup (batas 30 µV p-p ≈ 44 count; 15 µV RMS ≈ 22 count).
