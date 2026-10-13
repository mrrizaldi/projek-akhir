# firmware/include/ — header kontrak

| Header | Isi | Asal |
|---|---|---|
| `model_int8.h` | Model TFLite INT8 sebagai array C, beserta scale dan zero point | GENERATED oleh `model/scripts/export_model_h.py` |
| `ecg_preproc.h` | Koefisien bandpass dan konstanta preprocessing dari `model/src/preprocessing.py` | GENERATED oleh `model/scripts/export_golden.py` |
| `ecg_pipeline.h` | Kontrak preprocessing on-device (harus sama dengan Python) | ditulis tangan |
| `ecg_live.h` | Kontrak alur streaming sampel → beat | ditulis tangan |
| `ecg_mqtt.h` | Kontrak payload dan antrean MQTT | ditulis tangan |
| `ina219.h` | Konversi register INA219 | ditulis tangan |
| `perangkat.h` | Pin map PCB rev1 dan pemasangan perangkat (TFT, buzzer, tombol, ADC) untuk `main.cpp` dan test `test_hw_*` | ditulis tangan |
| `akuisisi.h` | Timer ISR 360 Hz, antrean sampel, sumber ADC/replay | ditulis tangan |
| `gerbang.h` | Kualitas sinyal dan fase kalibrasi | ditulis tangan |
| `klasifikasi.h` | Inferensi TFLM per beat dan publikasi ke antrean MQTT | ditulis tangan |
| `tampilan.h` | TFT, NeoPixel, buzzer | ditulis tangan |
| `tombol.h` | Debounce dan event tombol B1–B3 | ditulis tangan |
| `rekam.h` | Rekaman bernomor `/rekam/NNN.csv` di LittleFS | ditulis tangan |
| `daya.h` | INA219 dan tangga ukur daya `p0`–`p5` | ditulis tangan |
| `konfig.h` | Daftar WiFi/broker dan pilihan di NVS | ditulis tangan |
| `serial_cmd.h` | Perintah serial | ditulis tangan |
| `wifi_secrets.example.h` | Templat kredensial; salin menjadi `wifi_secrets.h` (di-ignore git) | ditulis tangan |

Header GENERATED tidak boleh diedit tangan. Regenerasi:

```bash
cd model && make quantize && make export    # model_int8.h (lewat scripts/export_artifacts.sh)
cd model && python scripts/export_golden.py  # ecg_preproc.h + firmware/test/golden_ref.h
cd firmware && pio test -e native            # verifikasi C == Python
```
