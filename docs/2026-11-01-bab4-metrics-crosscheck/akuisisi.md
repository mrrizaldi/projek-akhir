# Crosscheck of ECG acquisition quality metrics against standards and literature

Scope: the AD8232 chain into the 12-bit ESP32-S3 ADC at 360 Hz, Lead II, wet-gel electrodes, a healthy subject sitting still, one 927 s session. The criteria checked are the Chapter 4 offline criteria and the firmware real-time gate (see `laporan/buku-pa/bab/bab4.tex` lines 580–611 and 881).

Source status convention: **[TL]** = full text read (PDF or PMC/publisher HTML full text), **[AB]** = abstract only, **[SK]** = secondary quotation (the content of the standard/paper is quoted by another source, the original text was not read).

Conversion used below (from the figures in the brief): 1 count = 0.757 mV / 1,100 ≈ 0.688 µV input-equivalent. The ADC full scale of 4,095 counts ≈ 3.10 V at the ADC ≈ 2.82 mV p-p input-equivalent.

---

## 1. Crosscheck table

| # | Our metric / measurement method | Standard practice / literature (source, page/table) | Status | Concrete suggestion |
|---|---|---|---|---|
| 1 | **Causal 4th-order Butterworth bandpass, 0.5–40 Hz** (non-linear phase). | AHA 1990 (quoted by Buendía-Fuentes 2012): flat response 1–30 Hz, −3 dB at ≤0.67 Hz and ≥150 Hz; a 0.5 Hz HPF shifts the phase of harmonics 1–6 and distorts ST [buendiafuentes2012, Discussion section, TL]. Kligfield 2007 (AHA/ACCF/HRS): HPF 0.05 Hz, may be raised to 0.67 Hz only with a linear zero-phase digital filter [SK, original text not read]. A 0.5–40 Hz band is used by commercial single-lead devices in CinC 2017 (AliveCor: "bandwidth 0.5-40 Hz and a ± 5 mV dynamic range", clifford2017 p. 1) [TL], by BITalino (wagner2021 §2.2) [TL], and as the SNR band of Joutsen 2024 (p. 5) [TL]. | **Different but defensible** | State explicitly in Chapter 3/4: the device is for **rhythm/HR and beat classification**, not ST analysis. The phase distortion is consistent between the training data and the device because training uses the same causal `sosfilt`/`lfilter` (`model/src/preprocessing.py` lines 21–41; checked). Cite CinC 2017 as precedent for the 0.5–40 Hz single-lead band. Do not claim ST diagnostic quality. |
| 2 | **Absolute ADC swing** (max − min, counts and mV); <150 counts = no biopotential; healthy ECG ≈2 mV ≈3,000 counts. | No standard SQI uses absolute swing as a criterion. Closest: the "low energy" QC of Gajdzik 2026 (moving RMS over 1 s < 25% of the median RMS is flagged invalid, pp. 59–60) [TL]; Lueken 2023 includes "mean R-peak amplitude" as a feature (feature table, p. 12) [TL]. Standards measure **dynamic range**, not swing: IEC 60601-2-25 requires a minimum dynamic range of ±5 mV without clipping (Raus-Jarzabek 2025 §3.7) [TL, secondary quotation of the standard's content]; IEC 60601-2-27 has clause 201.12.1.101.2 "Dynamic range and differential offset voltage" (Raus-Jarzabek 2025 §2.1) [TL; the 2-27 clause values were not read]. | **Conforms as a "signal present" detector; Lacking for dynamic range** | Keep the swing as the "biopotential present" gate. Add one dynamic range sentence: effective input ≈2.82 mV p-p; with a baseline of ≈1,900 counts (Chapter 4 line 624), headroom upward is ≈(4,095−1,900)×0.688 µV ≈1.5 mV and downward ≈1.3 mV, far below ±5 mV. This explains the saturated samples at the R peak (ADC max 4,095 in all four recordings). See Gap 2. |
| 3 | **50 Hz hum** = % of 50 Hz band energy relative to the 0.5–40 Hz ECG band energy; pass <15%. Firmware: hum ≤500 counts. | The ratio construction is **identical** to PLIratio = P(49–51 Hz)/P(0.5–40 Hz) in Gajdzik 2026 (AD8232 + 12-bit ESP32 ADC, gain ≈1,100; equation pp. 59–60, Table 6 p. 62) [TL]. The AD8232 values there are 0.0028–0.0046% (simulator signal, not a body), and **there is no pass threshold**. Kramer 2022 (ECGAssess) uses SNR = P(2–40)/[P(0–2)+P(40–250)], with the 0.5 dB threshold chosen visually from the training data (§2.3.3) [TL]. Li 2008/Zhao 2018: mains interference is detected indirectly through kSQI < 5 (Li 2008 §2.1.3; Zhao 2018 p. 5) [TL]. Syversen 2024: the PLI threshold at which public SQIs start rejecting a signal varies widely, 0.70–10.71 dB (Table 1, p. 3) [TL]. Rahman 2022: there is no standard SQI threshold that holds across datasets (§ Introduction) [TL]. | **Different but defensible** | Cite Gajdzik 2026 as precedent for the definition. Write the 15% threshold as an empirical project threshold (equivalent to an ECG/50 Hz band ratio ≈ 8.2 dB) and state that the literature gives no standard threshold. Stronger still if the 15% threshold is derived from trial recordings, disturbed vs clean (like the 0.1% saturation threshold, which already has a data-based reason). Also report whether the ratio is computed from the raw ADC (before the bandpass): state it in the text. |
| 4 | **Pan-Tompkins R peak; proportion of RR intervals equivalent to 30–200 BPM > 90%** (over the whole recording or per segment). | Orphanidou 2015 (feasibility rules per **10 s window**): HR 40–180 bpm, maximum RR gap 3 s, max/min RR ratio < 2.2 (p. 834) [TL]. Kramer 2022: HR 24–300 bpm per 10 s (§2.3.2) [TL]. The 30–200 bpm range is the minimum heart-rate meter range of ANSI/AAMI EC13 (1987 edition clause 3.2.7, quoted through a patent; WebSearch) [SK]. Li 2008 and Clifford 2011 compute the SQI per 10 s window (Li 2008 §2.1.1; Clifford 2011 p. 286) [TL]. | **Different but defensible** (range); **Lacking** (granularity) | The 30–200 range is valid, match it to EC13. Add an evaluation **per 10 s window** with the three Orphanidou rules, and report the % of windows that pass. Cheap: the R peaks already exist. |
| 5 | **Autocorrelation of QRS band energy** (median per 30 s), pass > 0.25. | Not found in the literature as a standard SQI. Closest comparison: mean correlation of each QRS against the average template per 10 s, threshold **0.66** (Orphanidou 2015 pp. 835–836; Se 94%, Sp 97% against manual annotation) [TL]; bSQI = agreement of two detectors within a 150 ms window (Li 2008 §2.1.1) [TL]; qSQI of Zhao 2018: optimal > 90% (p. 4) [TL]. | **Lacking, needs addition** | The 0.25 threshold has no reference and R4 passes narrowly (0.28). Add the Orphanidou template correlation (threshold 0.66) as a morphological SQI with a reference; the autocorrelation may stay as a complementary metric. If bSQI is wanted, Pan-Tompkins vs a second detector (e.g. Hamilton) with 150 ms tolerance. |
| 6 | **Saturated samples** (at the ADC limit) are reported; flagged when > 0.1%. | Clifford 2011: pSQI = the percentage of the signal that looks like a flat line (dx/dt < 1 mV) (p. 286) [TL]; Kramer 2022: the signal is rejected if one 0.2 s window is entirely constant (§2.3.1) [TL]; Gajdzik 2026: flatline/low-energy samples are flagged invalid, a 10 s segment is rejected if > 30% invalid (pp. 59–60) [TL]. | **Conforms** (in spirit) | Keep. Add flatline detection (a constant run ≥0.2 s) next to the rail count, because a partial lead-off can be flat at a mid value, not at the rail. |
| 7 | **Status Berhasil / Bersinyal / Gagal** (successful / with signal / failed) per recording. | Tiered schemes are common: Zhao 2018 optimal/suspicious/unqualified (pp. 4–6) [TL]; CinC 2011 acceptable/indeterminate/unacceptable (Silva 2011 p. 274; Clifford 2011 p. 286) [TL]. The unit of assessment in the literature = a 10 s segment, not a whole recording. | **Conforms** | Add a per-10 s segment summary (% of segments per status) next to the recording status. |
| 8 | **Real-time gate**: AD8232 lead-off, clean swing ≥60 counts (≈41 µV), hum ≤500 counts, good contact 60 s, RR 300–1,500 ms (40–200 bpm) and \|ΔRR\| ≤ 200 ms for 30 s. | RR 300–1,500 ms is equivalent to the Orphanidou HR rule (40–180 bpm) [TL]. **However** the \|ΔRR\| ≤ 200 ms requirement and RR-regularity-based rules reject irregular rhythms; Orphanidou themselves state "the algorithm is unlikely to perform well on patients exhibiting atrial fibrillation" (p. 838) [TL]. Behar 2013 specifically addresses SQI during arrhythmia [AB, title only; text not read]. | **Different but defensible** for healthy subjects; **risky** for the purpose of arrhythmia classification | State in Chapter 3/4 that the ΔRR gate is used only for the **calibration phase** (not for rejecting beats after calibration, per Chapter 4 line 881). State the limitation: AF/ectopic patients may often be held in the calibration phase. |
| 9 | **HR/R-peak accuracy**: there is no reference device, R peaks are not validated. | Standard: ANSI/AAMI EC13 HR accuracy ±10% or ±5 bpm, whichever is greater (Solbiati 2025 §2, Areia 2021 §Methods) [SK]; IEC 60601-2-27 clause 201.12.1.101.15 "HR range and accuracy, QRS detection range" (Raus-Jarzabek 2025 §2.1) [TL; clause values not read]. Paper practice: simultaneous recording against a clinical reference + Bland-Altman/ICC (Wagner 2021: 23 subjects, seated, ~35 minutes, ICC > 0.9 and LoA; §2.1, §4.3–4.4) [TL]; MAE ≤ 5 bpm per EC13 (Areia 2021: 29 subjects) [TL]; Polar H10 vs Lead II, r > 0.99 (Chung 2026: 26 subjects) [TL]; RR detection compared against **visual inspection of the raw ECG**, RR quality = the proportion of correctly detected RR (Gilgen-Ammann 2019: 10 subjects; Polar H10 99.6%) [AB]; without manual annotation, Gajdzik 2026 uses a patient simulator and compares the beat count against the nominal count (deviation −0.13% to +0.21%, Table 3 pp. 60–61) [TL]. An ESP32-S3 + AD8232 paper with no subjects and no reference states explicitly "Table 4 therefore records validation status rather than accuracy" (Torad 2026 §4) [TL]. | **Lacking, needs addition** | Minimum acceptable without new equipment: **manual R-peak annotation** over the whole 927 s (≈1,200 beats, semi-automatic: correct the Pan-Tompkins output on a plot), then compute Se and +P with 150 ms tolerance (EC57/bSQI style). Better: a short simultaneous re-recording with a Polar H10 (the literature validates it) and report the HR Bland-Altman plus the % of windows within ±5 bpm/±10% (EC13). If there is no time, write it like Torad 2026: the result = functional status, not accuracy. |
| 10 | **Intrinsic noise and CMRR** are not measured. | IEC 60601-2-25: system noise ≤ 30 µV p-p and ≤ 15 µV RMS over 10 s, input shorted (Raus-Jarzabek 2025 §3.4) [TL, secondary quotation of the standard's content]; CMRR ≈ 89–90 dB at 50/60 Hz (Raus-Jarzabek 2025 §1, quoting Campillo) [TL, secondary]. IEC 60601-2-27 has a CMR test circuit (Figure 201.107) and a CMR definition (201.3.201, p. 9 of the preview) [TL preview; no values]. Joutsen 2024 measures p-p noise and total power on a no-signal channel (Table 5) [TL]. | **Lacking, needs addition** (noise); CMRR may be stated as not tested | A 10 s bench test with IN+, IN−, and RLD tied together (or through a resistor network): compute p-p and RMS in µV input-equivalent. The 30 µV p-p limit ≈ 44 counts and 15 µV RMS ≈ 22 counts. No extra equipment. CMRR: cite the AD8232 datasheet specification and state that the system CMRR was not tested. |

---

## 2. Source list

### Standards and regulatory documents

**fda1998**: Guidance for Industry: Cardiac Monitor Guidance (including Cardiotachometer and Rate Alarm). FDA CDRH, 5 Nov 1998. URL: https://www.fda.gov/media/71947/download. Scopus: –. **[TL]**. PDF: `laporan/pustaka/belum-dirujuk/riset-pengukuran/akuisisi/fda_1998.pdf`.
- Quote (p. 1): "This guidance applies to most of the cardiac monitors covered by the ANSI/AAMI EC13-1992 standard for Cardiac Monitors, Heart Rate Meters, and Alarms (EC13 standard)."
- Quote (p. 1): the EC13 scope exclusion covers "devices for monitoring ambulatory ECG".
- Note: this document does **not** contain the EC13 requirement figures; it only asks for an EC13 conformance test or a comparison test against a predicate.

**iec27_2011**: IEC 60601-2-27:2011 Ed. 3.0, Particular requirements for the basic safety and essential performance of electrocardiographic monitoring equipment. Official preview (VDE). Scopus: –. **[TL preview only; the clause values are paywalled]**. PDF: `.../akuisisi/iec_60601-2-27_2011_preview.pdf`.
- Quote (201.1.1 Scope, p. 7): "This standard is not applicable to electrocardiographic monitors for home use. However, MANUFACTURERS should consider using relevant clauses of this standard as appropriate for their INTENDED USE."
- Quote (p. 7): "Ambulatory ("Holter") monitors, fetal heart rate monitoring, pulse plethysmographic devices, and other ECG recording equipment are outside the scope of this particular standard."
- Table of contents: Figure 201.106 High frequency response, Figure 201.107 Test circuit for COMMON MODE REJECTION, Figure 201.110 Test waveforms for T-wave rejection.

**rausjarzabek2025**: Raus-Jarzabek E, Czerw M, Skowronek A, Dąbrowska-Boruch A, Jamro E, Olejarczyk E. A Practical Guide to ECG Device Performance Testing According to International Standards. *Electronics* 14(19):3878, 2025. DOI 10.3390/electronics14193878. Scopus 105019201211. **[TL, publisher HTML through a browser; the PDF could not be downloaded (403)]**.
- Quote (§2.1): "The following three standards for ECG equipment are currently in force: 60601-2-25 (diagnostic electrocardiographs) [1], 60601-2-47 (ambulatory ECG) [2], and 60601-2-27 (ECG patient monitors) [3]."
- List of IEC 60601-2-27:2014 clauses (§2.1): "201.12.1.101.2—Dynamic range and differential offset voltage; ... 201.12.1.101.8—Frequency and impulse response; ... 201.12.1.101.15—HR range and accuracy, QRS detection range."
- Quote (§3.4): "The peak-to-peak noise amplitude measured over the 10 s window must not exceed 30 microvolts (µV)." and "The root mean square (RMS) noise over the same interval must be no greater than 15 µV."
- Quote (§3.7): "the standard specifies that ECG systems must possess a minimum dynamic range of ±5 millivolts." (IEC 60601-2-25 context)
- Quote (§3.6.1): "the amplitude of the output for the 0.67 Hz and 40 Hz signals must not deviate by more than 10% from the amplitude observed at 10 Hz." (IEC 60601-2-25)
- Quote (§1): "a CMRR ≈ 93.7 dB (well above the 89 dB minimum), intrinsic channel noise ≈ 9 μVpp (<30 μV allowed)" (quoting Campillo et al., 60601-2-25 context).

**kligfield2007**: Kligfield P, et al. Recommendations for the standardization and interpretation of the electrocardiogram: Part I. *Circulation* 115:1306–1324, 2007. DOI 10.1161/CIRCULATIONAHA.106.180200. Scopus 33947712041. **[SK; the original text is blocked by Cloudflare at ahajournals, jacc.org, heartrhythmjournal, hrsonline]**. Circulating content (WebSearch summary, not verified verbatim): HPF 0.05 Hz; 0.67 Hz or lower is allowed with a linear zero-phase digital filter. Do not quote its figures or sentences in the book without reading the original.

**buendiafuentes2012**: Buendía-Fuentes F, Arnau-Vives MA, Arnau-Vives A, Jiménez-Jiménez Y, et al. High-Bandpass Filters in Electrocardiography: Source of Error in the Interpretation of the ST Segment. *ISRN Cardiology* 2012:706217. DOI 10.5402/2012/706217. PMC3388307. Scopus: not found. **[TL, PMC full text]**. Text: `.../akuisisi/buendiafuentes_2012.txt`.
- Quote (Discussion): "the AHA recommended a flat amplitude response (±6%, 0.5 dB) between 1 and 30 Hz, with an attenuation of −3 dB in frequencies ≤0.67 Hz and ≥150 Hz"
- Quote (Discussion): "a 0.5 Hz high-pass filter induces discrete amplitude attenuation of the first harmonic, though primarily and most importantly it causes phase shifts in up to the fifth or sixth harmonic (phase nonlinearities)."
- Quote (Discussion): "A bidirectional filter cannot happen in real time."

**aami_ec13**: ANSI/AAMI EC13:2002 Cardiac monitors, heart rate meters, and alarms. **[SK; paywalled]**.
- Via solbiati2025 (§2, Methods): "The standard defines a maximum tolerance of ±10% of the actual value or ±5 bpm, whichever is greater."
- Via areia2021 (Objective): "In line with the ... (ANSI/AAMI) EC13:2002 standard [27], we defined the MAE of the patch estimates to be clinically acceptable if the rates are within 5 beats per minute (bpm)".
- The 30–200 bpm range: only from a patent quoting EC13 1987 edition clause 3.2.7 (WebSearch result, not read directly). Treat it as unverified.

### Signal Quality Index

**orphanidou2015**: Orphanidou C, Bonnici T, Charlton P, Clifton D, Vallance D, Tarassenko L. Signal-Quality Indices for the Electrocardiogram and Photoplethysmogram: Derivation and Applications to Wireless Monitoring. *IEEE J Biomed Health Inform* 19(3):832–838, 2015. DOI 10.1109/JBHI.2014.2338351. Scopus 84929377665. **[TL]**. PDF: `laporan/pustaka/belum-dirujuk/orphanidou_2015.pdf`.
- p. 834: "Rule 1: The HR extrapolated from the 10-s sample must be between 40 and 180 beats per minute (bpm)."
- p. 834: "Rule 2: The maximum acceptable gap between successive R-peaks/PPG pulse-peaks is 3 s."
- p. 834: "Rule 3: The ratio of the maximum beat-to-beat interval to the minimum beat-to-beat interval within the sample should be less than 2.2."
- p. 834: manual labels by two assessors and R peaks "manually identified by the two human experts using a custom annotation GUI".
- p. 836: "The optimum threshold for the average correlation coefficient was found to be 0.66 for the ECG SQI ... this corresponded to a sensitivity of 94% and specificity of 97%".
- p. 838: "the algorithm is unlikely to perform well on patients exhibiting atrial fibrillation (AF)".

**li2008**: Li Q, Mark RG, Clifford GD. Robust heart rate estimation from multiple asynchronous noisy sources using signal quality indices and a Kalman filter. *Physiol Meas* 29(1):15–32, 2008. DOI 10.1088/0967-3334/29/1/002. PMC2259026. Scopus 38049013310. **[TL, PMC HTML through a browser; the sSQI threshold equation (eq. 6) is an image and was not readable]**.
- §2.1.1: "Nmatched is the number of beats that both algorithms agreed upon (within γ = 150 ms)"; window "w = 10 s long, centered ± 5 s around the kth beat".
- §2.1.3: "clean, sinus rhythm ECG generally has a kurtosis larger than 5 ... baseline wander and power-line interference have kurtosis lower than 5".
- §2.1.4: SDR = power ratio "between 5 Hz and 14 Hz to the power between 5 Hz and 50 Hz".

**clifford2011**: Clifford GD, Lopez D, Li Q, Rezek I. Signal Quality Indices and Data Fusion for Determining Acceptability of Electrocardiograms Collected in Noisy Ambulatory Environments. *Computing in Cardiology* 38:285–288, 2011. Scopus 84859972933. **[TL]**. PDF: `.../akuisisi/clifford_2011.pdf`.
- p. 286: "Group 1 (acceptable): If ŝ ≥ 0.70, and N (F ) ≤ 1."
- p. 286: "3. fSQI: The ratio of power P (5-20Hz)/P (0-fn Hz)"; "6. pSQI: The percentage of the signal xm which appeared to be a flat line (dxm /dt < ǫ where ǫ =1mV)."
- Note: the journal version (Clifford et al. 2012, *Physiol Meas* 33(9):1419, Scopus 84866323283) was not readable (paywalled).

**silva2011**: Silva I, Moody GB, Celi L. Improving the Quality of ECGs Collected Using Mobile Phones: The PhysioNet/Computing in Cardiology Challenge 2011. *Computing in Cardiology* 38:273–276, 2011. Scopus 84859998604. **[TL]**. PDF: `.../akuisisi/silva_2011.pdf`.
- p. 274: data "2,000 twelve-lead ECGs, each 10 seconds long, with standard diagnostic bandwidth (0.05-100 Hz)", "recorded at 500 samples per second".

**clifford2017**: Clifford GD, Liu C, Moody B, Lehman LH, Silva I, Li Q, Johnson AE, Mark RG. AF Classification from a Short Single Lead ECG Recording: the PhysioNet/Computing in Cardiology Challenge 2017. *Computing in Cardiology* 44, 2017. DOI 10.22489/CinC.2017.065-469. Scopus 85045094669. **[TL]**. PDF: `.../akuisisi/clifford_2017.pdf`.
- p. 1: data "stored as 300 Hz, 16-bit files with a bandwidth 0.5-40 Hz and a ± 5 mV dynamic range."
- pp. 1–2: the class "too noisy to be classified" was relabeled by experts.

**zhao2018**: Zhao Z, Zhang Y. SQI Quality Evaluation Mechanism of Single-Lead ECG Signal Based on Simple Heuristic Fusion and Fuzzy Comprehensive Evaluation. *Front Physiol* 9:727, 2018. DOI 10.3389/fphys.2018.00727. Scopus 85048541168. **[TL]**. PDF: `.../akuisisi/zhao_2018.pdf`.
- p. 4: qSQI "optimal, qSQI > 90%; ECG suspicious, qSQI ∈ [60%, 90%]; unqualified, qSQI < 60%".
- pp. 4–5: pSQI = P(5–15 Hz)/P(5–40 Hz); for HR 60–130 bpm "l1 = 0.5, l2 = 0.8; l3 = 0.4".
- p. 5: kSQI "optimal kSQI > 5"; basSQI = 1 − P(0–1 Hz)/P(0–40 Hz), "optimal, basSQI ∈ [0.95, 1]; ECG suspicious, basSQI ∈ [0.9, 0.95]; unqualified, basSQI < 0.9".

**behar2013**: Behar J, et al. ECG signal quality during arrhythmia and its application to false alarm reduction. *IEEE Trans Biomed Eng* 60(6):1660–1666, 2013. DOI 10.1109/TBME.2013.2240452. Scopus 84877912344. **[not read; Scopus returns no abstract, not OA]**. Recorded only because it is relevant to the ΔRR gate.

**kramer2022**: Kramer L, Menon C, Elgendi M. ECGAssess: A Python-Based Toolbox to Assess ECG Lead Signal Quality. *Front Digit Health* 4:847555, 2022. DOI 10.3389/fdgth.2022.847555. PMC9120362. Scopus 85131240007. **[TL, PMC full text]**. Text: `.../akuisisi/kramer_2022.txt`.
- §2.3.1: the signal is stationary when max = min within a 0.2 s window.
- §2.3.2: "If the heart rate was between 24 and 300 bpm, the signal was declared passed".
- §2.3.3: SNR = ΣPSD(2–40 Hz) / [ΣPSD(0–2 Hz) + ΣPSD(40–250 Hz)]; "Visually, the SNR threshold value of 0.5 dB is selected."

**rahman2022**: Rahman S, Karmakar C, Natgunanathan I, Yearwood J, Palaniswami M. Robustness of electrocardiogram signal quality indices. *J R Soc Interface* 19:20220012, 2022. DOI 10.1098/rsif.2022.0012. PMC9006023. Scopus 85128156811. **[TL, PMC full text]**. Text: `.../akuisisi/rahman_2022.txt`.
- Introduction: "A few researchers have sought to determine the standard threshold and window sizes for SSQI measurements in diverse datasets; however, they have not found a gold standard that works for multiple datasets".

**syversen2024**: Syversen AB, Zhang Z, Batty JA, Kaisti M, Jayne D, Wong DC. Assessment of ECG Signal Quality Index Algorithms Using Synthetic ECG Data. *Computing in Cardiology* 2024. DOI 10.22489/CinC.2024.270. Scopus 105028373590. **[TL]**. PDF: `laporan/pustaka/syversen_2024.pdf`.
- Table 1 (p. 3): PLI thresholds towards "unacceptable": Orphanidou 4.13 dB, Zhao 10.71 dB, Kramer 0.70 dB, Elgendi 0.70 dB.
- p. 3: "the tested SQIs were inconsistent with each other and with an expert opinion."

**lueken2023**: Lueken M, Gramlich M, Leonhardt S, Marx N, Zink MD. Automated Signal Quality Assessment of Single-Lead ECG Recordings for Early Detection of Silent Atrial Fibrillation. *Sensors* 23:5618, 2023. DOI 10.3390/s23125618. Scopus 85163942520. **[TL]**. PDF: `laporan/pustaka/belum-dirujuk/lueken_2023.pdf`.
- Feature table (p. 12): basSQI and qrsSQI "according to [15]" (Clifford 2012), "pliSQI SQI for power-line interference according to [38]", "mean R-peak amplitude".

### SNR and mains interference measurement

**gajdzik2026**: Gajdzik F, Kimbar M, Krowicki P. Comparative assessment of AD8232- and MAX30003-based ECG acquisition paths using synthetic ECG signals. *Acta Bioeng Biomech* 28(3):54–69, 2026. DOI 10.37190/abb/231067. Scopus 105054295912. **[TL]**. PDF: `laporan/pustaka/gajdzik_2026.pdf`.
- Specification table: AD8232 "Nominal voltage gain Approximately 1,100 V/V", ESP32 "12 bit" ADC with 11 dB attenuation.
- pp. 59–60: "P50 Hz denotes the power in the 49.00–51.00 Hz band corresponding to power-line interference"; PLIratio = P50Hz/PECG, PECG = power in 0.50–40.00 Hz.
- pp. 59–60: a sample is invalid when "the RMS value fell below 25% of the median moving RMS"; "A 10 s segment was rejected if the proportion of samples marked as invalid exceeded 30%".
- pp. 59–60: "Because no independent manual R-wave annotations were available, the QRS detector was validated by comparing the number of detected beats with the expected number derived from the nominal simulator heart rate".
- pp. 62–63: "For AD8232, its values ranged from 0.0028% to 0.0046%" (PLIratio, simulator signal).
- Note: no human subjects; no PLIratio pass threshold.

**joutsen2024**: Joutsen A, Cömert A, Kaappa E, Vanhatalo K, Riistama J, et al. ECG signal quality in intermittent long-term dry electrode recordings with controlled motion artifacts. *Sci Rep* 14:8882, 2024. DOI 10.1038/s41598-024-56595-0. Scopus 85190649731. **[TL]**. PDF: `laporan/pustaka/belum-dirujuk/joutsen_2024.pdf`.
- p. 5: "The SNR assessments were conducted in this 0.5 to 40 Hz frequency range."; the 10 and 50 Hz components and their first harmonics are excluded from the band.
- p. 5: signal = the QRS range within a 100 ms window; noise = RMS of a 2 s reference channel; SNRdB = 20·log10(SNR).
- Subjects: 9 healthy volunteers (p. 3).

### Validation of low-cost ECG devices and HR

**wagner2021**: Wagner RE, Plácido da Silva H, Gramann K. Validation of a Low-Cost Electrocardiography (ECG) System for Psychophysiological Research. *Sensors* 21:4485, 2021. DOI 10.3390/s21134485. PMC8271611. Scopus 85108887171. **[TL, PMC full text]**. Text: `.../akuisisi/wagner_2021.txt`.
- §2.1: 23 healthy participants; seated still ~35 minutes; simultaneous recording BITalino vs BrainAmp-ExG.
- §2.2: "The BITalino ECG sensor has a bandwidth between 0.5 and 40 Hz."
- §2.4: automatic R peaks, then "false R-peaks were marked and rejected" (manual correction).
- §4.3: criterion "the ICC should be higher than 90% for clinical measurements ... and the lower CI should be higher than 75%".

**chung2026**: Chung V, Chopin L, Karadayi J, et al. Validity of the Polar H10 for Continuous Measures of Heart Rate and Heart Rate Synchrony Analysis. *Sensors* 26:855, 2026. DOI 10.3390/s26030855. PMC12899868. Scopus 105030019450. **[TL, PMC full text]**. Text: `.../akuisisi/chung_2026.txt`.
- 26 seated participants; reference Lead II PowerLab 1,000 Hz; automatic R peaks "and the ECG was visually inspected to correct for peak misidentification"; correlation, Lin concordance, Bland-Altman bias.

**gilgenammann2019**: Gilgen-Ammann R, Schweizer T, Wyss T. RR interval signal quality of a heart rate monitor and an ECG Holter at rest and during exercise. *Eur J Appl Physiol* 119:1525–1532, 2019. DOI 10.1007/s00421-019-04142-5. Scopus 85064623069. **[AB; paywalled]**.
- Abstract: "both measurement systems were compared against visual inspection of the raw electrocardiography signal. The missing and wrong R-wave peak detections were counted manually ... RR interval signal quality was defined as the relative number of correctly detected RR intervals." Polar H10 99.6%; 10 subjects.

**areia2021**: Areia CM, Santos M, Vollam S, Pimentel M, Young L, et al. A Chest Patch for Continuous Vital Sign Monitoring: Clinical Validation Study During Movement and Controlled Hypoxia. *J Med Internet Res* 23(9):e27547, 2021. DOI 10.2196/27547. Scopus 85115308718. **[TL, PMC full text]**. Text: `.../akuisisi/areia_2021.txt`. For the EC13 quote see aami_ec13. 29 participants, reference Philips MX450 3-lead.

**solbiati2025**: Solbiati S, Mozzini F, Sahler J, et al. Estimating Heart Rate from Inertial Sensors Embedded in Smart Eyewear: A Validation Study. *Sensors* 25:4531, 2025. DOI 10.3390/s25154531. Scopus 105013341608. **[TL, PMC full text]**. Text: `.../akuisisi/solbiati_2025.txt`. For the EC13 quote see aami_ec13.

**torad2026**: Torad MA, Ahmed HE, Torad AAM, et al. ESP32-S3-Based Multimodal Wearable for Remote Vital-Sign Acquisition ... An Engineering Proof of Concept. *Sensors* 26:6047, 2026. DOI 10.3390/s26196047. Scopus 105053670763. **[TL, PMC full text]**. Text: `.../akuisisi/torad_2026.txt`.
- §4: "No quantitative reference-device agreement is reported for heart rate, SpO2, ECG waveform, or contact temperature." and "The AD8232 leads-off and signal-acquisition paths were functionally verified, but no quantitative ECG waveform error is available. Table 4 therefore records validation status rather than accuracy."

**panwar2025**: Panwar A, Narendra M, Arya A, et al. Integrated portable ECG monitoring system with CNN classification for early arrhythmia detection. *Front Digit Health* 7:1535335, 2025. DOI 10.3389/fdgth.2025.1535335. Scopus 105001450460. **[TL, PMC full text]**. Text: `.../akuisisi/panwar_2025.txt`. An example of an AD8232 paper that does not report acquisition validation against a reference; classification is only evaluated on MIT-BIH. Useful as a comparison for the literature gap, not as a method reference.

### Searched but not readable
- Narasinghe 2025 (AD8232 vs BIOPAC MP160, eIT 2025, DOI 10.1109/eIT64391.2025.11103617, Scopus 105014910660) and Mamee 2023 (AD8232 vs BioAmp EXG Pill, DOI 10.1109/ICSPC59664.2023.10420266, Scopus 85186731909): IEEE paywalled, title only.
- Full text of IEC 60601-2-27/-2-47/-2-25 and AAMI EC13: paywalled.
- AD8232 datasheet from analog.com: download failed from the sandbox.

---

## 3. Most important gaps (ordered from most risky at the defense)

1. **No R-peak/HR validation against ground truth.** The acquisition validation literature always has a reference: a simultaneous clinical device (Wagner 2021, Areia 2021, Chung 2026), manual visual inspection (Gilgen-Ammann 2019, Orphanidou 2015), or a patient simulator (Gajdzik 2026). EC13 and IEC 60601-2-27 clause 201.12.1.101.15 test HR accuracy (±10% or ±5 bpm, secondary quotation). The question "what is the beat detection accuracy?" will almost certainly come up. The cheapest route: manual annotation of the existing 927 s, then Se/+P with 150 ms tolerance. If it is not done, write explicitly, like Torad 2026, that the result is functional status, not accuracy.
2. **Dynamic range ≈2.8 mV p-p, far below ±5 mV.** IEC 60601-2-25 (via Raus-Jarzabek 2025 §3.7) and the CinC 2017 single-lead devices use ±5 mV. With a gain of 1,100 and a baseline of ≈1,900 counts, the R peak touches 4,095 in all four official recordings. An examiner who computes gain × ADC scale will find it. Acknowledge it as a design limitation (fixed gain of the AD8232 module), explain that saturated samples are ≤0.010% and do not shift the R-peak position, and state the fix (lower gain or a baseline at mid-scale).
3. **Thresholds 15% (hum), 0.25 (autocorrelation), 90% (plausible RR) have no reference.** The literature itself states there is no standard threshold (Rahman 2022) and public SQIs are inconsistent (Syversen 2024), so own thresholds are valid, **as long as their origin is written down**. The 0.25 autocorrelation is the most vulnerable (R4 = 0.28, and it is not a known SQI). Add the Orphanidou template correlation (0.66) and cite Gajdzik 2026 for the definition of the 50 Hz ratio.
4. **Unit of assessment = the whole recording, not a 10 s segment.** All standard SQIs (Orphanidou, Li, Clifford, Zhao, Kramer, Gajdzik) assess per 10 s. A 300 s recording that is "Berhasil" (successful) can hide a bad minute. Recompute per 10 s from the existing data and report the % of segments that pass.
5. **The ΔRR ≤ 200 ms gate and the causal 0.5 Hz filter conflict with the arrhythmia purpose if left unbounded.** ΔRR rejects irregular rhythms (Orphanidou themselves acknowledge the limitation for AF, p. 838). A 0.5 Hz non-linear-phase HPF distorts ST (Buendía-Fuentes 2012). Both can be kept if the text states: ΔRR is only a calibration gate, and the device is not used for ST analysis; the phase distortion is identical between the MIT-BIH training data and the device.

Secondary gaps (not in the top five): intrinsic noise has not been measured, although a 10 s bench test with the input shorted is enough (30 µV p-p limit ≈ 44 counts; 15 µV RMS ≈ 22 counts).
