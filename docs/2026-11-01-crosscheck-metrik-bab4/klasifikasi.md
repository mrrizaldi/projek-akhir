# Crosscheck metrik dan cara ukur klasifikasi (Bab 4) terhadap standar dan literatur

Kondisi riset: 1 Nov 2026. Teks lengkap dibaca untuk 16 sumber. Tiga sumber lain hanya abstrak atau dikutip lewat sumber sekunder, dan statusnya ditandai di Bagian 2.

**Batas penting.** Teks standar ANSI/AAMI EC57 (edisi 1998/(R)2008 maupun 2012/(R)2020) dan EC38 **tidak dapat diakses** karena berbayar. Isi EC57 di laporan ini diambil dari tiga jalur:
(a) implementasi rujukan resmi `bxb`/`sumstats` dan panduan "Evaluating ECG Analyzers" karya G. B. Moody di PhysioNet. Halaman `bxb` menyatakan program itu "must be used to obtain the beat-by-beat performance statistics cited in EC38 and EC57";
(b) uraian EC57 di de Chazal 2004 dan Luz 2016;
(c) uraian EC57 di tinjauan sistematis Silva 2025.
Ketiga jalur itu menulis edisi **EC57:1998** atau **EC57:1998/(R)2008**. Tidak ditemukan sumber yang merinci perubahan pada edisi 2012. Kunci `aami_ec57_2012` di buku sebaiknya dicek ulang: klaim yang dikutip ke kunci itu sebenarnya bersumber dari edisi mana.

---

## 1. Tabel crosscheck

