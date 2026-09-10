// Firmware ESP32-S3 — placeholder.
// TODO manual: akuisisi AD8232 -> ecg_pipeline.h (sudah diport & terverifikasi)
//   -> inferensi TFLite Micro (model_int8.h) -> MQTT -> ring buffer PSRAM.
//
// PIO_UNIT_TESTING didefinisikan PlatformIO saat `pio test`; setup()/loop() di
// sini harus menyingkir supaya tidak bentrok dengan milik file test.
#ifndef PIO_UNIT_TESTING

void setup() {}
void loop()  {}

#endif  // PIO_UNIT_TESTING
