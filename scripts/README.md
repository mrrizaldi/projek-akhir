# scripts/ — otomasi lintas-komponen

| Skrip | Fungsi |
|---|---|
| `export_artifacts.sh` | Sinkronisasi artefak produsen → konsumen: `model_int8.tflite` → `firmware/include/model_int8.h`; dengan `--laporan`, figure final dari `model/artifacts/metrics/` dan `dashboard/preview.png` → `laporan/<projek>/gambar/` |

```bash
bash scripts/export_artifacts.sh                                 # model -> firmware
bash scripts/export_artifacts.sh --laporan                       # + figure -> laporan/buku-pa/gambar/
LAPORAN_PROJ=proposal-pa bash scripts/export_artifacts.sh --laporan
```

Langkah figure tidak berjalan tanpa `--laporan` karena `laporan/` bersifat
read-only tanpa konfirmasi. Artefak tidak disalin manual.