| # | Metrik / cara ukur kami | Praktik standar / literatur (sumber + lokasi) | Status | Saran konkret |
|---|---|---|---|---|
| 1 | Kelas biner Normal vs Aritmia (S+V+F), positif = Aritmia | EC57 tidak mendefinisikan kelas "aritmia" gabungan. Statistik detak EC57 berupa **QRS** (deteksi), **VEB** (V vs non-V) dan **SVEB** (S vs non-S), masing-masing Se dan +P, ditambah FPR untuk VEB. Lihat kolom laporan `bxb` "Q Se, Q +P, V Se, V +P, V FPR" (+ "S Se, S +P" pada opsi -L/-S) di `bxb.c`/`sumstats.c` PhysioNet, serta de Chazal 2004 hlm. 1201–1202 dan Tabel V(a),(b). Ada aturan khusus: F yang diberi label V **tidak** dihitung FP untuk VEB, dan Q→V atau Q→S tidak dihitung FP (`bxb.c`: `VFP = Nv + Sv + Ov + Xv`, `SFP = Ns + Vs + Fs + Os + Xs`; de Chazal hlm. 1201; Luz 2016 hlm. 154). Klasifikasi biner normal/abnormal di MIT-BIH inter-patient memang dipakai, tetapi jarang, misalnya tahap-1 Yan et al. 2021 (dikutip Silva 2025 hlm. 21). | Beda tapi dapat dipertanggungjawabkan | Pertahankan metrik biner sebagai metrik utama produk, tetapi tambahkan tabel "gaya EC57" di DS2: Se per kelas V, S, F (sudah ada) + FPR dari kelas N. Tulis eksplisit bahwa +P per kelas tidak terdefinisi untuk keluaran biner. Jangan bandingkan angka biner langsung dengan Se/+P SVEB/VEB paper multikelas tanpa catatan. |
| 2 | Recall, precision, F1, specificity, accuracy (accuracy dilaporkan, bukan acuan) | AAMI merekomendasikan Se, +P, FPR, dan Acc. Accuracy "can be strongly distorted by the results of the majority class", sehingga tiga ukuran pertama yang paling relevan (Luz 2016 hlm. 154; Silva 2025 hlm. 5–6). Mondéjar 2019 (hlm. 8) dan Dias 2021 (hlm. 6) melaporkan Se, +P, dan F per kelas. | Sesuai | Pakai istilah ganda Se (recall), +P (precision), FPR = 1 − Sp agar penguji yang terbiasa AAMI langsung mengenali. |
| 3 | Gross statistics (TP/FP dijumlah semua detak) | EC57 meminta statistik **gross** dan **average** (rerata per rekaman): `sumstats` mencetak baris "Gross" dan "Average" (`sumstats.c`, mengacu EC57:1998 §3.5.2–3.5.3 dan EC38 §4.2.14.4.1–2). Luz 2016 hlm. 154 menulis hasil "in a global manner ... (gross statistics) and in per sample basis". de Chazal 2004 hlm. 1202–1203 memakai gross, dan Tabel VII menyertakan hasil per rekaman. | Sesuai (gross); average kurang | Tambahkan **rerata per rekaman** (definisi `sumstats`: rerata statistik rekaman yang penyebutnya > 0) di samping median per pasien yang sudah ada. Median sah dipakai sebagai pelengkap, tetapi bukan statistik EC57. |
| 4 | DS2 rekaman penuh, 5 menit pertama tidak dibuang | Protokol EC38/EC57: "Any beat annotations that appear in the first five minutes of a record (the 'learning period') are ignored in the evaluation process" (Moody, WAG "Obtaining Test Annotation Files"). `bxb` default `-f` = 5 menit, dan opsi `-f` disebut "non-standard comparison". Paper klasifikasi inter-patient umumnya memakai seluruh detak: jumlah DS2 49.712 detak menurut pembagian de Chazal (Luz 2016 Tabel 6 hlm. 156), dan tidak satu pun dari de Chazal, Mondéjar, Dias, Saenz-Cogollo, Farag menyebut pembuangan 5 menit. | Beda tapi dapat dipertanggungjawabkan | Tulis satu kalimat bahwa protokol mengikuti konvensi literatur inter-patient (seluruh rekaman), bukan learning period EC57. Klasifikasi kami tidak adaptif per pasien, jadi learning period tidak relevan. Opsional: lampirkan angka DS2 tanpa 5 menit pertama sebagai uji sensitivitas. |
| 5 | Q dibuang (7 detak DS2) | EC57/`bxb` tidak membuang Q. Detak Q tetap dihitung untuk Se QRS dan masuk TN VEB, dan Q→V/Q→S tidak dihukum (`bxb.c` `VTN`, `VFP`, `SFP`). Mondéjar 2019 hlm. 4: "We adopted the decision of ignoring the Q AAMI class like other authors [9, 22], since it is practically non-existent. Only 15 samples belong to class Q." Dias 2021 hlm. 3 juga membuang F dan Q. | Sesuai (konvensi umum) | Cukup sebut jumlahnya (7 detak DS2) dan rujuk Mondéjar 2019. |
| 6 | Rekaman 102/104/107/217 dibuang; split DS1/DS2 de Chazal | de Chazal 2004 hlm. 1197–1198 (44 rekaman nonpacemaker, DS1 dan DS2 masing-masing 22 rekaman); Luz 2016 hlm. 154 ("records of patients using pacemakers should not be considered"); Mondéjar 2019 hlm. 4. | Sesuai | — |
| 7 | VAL = 5 rekaman DS1 (101,114,201,220,223) untuk epoch & threshold | de Chazal 2004 hlm. 1202: konfigurasi dipilih dengan cross-validation pada DS1 per rekaman (DD1, 22 fold), lalu DS2 dipakai sekali. Luz 2016 hlm. 156: "During training, use a k-patient cross validation to define model parameters". Farag 2023 §5.3 memakai VAL berbasis rekaman di DS1 (rekaman ≥200) untuk early stopping. Llamedo & Martínez 2011 (abstrak) memilih model pada himpunan "training and validation". | Sesuai | Sebut bahwa VAL dipisah **per pasien**, bukan per detak. Karena VAL hanya 5 rekaman, varians kriteria seleksi besar (Cawley & Talbot 2010 hlm. 2079). Lampirkan kurva F1 vs threshold di VAL agar terlihat apakah 0,80 berada di dataran yang stabil. |
| 8 | Threshold 0,80 = F1 maksimum di VAL | Memilih threshold di data validasi, bukan di data uji, sesuai prinsip pemisahan model selection dari evaluasi (Cawley & Talbot 2010 hlm. 2080: "model selection must be treated as an integral part of the model fitting process"). Tidak ditemukan standar EC57 tentang threshold. | Sesuai | Sebutkan juga recall dan precision di DS2 pada threshold bawaan 0,5 sebagai pembanding. Itu hanya laporan, bukan dasar pemilihan. |
| 9 | DS2 dipakai untuk ablasi | Kapoor & Narayanan 2023 [L1.3]: "Feature selection on the entire dataset results in using information about which feature performs well on the test set to make a decision". Cawley & Talbot 2010 hlm. 2080: model selection memberi "optimistic bias". Praktik ini **ada** di literatur ECG: Mondéjar 2019 Tabel 5 (semua kombinasi fitur diuji di DS2, konfigurasi terbaik dilaporkan di Tabel 6), Saenz-Cogollo 2020 hlm. 7 (jumlah fitur 6 dibaca dari kurva akurasi DS2, Gbr. 3), Farag 2023 §6.2 (varian model untuk edge dipilih dari hasil uji DS2 Tabel 4). | Kurang, perlu ditambah (bila keputusan diambil dari DS2) | Pastikan setiap nilai yang **dikunci** (window, HOS, dll.) dipilih dari VAL/DS1. Kalau ablasi DS2 hanya dilaporkan, tulis eksplisit: "ablasi di DS2 bersifat post-hoc, tidak dipakai untuk memilih". Kalau ada yang dipilih dari DS2, ulangi pemilihannya di VAL atau LOPO-CV DS1. |
| 10 | AUC (ROC) dilaporkan; positif ≈ 11% | Saito & Rehmsmeier 2015 hlm. 1: ROC "can be deceptive" pada data tak seimbang; hlm. 19: "strongly recommend PRC plots as the most informative visual analysis tool". Chicco & Jurman 2020 (Background): cek "both the PR AUC and the ROC AUC, focusing on the former"; bila ada threshold, "we recommend the usage of the Matthews correlation coefficient over F1 score, and accuracy". Chicco & Jurman 2023: MCC "should replace the ROC AUC" dan disarankan menyertakan Se, Sp, PPV, NPV. | Kurang, perlu ditambah | Tambahkan **PR-AUC (average precision)** dengan garis dasar prevalensi DS2 (≈0,11), dan **MCC** pada threshold 0,80. ROC-AUC boleh tetap ada sebagai pelengkap. |
| 11 | Posisi R di DS2 dari anotasi (oracle), bukan dari detektor | Statistik detak EC57 **end-to-end menurut desainnya**: anotasi uji berasal dari perangkat, dan `bxb` menghitung V yang terlewat detektor (`Vo`) sebagai FN VEB serta deteksi palsu berlabel V (`Ov`) sebagai FP (`bxb.c` `VFN`, `VFP`). Paper klasifikasi umumnya memakai posisi anotasi: de Chazal 2004 hlm. 1198 ("This study did not investigate the problem of heartbeat detection"), Mondéjar 2019 hlm. 4, Saenz-Cogollo 2020 hlm. 10 (Lampiran A). Dias 2021 hlm. 2–3 dan Luz 2016 hlm. 148 mengkritiknya dan menyarankan jitter. de Chazal hlm. 1205 mengakui deteksi otomatis akan menurunkan kinerja. | Beda tapi dapat dipertanggungjawabkan (untuk metrik klasifier); kurang untuk klaim sistem | Pisahkan dua tingkat: (a) **kinerja klasifier** (R oracle, sebanding dengan literatur) dan (b) **kinerja sistem** di DS2 dengan R dari Pan-Tompkins. Detak yang dicocokkan ≤150 ms; detak aritmia yang terlewat = FN, deteksi tanpa pasangan = FP. Rantai penyelarasannya sudah ada di repo (`model/scripts/eval_detected_segmentation.py` menurut CLAUDE.md). |
| 12 | Error detektor = residu sampel vs anotasi di DS1; Se Pan-Tompkins DS2 0,9469 | EC57 untuk deteksi: **QRS Se dan QRS +P**, pencocokan "time difference of up to 150 ms" (WAG "Obtaining Test Annotation Files"; `bxb -w` default 0,15 s), ditambah learning period 5 menit. DER **tidak ada** di keluaran `bxb`/`sumstats`, jadi DER adalah konvensi literatur QRS, bukan EC57. Dias 2021 hlm. 2: paper detektor QRS memakai toleransi 50 ms atau 100 ms. | Kurang, perlu ditambah | Laporkan **Se dan +P** (bukan Se saja) dengan jendela 150 ms (=54 sampel pada 360 Hz) dan sebutkan jendelanya. Sebutkan pula apakah 5 menit pertama dibuang. Se 0,9469 jauh di bawah "<0.5% error rate" yang dikutip de Chazal 2004 hlm. 1205, sehingga penguji kemungkinan besar menanyakannya. |
| 13 | Recall per kelas AAMI (V 0,92, S 0,44, F 0,07) | Se per kelas adalah inti EC57 (VEB, SVEB). F tidak punya statistik sendiri di EC57, dan F→V tidak dihukum (de Chazal hlm. 1201). | Sesuai | Jelaskan bahwa F masuk positif karena desain biner kami, bukan karena EC57. Recall F yang rendah ikut menurunkan recall agregat. |
| 14 | Recall per pasien (median) | EC57 "Average" = rerata per rekaman (`sumstats`). de Chazal Tabel VII menyertakan hasil per rekaman. | Beda tapi dapat dipertanggungjawabkan | Tambahkan rerata, atau tabel per rekaman di lampiran. |
| 15 | Kuantisasi: \|Δrecall\| float32 vs INT8 di DS2 < 0,02, merujuk Zambrano 2026 (−0,7 poin akurasi) | **Tidak ditemukan standar** ambang "negligible". Praktiknya beragam. Zambrano 2026 hlm. 14 Tabel 5: ΔAccuracy −0,7 dan R² keluaran float vs INT8 = 0,992; split per detak, dan penulis sendiri menulis "data leakage may occur" (hlm. 5). Busia 2024 hlm. 8: QAT 8-bit "0.1% drop" akurasi yang "mostly affects the sensitivity of the S class". Farag 2023 §6.2: semua model PTQ int8 "suffer a significant loss of accuracy of more than 10%", sedangkan QAT tidak; dibandingkan lewat accuracy, F1, dan sensitivity di DS2. Banjo 2026 §1: fidelitas deployment dibandingkan lewat precision dan recall. | Beda tapi dapat dipertanggungjawabkan (ambang buatan sendiri); rujukan Zambrano lemah | Sebut 0,02 sebagai **ambang rancangan sendiri**. Zambrano dipakai hanya sebagai contoh besaran, karena metriknya akurasi dengan split per detak. Laporkan Δ untuk recall, precision, F1, PR-AUC, **dan Δrecall per kelas S, V, F** (S paling peka menurut Busia), plus **persentase detak yang labelnya berbeda** antara float32 dan INT8. |

