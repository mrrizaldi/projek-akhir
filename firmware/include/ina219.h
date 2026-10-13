// Konversi register INA219 -> satuan teknik. Murni, tanpa I2C dan tanpa
// Arduino, supaya bisa diuji di PC (pio test -e native).
//
// Register kalibrasi on-chip tidak dipakai: R_SHUNT dibagi di software supaya
// jadi knob kalibrasi eksplisit terhadap multimeter.
#ifndef INA219_H
#define INA219_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define INA219_ALAMAT     0x40      // A0=A1=GND (bawaan modul)
#define INA219_REG_CONFIG 0x00
#define INA219_REG_SHUNT  0x01
#define INA219_REG_BUS    0x02

// BRNG=32V, PGA=/8 (+-320 mV = +-3,2 A pada 0,1 ohm), BADC & SADC = rata-rata
// 128 sampel (~68 ms), MODE = shunt+bus kontinu. PGA /8 karena burst TX WiFi
// melewati +-400 mA milik PGA /1; LSB register shunt tetap 10 uV di semua PGA.
// Averaging WAJIB: arus alat ini berdenyut mengikuti burst 33 ms (HW-3),
// pembacaan sesaat melompat tanpa arti.
#define INA219_CONFIG     0x3FFF

// Shunt voltage: 1 LSB = 0,01 mV, signed. mV / ohm = mA.
float ina219_arus_mA(int16_t shunt_reg, float r_shunt_ohm);

// Bus voltage: nilai di bit 15:3, 1 LSB = 4 mV. Bit 1 (CNVR) & 0 (OVF) dibuang.
float ina219_bus_V(uint16_t bus_reg);

#ifdef ARDUINO
// Bagian I2C, cuma di board. Tulis config lalu baca balik: modul yang tidak
// ada membalas 0x0000/0xFFFF, jadi "tidak terpasang" terdeteksi, bukan 0 mA.
bool ina219_mulai(int pin_sda, int pin_scl);
// false = modul tidak menjawab (kabel lepas di tengah jalan).
bool ina219_baca(float r_shunt_ohm, float *arus_mA, float *bus_V);
// Register mentah, untuk diagnosa (bit 0 register bus = OVF, bit 1 = CNVR).
bool ina219_baca_reg(uint8_t reg, uint16_t *out);
#endif

#ifdef __cplusplus
}
#endif
#endif  // INA219_H
