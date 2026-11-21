# Cek klaim tanpa angka (progres-pa-1 dan buku-pa)

Halaman PDF = nomor halaman berkas PDF (bukan nomor cetak). Kutipan disalin dari keluaran `pdftotext` pada halaman tersebut.

| # | Klaim | Vonis | Usulan singkat |
|---|---|---|---|
| 1 | Akurasi Mulyawan "tinggi" | didukung angka | Ganti "tinggi" dengan 98,04% pada pengujian offline |
| 2 | "baru sedikit yang dibuktikan" di MCU | didukung tanpa angka (sebagian), sitasi tidak memuat klaimnya | Sebut 3 dari 12 penelitian terkait, atau lunakkan dan ganti sitasi |
| 3 | "salah satu dari sedikit studi" (Kim) | didukung tanpa angka, hitungan internal 3 dari 12 | Sebut bahwa dari dua belas penelitian hanya tiga yang menjalankan inferensi ECG di MCU |
| 4 | "dua keperluan yang berbeda" | didukung tanpa angka, keduanya diuraikan (latih dan uji) | Tulis eksplisit "melatih dan menguji" |
| 5 | GAP "menekan parameter secara drastis", "divalidasi" Mekhfioui | angka internal ada (22.300 vs 6.417), "divalidasi" tidak didukung sumber | Ganti dengan angka, Mekhfioui hanya dirujuk sebagai pemakai GAP |
| 6 | "model yang telah teruji akurat" | tidak didukung (recall 0,7105, F1 0,6604) | Ganti dengan "telah diuji secara offline" |

## Klaim 1: akurasi Mulyawan "tinggi"
- Lokasi: `laporan/progres-pa-1/bab/bab2.tex:442` (paragraf mulai baris 435), `laporan/buku-pa/bab/bab2.tex:427` (paragraf mulai baris 420)
- Naskah: "Klasifikasi dilakukan oleh model Support Vector Machine (SVM) dengan kernel Radial Basis Function yang di-deploy pada sisi backend, dilatih menggunakan dataset MIT-BIH dan mencapai akurasi tinggi pada pengujian offline."
- Sumber: `mulyawan_2026` → `laporan/pustaka/mulyawan_2026.pdf` hlm. 124: "dibuktikan oleh nilai Akurasi 98,04% dan skor AUC mendekati 1 pada pengujian offline menggunakan dataset MIT-BIH." Hlm. 128: "Validasi offline menggunakan dataset klinis MIT-BIH Atrial Fibrillation Database membuktikan kemampuan separasi matematis yang sangat kuat dengan akurasi klasifikasi mencapai 98,04%." Abstrak hlm. 7: "model SVM mencapai akurasi sebesar 98,04%, presisi 0,98, serta recall 0,98".
- Catatan: dataset sumbernya MIT-BIH Atrial Fibrillation Database (hlm. 128), bukan MIT-BIH Arrhythmia Database. Naskah menulis "dataset MIT-BIH" sehingga tidak salah, tetapi tidak sama dengan basis data yang dipakai Bab 2 subbab MIT-BIH. Tugasnya juga biner sinus normal lawan AFib.
- Vonis: didukung angka
- Usulan kalimat: "Klasifikasi dilakukan oleh model Support Vector Machine (SVM) dengan kernel Radial Basis Function yang di-deploy pada sisi backend, dilatih menggunakan dataset MIT-BIH Atrial Fibrillation dan mencapai akurasi 98,04% pada pengujian \textit{offline}~\cite{mulyawan_2026}."