---

## 2. Daftar sumber

Status: **TL** = teks lengkap dibaca; **AB** = hanya abstrak; **SK** = hanya lewat sumber sekunder. Path PDF/XML relatif terhadap `laporan/pustaka/`. Halaman = nomor halaman jurnal bila ada, selain itu halaman PDF.

### Standar dan implementasi rujukan

**moody_wag_eval** — G. B. Moody, "Evaluating ECG Analyzers" (WFDB Applications Guide, PhysioNet, diperbarui 10 Jun 2022). https://physionet.org/physiotools/wag/eval.htm (subhalaman evnode8, evnode10). Status: TL (HTML). Kutipan:
- "the evaluation protocol allows a time difference of up to 150 ms between each pair of matching beat annotations." (evnode8, Obtaining Test Annotation Files)
- "All beat annotations are mapped during the evaluation process into the set { N, V, F, S, Q } (corresponding to normal, ventricular ectopic, ventricular fusion, supraventricular ectopic, and unclassifiable or paced beats respectively)" (evnode8)
- "Any beat annotations that appear in the first five minutes of a record (the 'learning period') are ignored in the evaluation process." (evnode8)
- "bxb compares annotation files beat by beat; its output includes QRS, VEB, and (optionally) SVEB sensitivity and positive predictivity, as well as RR interval error and shutdown statistics." (evnode10)
- "Only the statistics required by EC38 and EC57 are reported by ecgeval." (evnode10)

