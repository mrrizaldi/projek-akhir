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

// BRNG=16V, PGA=/1 (+-40 mV), BADC & SADC = rata-rata 128 sampel (~68 ms),
// MODE = shunt+bus kontinu. Averaging WAJIB: arus alat ini berdenyut mengikuti
// burst 33 ms (HW-3), pembacaan sesaat melompat tanpa arti.
#define INA219_CONFIG     0x07FF

// Shunt voltage: 1 LSB = 0,01 mV, signed. mV / ohm = mA.
float ina219_arus_mA(int16_t shunt_reg, float r_shunt_ohm);

// Bus voltage: nilai di bit 15:3, 1 LSB = 4 mV. Bit 1 (CNVR) & 0 (OVF) dibuang.
float ina219_bus_V(uint16_t bus_reg);

#ifdef __cplusplus
}
#endif
#endif  // INA219_H