## Klaim 2: "baru sedikit yang dibuktikan"
- Lokasi: `laporan/progres-pa-1/bab/bab2.tex:7`, `laporan/buku-pa/bab/bab2.tex:7`; kalimat yang sama di `bab/bab1.tex:13` kedua buku.
- Naskah: "Model kecerdasan buatan untuk deteksi aritmia umumnya dijalankan pada perangkat keras desktop atau server, dan baru sedikit yang dibuktikan mampu melakukan inferensi real-time pada mikrokontroler low-power yang sesungguhnya digunakan dalam perangkat wearable~\cite{zambrano_2026}."
- Sumber: `zambrano_2026` → `laporan/pustaka/zambrano_2026.pdf` hlm. 2: "these approaches often rely on computationally complex architectures, large-scale datasets, extensive validation procedures, and advanced hardware resources, which substantially limits their practical deployment in infrastructure-constrained environments". Hlm. 3: "These systems are typically implemented on a wide range of hardware platforms, including ARM-based microcontrollers, system-on-chip (SoC) devices, and embedded Linux platforms such as Raspberry Pi". Pembanding: `kim_2023` → `laporan/pustaka/kim_2023.pdf` hlm. 3: "since integrating TinyML into medical and healthcare devices is an initial stage, there are very few works on it".
- Catatan: Zambrano tidak menyatakan "baru sedikit"; ia hanya menyebut pendekatan lain memerlukan perangkat keras berat. Kata "desktop atau server" tidak ada di sumber. Zambrano sendiri adalah salah satu dari penelitian yang membuktikan inferensi di MCU, jadi sitasinya memperkuat kebalikan klaim. Dukungan terdekat adalah Kim hlm. 3, tetapi cakupannya TinyML pada perangkat medis, bukan ECG.
- Hitungan internal (12 penelitian terkait di Bab 2, subbab penelitian terkait dan Tabel perbandingan, tidak termasuk baris penelitian ini): inferensi ECG berjalan di MCU fisik pada 3 penelitian, yaitu Kim 2023 (Arduino Nano 33 BLE, Cortex-M4), Zambrano 2026 (Arduino UNO ATmega328P), dan Sheeba Rani 2026 (Cortex-M4; `sheeba_rani_2026.pdf` hlm. 10 memuat "ARM Cortex-M4 (STM32F407VG Microcontroller)"). Sembilan lainnya memakai Raspberry Pi (Karri, Mekhfioui), PC server (Xie), cloud (Mulyawan), Kubernetes (Boluda-Prieto), simulasi atau tinjauan (Laiu, tinyml review, fog/edge), atau sinyal PCG bukan ECG (auskultasi).
- Vonis: didukung tanpa angka secara internal (3 dari 12); sitasi `zambrano_2026` tidak memuat klaimnya
- Usulan kalimat: "Model kecerdasan buatan untuk deteksi aritmia umumnya dijalankan pada perangkat keras yang jauh lebih kuat daripada mikrokontroler \textit{wearable}, dan hanya tiga dari dua belas penelitian terkait dalam tinjauan ini yang membuktikan inferensi ECG pada mikrokontroler~\cite{kim_2023, zambrano_2026, sheeba_rani_2026}."

## Klaim 3: "salah satu dari sedikit studi"
- Lokasi: `laporan/progres-pa-1/bab/bab2.tex:367`, `laporan/buku-pa/bab/bab2.tex:352`
- Naskah: "Penelitian tersebut merupakan salah satu dari sedikit studi yang menjalankan inferensi ECG di MCU fisik low-power." (buku-pa: "...yang benar-benar menjalankan...")
- Sumber: `kim_2023` → `laporan/pustaka/kim_2023.pdf` hlm. 3: "since integrating TinyML into medical and healthcare devices is an initial stage, there are very few works on it [31]. Furthermore, no previous work considered the TinyML-based ECG monitoring system." Hlm. 2: "this is the first study to introduce the TinyML concept into the ECG monitoring system".
- Catatan: kutipan Kim berlaku pada 2023 dan tentang TinyML di perangkat medis. Naskah Bab 2 sendiri memuat dua penelitian lain yang menjalankan inferensi ECG di MCU (Zambrano 2026, Sheeba Rani 2026), jadi "sedikit" cocok tetapi sebaiknya diberi hitungan. Sitasi pada kalimat itu belum ada (kalimat bersitasi hanya di awal paragraf, `kim_2023`).
- Vonis: didukung tanpa angka (3 dari 12, nama di Klaim 2)
- Usulan kalimat: "Penelitian tersebut menjadi salah satu dari tiga penelitian dalam tinjauan ini yang menjalankan inferensi ECG pada MCU fisik, bersama Zambrano-de la Torre et al.~\cite{zambrano_2026} dan Sheeba Rani et al.~\cite{sheeba_rani_2026}."