**physionet_bxb** — G. B. Moody, BXB(1) "ANSI/AAMI-standard beat-by-beat annotation comparator", https://physionet.org/physiotools/wag/bxb-1.htm. Sumber program `bxb.c` dan `sumstats.c` di https://github.com/bemoody/wfdb (app/). Status: TL (HTML + kode sumber). Kutipan:
- "bxb is the reference implementation of these algorithms, and must be used to obtain the beat-by-beat performance statistics cited in EC38 and EC57 in order to be in compliance with these standards (see EC38, section 5.2.14, and EC57, section 4.2)."
- "-f time Begin the comparison at the specified time (default: 5 minutes after the beginning of the record)." "-w time Set the match window (default: 0.15 seconds)".
- "The -f, -O, -t, and -w options modify the comparison algorithm used by bxb in ways not permitted by EC38 or EC57."
- `bxb.c`: `VFN = Vn + Vs + Vf + Vq + Vo + Vx; VFP = Nv + Sv + Ov + Xv; SFN = Sn + Sv + Sf + Sq + So + Sx; SFP = Ns + Vs + Fs + Os + Xs;` (huruf besar = referensi, kecil = uji, o = terlewat, O = deteksi palsu).
- `bxb.c` (komentar pemetaan): "beats which are either paced (type PACE) or fusions of paced and normal beats (type PFUS) are treated in the same way as unknown beats."
- `sumstats.c`: "derives the aggregate statistics described in sections 3.5.2 and 3.5.3 of ... ANSI/AAMI EC57:1998 ... and in sections 4.2.14.4.1 and 4.2.14.4.2 of ... EC38:1998". Keluaran memuat baris "Gross" dan "Average".

**aami_ec57** — ANSI/AAMI EC57 (1998/(R)2008; 2012/(R)2020). Status: **tidak diakses** (berbayar). Isinya hanya diketahui lewat sumber di atas dan di bawah.

### Protokol inter-patient dan survei

