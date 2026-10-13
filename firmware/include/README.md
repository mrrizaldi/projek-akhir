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
| `wifi_secrets.example.h` | Templat kredensial; salin menjadi `wifi_secrets.h` (di-ignore git) | ditulis tangan |

Header GENERATED tidak boleh diedit tangan. Regenerasi:

```bash
cd model && make quantize && make export    # model_int8.h (lewat scripts/export_artifacts.sh)
cd model && python scripts/export_golden.py  # ecg_preproc.h + firmware/test/golden_ref.h
cd firmware && pio test -e native            # verifikasi C == Python
```