## Klaim 4: "dua keperluan yang berbeda"
- Lokasi: `laporan/progres-pa-1/bab/bab2.tex:329`, `laporan/buku-pa/bab/bab2.tex:314`
- Naskah: "Dalam penelitian ini, MIT-BIH Arrhythmia Database digunakan sebagai sumber data untuk dua keperluan yang berbeda. Model CNN dilatih dengan rekaman dari separuh kelompok pasien (DS1) dan diuji dengan rekaman dari kelompok pasien yang berbeda sepenuhnya (DS2), yang dikenal sebagai pembagian inter-patient."
- Sumber: tidak ada sitasi; ini klaim tentang penelitian sendiri.
- Keperluan yang diuraikan: pelatihan (DS1) dan pengujian (DS2). Keduanya ada pada kalimat berikutnya, jadi "dua keperluan" terpenuhi, tetapi tidak dinamai sehingga pembaca mengira masih ada keperluan lain yang menyusul. Pemakaian lain MIT-BIH di naskah: sinyal replay rekaman 208 DS1 untuk uji tanpa elektroda (`bab/bab4.tex:144-149` progres-pa-1) dan sumber distribusi error jitter dari DS1 (Bab 2 subbab jitter, baris 343-345). Keduanya tidak diuraikan di paragraf ini.
- Vonis: didukung tanpa angka (kedua keperluan memang diuraikan, hanya tidak dinamai)
- Usulan kalimat: "Dalam penelitian ini, MIT-BIH \textit{Arrhythmia Database} digunakan untuk melatih model CNN dengan rekaman separuh kelompok pasien (DS1) dan menguji model dengan rekaman kelompok pasien lain (DS2), yang dikenal sebagai pembagian \textit{inter-patient}."

## Klaim 5: "menekan jumlah parameter secara drastis"
- Lokasi: `laporan/progres-pa-1/bab/bab3.tex:294`, `laporan/buku-pa/bab/bab3.tex:303`
- Naskah: "Penggunaan Global Average Pooling dipilih untuk menekan jumlah parameter secara drastis dibandingkan perataan langsung (flatten), sesuai pendekatan yang divalidasi oleh Mekhfioui et al.~\cite{mekhfioui_2025}."
- Sumber: `mekhfioui_2025` → `laporan/pustaka/mekhfioui_2025.pdf` hlm. 5: "A Global Average Pooling 1D layer that summarizes feature maps into a global vector,". Pencarian "flatten", "parameters", "million", "KB", "memory" pada seluruh 10 halaman tidak menemukan jumlah parameter atau perbandingan GAP lawan flatten. Sumber hanya memakai GAP, tidak memvalidasinya.
- Angka internal: `model/docs/model-walkthrough.md` bagian 3 (baris 112-123): dengan Flatten, `Dense(16)` berikutnya (1.024+3)x16+16 = 16.448 parameter dan total model sekitar 22.300; dengan GAP, 576 parameter pada lapisan itu dan total 6.417. Pengurangan total sekitar 71% (6.417 dari 22.300, hitungan dari tabel itu, bukan ablasi yang dilatih). Total 6.417 sudah tertulis di naskah baris berikutnya.
- Vonis: "secara drastis" didukung angka internal; "divalidasi oleh Mekhfioui" tidak didukung sumber
- Usulan kalimat: "Penggunaan \textit{Global Average Pooling} dipilih karena menurunkan total parameter dari sekitar 22.300 pada perataan langsung (\textit{flatten}) menjadi 6.417, dan lapisan yang sama dipakai pada model Mekhfioui et al.~\cite{mekhfioui_2025}."

## Klaim 6: "model yang telah teruji akurat"
- Lokasi: `laporan/progres-pa-1/bab/bab3.tex:803`, `laporan/buku-pa/bab/bab3.tex:813`
- Naskah: "Pengukuran ini memastikan model yang telah teruji akurat secara offline juga layak dijalankan dalam batasan sumber daya perangkat edge."
- Sumber: tidak ada sitasi literatur; bukti ada di naskah sendiri. `laporan/progres-pa-1/bab/bab4.tex` (tab:hasil-ds2, sekitar baris 621-643) dan `bab/bab5.tex:10`: model INT8 pada DS2 recall 0,7105, F1 0,6604, AUC 0,9344, precision 0,6169; recall kelas S 0,4630 dan F 0,0773. Bab 4 sendiri menyebut sekitar 38% alarm adalah alarm palsu.
- Catatan: "akurat" bertentangan dengan angka Bab 4. Accuracy bukan acuan di naskah (Bab 4 baris 28, mengutip `chicco_2020`).
- Vonis: tidak didukung (kata "akurat" tidak sesuai hasil sendiri)
- Usulan kalimat: "Pengukuran ini memastikan model yang telah diuji secara \textit{offline} pada DS2 juga layak dijalankan dalam batasan sumber daya perangkat \textit{edge}."