**dechazal_2004** — P. de Chazal, M. O'Dwyer, R. B. Reilly, "Automatic classification of heartbeats using ECG morphology and heartbeat interval features", IEEE TBME 51(7):1196–1206, 2004. DOI 10.1109/TBME.2004.827359. Scopus 2942709662. Status: TL. PDF: `belum-dirujuk/riset-pengukuran/klasifikasi/dechazal_2004.pdf` (repositori TARA, TCD). Kutipan:
- hlm. 1198: "This study did not investigate the problem of heartbeat detection from the ECG; instead we have utilized the heartbeat fiducial point times provided with the MIT-BIH arrhythmia database."
- hlm. 1201: "In accordance with the AAMI recommendations, two sets of performance measurements were calculated. These performance measures focus on the ability of algorithms to distinguish VEBs from non-VEBs [Table V(a)] and SVEBs from non-SVEBS [Table V(b)]. It is worth noting that the AAMI-recommended calculations ... do not reward or penalize a classifier for the classification of ventricular fusion (F) or unknown beats (Q) as VEBs."
- hlm. 1202: "All aggregate performance measures for a dataset were calculated by giving each heartbeat equal weighting (the so-called 'gross' statistics in [13])." ([13] = EC57:1998)
- hlm. 1203: "In accordance with AAMI recommendations, the classification performance for each recording and the gross performance figures were calculated for DS2 (test-set)".
- hlm. 1196 (abstrak): SVEB "sensitivity of 75.9%, a positive predictivity of 38.5%, and a false positive rate of 4.7%"; VEB "sensitivity was 77.7%, the positive predictivity was 81.9%".
- hlm. 1205: "Automatic heartbeat detection results in some errors in heartbeat detection (missed heartbeats, erroneously detected heartbeats, and errors in heartbeat fiducial point identification), and this will cause a reduction in the performance of the presented heartbeat classifier".

**luz_2016** — E. J. da S. Luz, W. R. Schwartz, G. Cámara-Chávez, D. Menotti, "ECG-based heartbeat classification for arrhythmia detection: A survey", Comput. Methods Programs Biomed. 127:144–164, 2016. DOI 10.1016/j.cmpb.2015.12.008. Scopus 84953221679. Status: TL. PDF: `.../klasifikasi/luz_2016.pdf` (Repositório UFOP). Kutipan:
- hlm. 154: "The measures recommended by AAMI for evaluating methods are: Sensitivity (Se), Positive predictivity (+P), False positive rate (FPR) and Overall accuracy (Acc). ... the overall accuracy can be strongly distorted by the results of the majority class. In this way, the first three measures are the most relevant for comparing the methods".
- hlm. 154: "it is not necessary to penalize VEB +P with the false positives Fv and Qv"; "The standard also suggests that the results should be presented in a global manner, considering that each heartbeat has the same weight (gross statistics) and in per sample basis."
- hlm. 148: "a large majority of the reviewed researches herein utilized databases in which the events related to heartbeat segmentation ... are identified and previously labeled ... the results reported by these works disregard the impact of segmentation step".
- hlm. 156 (alur kerja usulan): "Add jitter to R location annotation ... to test the robustness of the method against segmentation errors"; "During training, use a k-patient cross validation to define model parameters as proposed in [7]."

**silva_2025** — G. A. L. Silva, P. H. L. Silva, G. J. P. Moreira, V. L. S. Freitas, J. C. Gertrudes, E. J. S. Luz, "A Systematic Review of ECG Arrhythmia Classification: Adherence to Standards, Fair Evaluation, and Embedded Feasibility", arXiv:2503.07276v1, 2025 (preprint; status terbit tidak dicek). Status: TL. PDF: `.../klasifikasi/silva_2025.pdf`. Kutipan:
- hlm. 5: "The key metrics recommended by the AAMI include Sensitivity (Se), Positive Predictive Value (+P), False Positive Rate (FPR), and Global Accuracy (Acc)."
- hlm. 6: "Sensitivity, Positive Predictive Value, and False Positive Rate are prioritized as the most relevant metrics".
- hlm. 21 (Yan et al. 2021, salah satu dari 5 studi yang memenuhi AAMI + inter-patient + MIT-BIH + embedded): "the two-class CNN achieved a sensitivity of 80% and a positive predictive value of 98% for normal beats, while abnormal beats attained a sensitivity of 87% and a positive predictive value of 35%".

**mondejar_2019** — V. Mondéjar-Guerra, J. Novo, J. Rouco, M. G. Penedo, M. Ortega, "Heartbeat classification fusing temporal and morphological information of ECGs via ensemble of classifiers", Biomed. Signal Process. Control 47:41–48, 2019. DOI 10.1016/j.bspc.2018.08.007. Scopus 85051770207. Status: TL (naskah penulis, RUC UDC; halaman = PDF). PDF: `.../klasifikasi/mondejar_2019.pdf`. Kutipan:
- hlm. 4: "We adopted the decision of ignoring the Q AAMI class like other authors [9, 22], since it is practically non-existent. Only 15 samples belong to class Q."
- hlm. 4: "this work is focused on the classification step, therefore the QRS annotations included in MIT-BIH were employed."
- hlm. 8: "To adjust the penalty parameter C, a 10-fold cross-validation strategy was performed over the training dataset (DS1)"; "they do not reward or penalize a classifier for the classification of ventricular fusion (F) as (VEBs), Fv."
- hlm. 10, Tabel 5: "All the possible combinations of the five features tested ... over MIT-BIH (DS2)".

