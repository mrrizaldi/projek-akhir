#ifndef RECORDER_H
#define RECORDER_H

#include <stddef.h>
#include <stdint.h>
#include "ecg_preproc.h"

#define RECORDER_DIR  "/rekam"
#define RECORDER_PATTERN "/rekam/%03d.csv"
#ifndef RECORDER_NUMBER
#define RECORDER_NUMBER 999
#endif
constexpr int RECORDER_NUMBER_MAX = RECORDER_NUMBER;
#ifndef RECORDER_SECONDS
#define RECORDER_SECONDS 300
#endif
constexpr size_t RECORDER_SECONDS_MAX = RECORDER_SECONDS;
constexpr size_t RECORDER_SAMPLE_MAX = (size_t)ECG_FS * RECORDER_SECONDS_MAX;
#ifndef RECORDER_PART
#define RECORDER_PART 6
#endif
constexpr int RECORDER_PART_MAX = RECORDER_PART;

void recorder_prepare(void);

bool recorder_active(void);
bool recorder_reject(const char *what);
bool recorder_paused(void);
bool recorder_writing(void);
void recorder_service(void);
size_t recorder_n(void);
size_t recorder_n_session(void);
int recorder_part(void);
void recorder_toggle(void);
void recorder_pause(void);
int recorder_newly_saved(void);
void recorder_sample(uint16_t s);

int recorder_list(int *number, int max_count);
void recorder_print_list(void);
bool recorder_dump(int number);
bool recorder_delete(int number);

size_t recorder_sample_n(int number);
size_t recorder_load(int number, uint16_t *buf, size_t max_count);

#endif
