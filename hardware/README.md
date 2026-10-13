# hardware/ — perangkat keras

Alat terdiri atas ESP32-S3 N16R8, front-end EKG AD8232, layar TFT ST7789
1,47" 172×320, modul buzzer pasif (aktif LOW), tiga tombol, dan sensor arus
INA219 di jalur daya.

- **Skematik PCB rev1** (KiCad) berada di luar repo dan tidak di-commit.
- **Penyesuaian rev1 → rev2** (TFT, buzzer, tombol, AD8232, pin map rev2, dan
  catatan rangkaian baterai): [`model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md`](../model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md).
- **Pin map yang dipakai firmware** (breadboard untuk firmware utama, PCB untuk
  env `hwtest`): [`firmware/README.md`](../firmware/README.md) §Pin map.
- **Uji rangkaian di breadboard:** `cd firmware && pio run -e hwtest -t upload`.