**dias_2021** — F. M. Dias, H. L. M. Monteiro, T. W. Cabral, R. Naji, M. Kuehni, E. J. da S. Luz, "Arrhythmia classification from single-lead ECG signals using the inter-patient paradigm", Comput. Methods Programs Biomed. 202:105948, 2021. DOI 10.1016/j.cmpb.2021.105948. Scopus 85100691681. Status: TL. PDF: `dias_2021.pdf` (sudah di repo). Kutipan:
- hlm. 2: "the majority of the works in the literature bypass the detection step and use the R-wave position given by a labeled database".
- hlm. 2: "works that evaluate QRS detection algorithms consider errors up to 50 ms or 100 ms [14,15]".
- hlm. 3: "Due to the small number of events in classes F and Q, both of them were excluded from this work."

**saenz_2020** — J. F. Saenz-Cogollo, M. Agelli, "Investigating Feature Selection and Random Forests for Inter-Patient Heartbeat Classification", Algorithms 13(4):75, 2020. DOI 10.3390/a13040075. Scopus 85086763772. Status: TL. PDF: `belum-dirujuk/algorithms-13-00075-v2.pdf` (sudah di repo). Kutipan:
- hlm. 6: "Performance measures from the training set are calculated with 'leave-one-patient-out' cross-validation."
- hlm. 7: "Figure 3 shows the classification performance in terms of Acc on the test set DS2 of RF classifiers that use up to ten MI-ranked features. It can be observed that the highest performance is actually achieved with just six features".

**mousavi_2019** — S. Mousavi, F. Afghah, "Inter- and Intra- Patient ECG Heartbeat Classification for Arrhythmia Detection: A Sequence to Sequence Deep Learning Approach", ICASSP 2019. DOI 10.1109/ICASSP.2019.8683140. Scopus 85068993477. Status: TL (arXiv 1812.07421v2). PDF: `.../klasifikasi/mousavi_2019.pdf`. Kutipan:
- hlm. 5: "The augmented data ... should not be considered in the validation phase as the information of the validation set may exist in the training set."
- hlm. 6: "Four main measures usually were considered in the literature ... sensitivity (SEN), positive predictive value (PPV), specificity (SPEC) (1 - False Positive Rate (FPR)) and accuracy".

**llamedo_2011** — M. Llamedo, J. P. Martínez, "Heartbeat classification using feature selection driven by database generalization criteria", IEEE TBME 58(3):616–625, 2011. DOI 10.1109/TBME.2010.2068048. Scopus 79952156441. Status: **AB** (PubMed 20729162). Teks lengkap tidak ditemukan versi terbuka. Abstrak: "The Association for the Advancement of Medical Instrumentation recommendations for class labeling and results presentation were followed. A floating feature selection algorithm was used to obtain the best performing and generalizing models in the training and validation sets".

**mar_2011** — T. Mar, S. Zaunseder, J. P. Martínez, M. Llamedo, R. Poll, "Optimization of ECG classification by means of feature selection", IEEE TBME 58(8), 2011. DOI 10.1109/TBME.2011.2113395. Scopus 79960710929. Status: **AB** (PubMed 21317067). Abstrak: "follows the Association for the Advancement of Medical Instrumentation standard EC57:1998 and the same interpatient division scheme".

**yan_2021** — Z. Yan, J. Zhou, W.-F. Wong, "Energy efficient ECG classification with spiking neural network", Biomed. Signal Process. Control 63:102170, 2021. DOI 10.1016/j.bspc.2020.102170. Scopus 85089921518. Status: **SK** (hanya lewat silva_2025 hlm. 21). Teks asli tidak dibaca.

### Pemilihan model dan kebocoran

**cawley_2010** — G. C. Cawley, N. L. C. Talbot, "On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation", JMLR 11:2079–2107, 2010. Status: TL. PDF: `.../klasifikasi/cawley_2010.pdf`. Kutipan:
- hlm. 2079: "some common performance evaluation practices are susceptible to a form of selection bias as a result of this form of over-fitting and hence are unreliable."
- hlm. 2080: "In order to avoid this bias, model selection must be treated as an integral part of the model fitting process and performed afresh every time a model is fitted to a new sample of data."

**kapoor_2023** — S. Kapoor, A. Narayanan, "Leakage and the reproducibility crisis in machine-learning-based science", Patterns 4(9):100804, 2023. DOI 10.1016/j.patter.2023.100804. Scopus 85169828210. Status: TL (Europe PMC PMC10499856, XML). Berkas: `.../klasifikasi/kapoor_2023.xml`. Kutipan (taksonomi leakage):
- "[L1.3] Feature selection on training and test set. Feature selection on the entire dataset results in using information about which feature performs well on the test set to make a decision about which features should be included in the model."
- "[L3.2] ... In the extreme (but unfortunately common) case, training and test samples come from the same people or units."
- Catatan: penyetelan hyperparameter atau threshold di data uji tidak disebut sebagai subkategori tersendiri. Analogi terdekat adalah L1.3.

