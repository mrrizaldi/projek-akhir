// GENERATED oleh model/scripts/export_golden.py — JANGAN EDIT TANGAN.
// Koefisien golden reference dari model/src/preprocessing.py.
// Regenerasi: cd model && python scripts/export_golden.py
#ifndef ECG_PREPROC_H
#define ECG_PREPROC_H

#define ECG_FS 360
#define ECG_WIN_PRE 90
#define ECG_WIN_POST 160
#define ECG_WIN_LEN_ 250
#define ECG_ZSCORE_EPS 1e-8f
#define ECG_RR_LOCAL_WINDOW 10

// Pan-Tompkins (deteksi R-peak on-device).
#define ECG_PT_MWI_LEN 54
#define ECG_PT_REFRACTORY 72
#define ECG_PT_N_SOS 2
const float ecg_pt_sos[12] = {
  6.76541326e-03f, 1.35308265e-02f, 6.76541326e-03f, 1.00000000e+00f, -1.79193383e+00f, 8.41222058e-01f,
  1.00000000e+00f, -2.00000000e+00f, 1.00000000e+00f, 1.00000000e+00f, -1.91937262e+00f, 9.28744645e-01f
};

// Penyelarasan R-peak. Urutan WAJIB, salah satu terlewat -> precision jatuh 4x:
//   r - ECG_PT_OFFSET  ->  puncak dlm +-ECG_PT_REFINE  ->  - ECG_GROUP_DELAY
#define ECG_PT_OFFSET 38
#define ECG_PT_REFINE 25
#define ECG_GROUP_DELAY 4

// Butterworth bandpass 0.5-40.0 Hz orde 4,
// 4 second-order section: {b0, b1, b2, a0, a1, a2} per baris.
// KAUSAL — jalankan maju saja, jangan pernah maju-mundur (filtfilt).
// Group delay menggeser R-peak +4 sampel; BIARKAN, model dilatih dengan geseran itu.
#define ECG_N_SOS 4
const float ecg_sos[24] = {
  6.60487567e-03f, 1.32097513e-02f, 6.60487567e-03f, 1.00000000e+00f, -9.78949069e-01f, 2.64010653e-01f,
  1.00000000e+00f, 2.00000000e+00f, 1.00000000e+00f, 1.00000000e+00f, -1.23747710e+00f, 6.12478820e-01f,
  1.00000000e+00f, -2.00000000e+00f, 1.00000000e+00f, 1.00000000e+00f, -1.98365367e+00f, 9.83732407e-01f,
  1.00000000e+00f, -2.00000000e+00f, 1.00000000e+00f, 1.00000000e+00f, -1.99338058e+00f, 9.93457003e-01f
};

#endif  // ECG_PREPROC_H
