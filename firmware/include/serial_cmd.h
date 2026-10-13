// Perintah serial satu huruf (+ angka opsional). Daftar lengkap di serial_cmd.cpp.
// Baris pertama balasan 's' dan baris 'SIMPAN'/'---MULAI---' di-parse alat di
// model/scripts/ (pull_recording.py, measure_power.py): formatnya kontrak.
#ifndef SERIAL_CMD_H
#define SERIAL_CMD_H

void serial_cmd_layani(void);              // tiap iterasi loop()

#endif