### Metrik untuk data tak seimbang

**saito_2015** — T. Saito, M. Rehmsmeier, "The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets", PLoS ONE 10(3):e0118432, 2015. DOI 10.1371/journal.pone.0118432. Scopus 84928911070. Status: TL. PDF: `saito_2015.pdf` (sudah di repo). Kutipan:
- hlm. 1: "the visual interpretability of ROC plots in the context of imbalanced datasets can be deceptive with respect to conclusions about the reliability of classification performance, owing to an intuitive but wrong interpretation of specificity."
- hlm. 19: "The results of our study strongly recommend PRC plots as the most informative visual analysis tool."

**chicco_2020** — D. Chicco, G. Jurman, "The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation", BMC Genomics 21:6, 2020. DOI 10.1186/s12864-019-6413-7. Scopus 85077436560. Status: TL (Europe PMC PMC6941312, XML). Berkas: `.../klasifikasi/chicco_2020.xml`. Kutipan (Background):
- "we suggest ... evaluations by checking both the PR AUC and the ROC AUC, focusing on the former [48, 97]. If a confusion matrix threshold is at disposal, instead, we recommend the usage of the Matthews correlation coefficient over F1 score, and accuracy." (frasa awal dipotong di XML; inti kalimat persis)
- "ROC AUC presents several flaws [92], and it is sensitive to class imbalance [93]."

**chicco_2023** — D. Chicco, G. Jurman, "The Matthews correlation coefficient (MCC) should replace the ROC AUC as the standard metric for assessing binary classification", BioData Mining 16:4, 2023. DOI 10.1186/s13040-023-00322-4. Scopus 85148415559. Status: TL (Europe PMC PMC9938573, XML). Berkas: `.../klasifikasi/chicco_2023.xml`. Kutipan:
- "we explain why the Matthews correlation coefficient should replace the ROC AUC as standard statistic in all the scientific studies involving a binary classification".
- "for diagnostics purposes, we suggest to always compute and include not only the MCC, but also the confusion matrix four basic rates (sensitivity, specificity, ...)".

### Kuantisasi INT8 pada ECG edge

**zambrano_2026** — M. Zambrano-de la Torre et al., "Real-Time Cardiac Arrhythmia Classification Using TinyML on Ultra-Low-Cost Microcontrollers ...", Bioengineering 13(5):532, 2026. DOI 10.3390/bioengineering13050532. Scopus 105040260667. Status: TL. PDF: `zambrano_2026.pdf` (sudah di repo). Kutipan:
- hlm. 14, Tabel 5: Float32 akurasi 98,3%, INT8 97,6%, "∆Accuracy −0.7".
- hlm. 14: "a near-perfect linear relationship (R2 = 0.992)" antara keluaran float dan INT8.
- hlm. 5: "this strategy does not enforce inter-patient separation ... data leakage may occur, and the reported performance can be optimistically biased".

**busia_2024** — P. Busia, M. A. Scrugli, V. J.-B. Jung, L. Benini, P. Meloni, "A Tiny Transformer for Low-Power Arrhythmia Classification on Microcontrollers", IEEE TBioCAS (cover 2025). DOI 10.1109/TBCAS.2024.3401858. Scopus 85193472268. Status: TL (arXiv 2402.10748v2; halaman = PDF arXiv). PDF: `.../klasifikasi/busia_2024.pdf`. Kutipan:
- hlm. 8: "obtaining an average test accuracy of 98.97% on the clean noiseless signal, with a limited 0.1% drop from the accuracy of the full-precision models"; "The accuracy drop resulted from restricting all computations to the integer type, and it mostly affects the sensitivity of the S class".
- Catatan: evaluasi intra-patient (Tabel I: "intra-patient").

**farag_2023** — M. M. Farag, "A Tiny Matched Filter-Based CNN for Inter-Patient ECG Classification and Arrhythmia Detection at the Edge", Sensors 23(3):1365, 2023. DOI 10.3390/s23031365. Scopus 85147854971. Status: TL (Europe PMC PMC9919183, XML; halaman tidak tersedia, rujuk subbab). Berkas: `.../klasifikasi/farag_2023.xml`. Kutipan:
- §5.3: "DS1 is divided by the patient records into training and validation sets to imitate the inter-patient division of DS1 and DS2. Record numbers less than 200 are used for model training, while the remaining are used for model validation."
- §6.2: "All int8 PTQ TFLite models suffer a significant loss of accuracy of more than 10% due to weight quantization and reduced operator precision. On the other hand, int8 QAT models do not suffer the same accuracy loss."
- §6.2: varian 1–3 "have been selected for edge inference" berdasarkan "highest sensitivity of the VEB class" dan "highest sensitivity of the 'SVEB' class" di Tabel 4 (hasil uji DS2).

**banjo_2026** — O. Banjo, B. Ghoraani, "A Cascaded Quantized Spiking Neural Network for Real-Time ECG Arrhythmia Detection on Edge Hardware", Sensors 26(12):3723, 2026. DOI 10.3390/s26123723. Status: TL (Europe PMC PMC13306364, XML). Berkas: `.../klasifikasi/banjo_2026.xml`. Kutipan:
- §1: "validate deployment fidelity by comparing classification metrics (precision, recall), latency, throughput, power consumption, and resource utilization against the GPU-based implementation."
- §1: memakai "a patient-specific (intra-patient) evaluation protocol with an 80/20 train–test split". Tahap pertama berupa penyaringan "Normal vs. Abnormal".

---

## 3. Celah paling penting (urut dari paling berisiko di sidang)

1. **Metrik DS2 diukur dengan posisi R oracle, padahal klaimnya tentang perangkat.** Statistik detak EC57 bersifat end-to-end: `bxb` menghitung V yang terlewat detektor sebagai FN dan deteksi palsu berlabel V sebagai FP. Dengan Se Pan-Tompkins 0,9469, sekitar 5% detak tidak pernah sampai ke klasifier, dan itu tidak tercermin di recall 0,92 (V) maupun recall agregat. Tindakan: laporkan dua tingkat metrik, yaitu klasifier (R anotasi) dan sistem (R Pan-Tompkins, pencocokan ≤150 ms, detak aritmia yang terlewat = FN). Rantai penyelarasannya sudah tersedia di `eval_detected_segmentation.py`.
2. **Pemakaian DS2 untuk ablasi.** Kalau satu saja nilai final (window, HOS, arsitektur) dipilih dari angka DS2, terjadi bias seleksi (Cawley & Talbot 2010; Kapoor & Narayanan 2023 L1.3). Literatur juga melakukannya (Mondéjar Tabel 5, Saenz-Cogollo Gbr. 3, Farag Tabel 4), tetapi penguji yang paham inter-patient akan menanyakannya. Tindakan: tunjukkan bahwa keputusan diambil di VAL/DS1, atau beri label "post-hoc" pada ablasi DS2.
3. **Deteksi QRS hanya dilaporkan Se, dan angkanya rendah.** EC57 meminta QRS Se **dan** +P dengan jendela 150 ms, plus learning period 5 menit. Se 0,9469 jauh dari "<0.5% error rate" yang dikutip de Chazal 2004 hlm. 1205. Tindakan: laporkan Se, +P, jendela pencocokan, dan perlakuan 5 menit pertama. Jelaskan penyebab Se rendah dengan data (rekaman mana yang menyumbang FN terbanyak).
4. **Ambang kuantisasi 0,02 bersandar pada rujukan yang tidak sebanding.** Zambrano mengukur akurasi dengan split per detak (penulis sendiri mengakui leakage), dan tidak ada standar ambang. Busia menunjukkan dampak INT8 terkonsentrasi di sensitivitas kelas S. Tindakan: nyatakan 0,02 sebagai ambang rancangan sendiri. Laporkan Δ per metrik, Δrecall per kelas S/V/F, dan persentase detak yang labelnya berubah.
5. **Metrik untuk data tak seimbang dan statistik EC57 belum lengkap.** ROC-AUC tanpa PR-AUC pada prevalensi ≈11% rawan dikritik (Saito 2015; Chicco & Jurman 2020/2023). Statistik "average" EC57 juga belum ada (baru median), dan pengecualian 5 menit tidak disebut. Tindakan: tambahkan PR-AUC dengan garis prevalensi, MCC, rerata per rekaman, dan satu kalimat protokol (seluruh rekaman, Q dibuang 7 detak, mengikuti konvensi de Chazal/Mondéjar).

---

## Catatan metode riset

- Pencarian: Scopus (DOI dan TITLE-ABS-KEY), arXiv API, Europe PMC REST (teks lengkap JATS), WebSearch. Unduhan dari repositori TCD (TARA), UFOP, dan RUC UDC lewat browser otomatis.
- Tidak ditemukan dan dibaca: (a) teks EC57/EC38 edisi mana pun; (b) paper inter-patient MIT-BIH yang melaporkan klasifikasi **end-to-end** dengan detektor dan pencocokan 150 ms. Pencarian Scopus hanya menemukan Wei et al. 2024 (BioCAS, Scopus 85216235964, judul saja, tidak dibaca); (c) teks lengkap Llamedo & Martínez 2011 dan Mar 2011; (d) teks lengkap Yan et al. 2021 (klasifikasi biner normal/abnormal inter-patient).
- Sumber berbentuk XML (Europe PMC) disimpan dengan ekstensi `.xml` karena PDF-nya terhalang Cloudflare atau JS. Isinya adalah teks lengkap artikel.
