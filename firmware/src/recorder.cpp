#if defined(ARDUINO) && !defined(PIO_UNIT_TESTING)
#include "recorder.h"

#include <Arduino.h>
#include <LittleFS.h>
#include <sys/stat.h>

#include "acquisition.h"
#include "power.h"
#include "ecg_pipeline.h"
#include "menu.h"
#include "board.h"
#include "display.h"

constexpr size_t RECORDER_N = RECORDER_SAMPLE_MAX;
constexpr int LIST_MAX = 64;
constexpr size_t READ_BLOCK = 512;
constexpr size_t BYTES_PER_SAMPLE_MAX = 6;
constexpr size_t FULL_FILE_SPACE = RECORDER_N * BYTES_PER_SAMPLE_MAX;
constexpr size_t SAMPLES_PER_WRITE = 256;
constexpr char PAUSE_LINE[] = "# jeda\n";
constexpr int BREAKS_MAX = 64;
constexpr size_t WRITE_BLOCK_BYTES = SAMPLES_PER_WRITE * BYTES_PER_SAMPLE_MAX + BREAKS_MAX * sizeof PAUSE_LINE;
constexpr uint32_t BEEP_SAVE_MS = 400;

constexpr size_t SESSION_N = RECORDER_N * RECORDER_PART_MAX;

static uint16_t *buf;
static size_t n, session_limit;
static bool active, paused, stopped_full, held_back;
static int part_max, part_reported;
static size_t leadoff_part[RECORDER_PART_MAX];
static uint32_t missed_start[RECORDER_PART_MAX + 1];
static size_t breaks[BREAKS_MAX];
static int n_breaks;
static int saved_number;
static uint32_t t_saved;

struct writer_t {
    File f;
    const uint16_t *data;
    size_t n, i, leadoff, byte;
    size_t breaks[BREAKS_MAX];
    int n_breaks, k, part, n_parts, first_number;
    unsigned missed;
    char path[24];
};
static writer_t writer;
static bool writing;
static char write_block[WRITE_BLOCK_BYTES];

bool recorder_active(void) { return active; }
bool recorder_paused(void) { return active && paused; }
bool recorder_writing(void) { return writing; }
bool recorder_reject(const char *what)
{
    if (!active) return false;
    Serial.printf("DITOLAK: %s selama sesi rekam, simpan dulu (tahan B3 / r)\n", what);
    return true;
}
int recorder_newly_saved(void) { return saved_number && millis() - t_saved < 3000 ? saved_number : 0; }
int recorder_part(void) { return (int)min<size_t>(n / RECORDER_N, part_max ? part_max - 1 : 0) + 1; }
size_t recorder_n(void) { return n - (size_t)(recorder_part() - 1) * RECORDER_N; }
size_t recorder_n_session(void) { return n; }

static size_t free_space() { return LittleFS.totalBytes() - LittleFS.usedBytes(); }

static void file_name(int number, char *out, size_t len) { snprintf(out, len, RECORDER_PATTERN, number); }

int recorder_list(int *number, int max_count)
{
    int k = 0;
    File d = LittleFS.open(RECORDER_DIR);
    if (!d || !d.isDirectory()) return 0;
    for (File f = d.openNextFile(); f && k < max_count; f = d.openNextFile()) {
        const int x = atoi(f.name());
        if (x <= 0) continue;
        int j = k++;
        while (j > 0 && number[j - 1] > x) { number[j] = number[j - 1]; j--; }
        number[j] = x;
    }
    return k;
}

static int last()
{
    int max_count = 0;
    File d = LittleFS.open(RECORDER_DIR);
    if (!d || !d.isDirectory()) return 0;
    for (File f = d.openNextFile(); f; f = d.openNextFile()) max_count = max(max_count, atoi(f.name()));
    return max_count;
}

void recorder_prepare(void)
{
    buf = (uint16_t *)ps_malloc(SESSION_N * sizeof(uint16_t));
    if (!buf) Serial.println("PERINGATAN: PSRAM gagal, perekaman mentah nonaktif");
    if (!LittleFS.begin(true)) { Serial.println("PERINGATAN: LittleFS gagal mount"); return; }
    LittleFS.mkdir(RECORDER_DIR);
    struct stat st;
    if (stat("/littlefs/rekaman.csv", &st) == 0 && !last()) {
        char p[24];
        file_name(1, p, sizeof p);
        if (LittleFS.rename("/rekaman.csv", p))
            Serial.printf("rekam: /rekaman.csv lama dipindah ke %s\n", p);
    }
}

static unsigned missed_part(int k)
{
    const int n_parts = (int)((n + RECORDER_N - 1) / RECORDER_N);
    return missed_start[k + 1 < n_parts ? k + 1 : RECORDER_PART_MAX] - missed_start[k];
}

static bool open_part(int k)
{
    const int number = writer.first_number + k;
    writer.part = k;
    file_name(number, writer.path, sizeof writer.path);
    writer.f = LittleFS.open(writer.path, "w");
    if (!writer.f) {
        writing = false;
        held_back = true;
        Serial.printf("GAGAL membuka %s: bagian %d-%d tetap di PSRAM, ulangi simpan dengan r / tahan B3\n",
                      writer.path, k + 1, writer.n_parts);
        display_message("GAGAL SIMPAN", "tekan r ulangi");
        return false;
    }
    const size_t start = (size_t)k * RECORDER_N;
    writer.data = buf + start;
    writer.n = min(n - start, RECORDER_N);
    writer.i = 0;
    writer.k = 0;
    writer.leadoff = leadoff_part[k];
    writer.missed = missed_part(k);
    writer.n_breaks = 0;
    for (int j = 0; j < n_breaks; j++)
        if (breaks[j] > start && breaks[j] < start + writer.n) writer.breaks[writer.n_breaks++] = breaks[j] - start;
    const float percent = writer.n ? 100.0f * writer.leadoff / writer.n : 0.0f;
    writer.byte = writer.f.printf("# fs=%u n=%u lewat=%u lepas=%u (%.0f%%)", ECG_FS, (unsigned)writer.n,
                                writer.missed, (unsigned)writer.leadoff, percent);
    if (k) writer.byte += writer.f.printf(" lanjutan=%03d celah=0", number - 1);
    writer.byte += writer.f.print("\n");
    writing = true;
    held_back = false;
    return true;
}

static void close_write(bool failed)
{
    writer.f.close();
    const size_t size = LittleFS.open(writer.path, "r").size();
    const float percent = writer.n ? 100.0f * writer.leadoff / writer.n : 0.0f;
    if (failed) Serial.printf("GAGAL: LittleFS penuh setelah %u sampel, %s terpotong\n",
                             (unsigned)writer.i, writer.path);
    if (size != writer.byte)
        Serial.printf("PERINGATAN: %s berukuran %u B, tertulis %u B\n", writer.path, (unsigned)size,
                      (unsigned)writer.byte);
    Serial.printf("SIMPAN %u sampel (%.1f detik, %d segmen), %u terlewat, elektroda lepas %.0f%% -> %s\n",
                  (unsigned)writer.n, (float)writer.n / ECG_FS, writer.n_breaks + 1, writer.missed, percent,
                  writer.path);
    if (writer.leadoff > writer.n / 10)
        Serial.println("PERINGATAN: elektroda lepas >10% — rekaman ini kemungkinan besar kosong.");
    saved_number = writer.first_number + writer.part;
    t_saved = millis();
    writing = false;
    if (!failed && writer.part + 1 < writer.n_parts) { open_part(writer.part + 1); return; }
    display_sound(BEEP_SAVE_MS);
}

static void write_step()
{
    size_t len = 0;
    const size_t end = min(writer.n, writer.i + SAMPLES_PER_WRITE);
    for (; writer.i < end; writer.i++) {
        if (writer.k < writer.n_breaks && writer.breaks[writer.k] == writer.i) {
            len += snprintf(write_block + len, sizeof write_block - len, "%s", PAUSE_LINE);
            writer.k++;
        }
        len += snprintf(write_block + len, sizeof write_block - len, "%u\n", writer.data[writer.i]);
    }
    const size_t written = writer.f.write((const uint8_t *)write_block, len);
    writer.byte += written;
    const bool failed = written != len;
    if (failed || writer.i >= writer.n) close_write(failed);
}

static void finish_write()
{
    while (writing) write_step();
}

static void save_session()
{
    active = false;
    buzzer(false);
    missed_start[RECORDER_PART_MAX] = acquisition_missed();
    if (n_breaks && breaks[n_breaks - 1] >= n) n_breaks--;
    writer.n_parts = (int)((n + RECORDER_N - 1) / RECORDER_N);
    if (!writer.n_parts) { Serial.println("REKAM: sesi kosong, tidak ada yang disimpan"); return; }
    writer.first_number = last() + 1;
    Serial.printf("REKAM berhenti: %u sampel (%.1f detik), menulis %d berkas dari PSRAM\n", (unsigned)n,
                  (float)n / ECG_FS, writer.n_parts);
    open_part(0);
}

void recorder_service(void)
{
    if (active && recorder_part() != part_reported) {
        part_reported = recorder_part();
        Serial.printf("REKAM lanjut bagian %d (di PSRAM, ditulis saat berhenti)\n", part_reported);
    }
    if (stopped_full) {
        stopped_full = false;
        const bool has_room = part_max < RECORDER_PART_MAX;
        Serial.printf("REKAM berhenti: batas sesi %d bagian (%u detik) tercapai%s\n", part_max,
                      (unsigned)(session_limit / ECG_FS), has_room ? ", LittleFS tidak cukup untuk bagian berikutnya" : "");
        display_message(has_room ? "RUANG PENUH" : "BATAS SESI", "menyimpan...");
        save_session();
    }
    if (writing && !acquisition_fill()) write_step();
}

void recorder_sample(uint16_t s)
{
    if (!active || paused || !buf) return;
    const size_t k = n / RECORDER_N;
    if (n % RECORDER_N == 0) missed_start[k] = acquisition_missed();
    buf[n++] = s;
    if (digitalRead(PIN_LOP) || digitalRead(PIN_LON)) leadoff_part[k]++;
    if (n >= session_limit) { active = false; stopped_full = true; }
}

void recorder_toggle(void)
{
    if (active) { save_session(); return; }
    if (held_back) { open_part(writer.part); return; }
    const int last_number = last();
    part_max = (int)min<size_t>(RECORDER_PART_MAX, free_space() / FULL_FILE_SPACE);
    part_max = min(part_max, RECORDER_NUMBER_MAX - last_number);
    const char *reject = acquisition_source() != SOURCE_ADC ? "REKAM hanya dari sensor"
                      : power_mode() >= 0 ? "REKAM ditolak: mode daya pN aktif ('p' = normal)"
                      : menu_is_open() ? "REKAM ditolak: tutup menu dulu"
                      : writing ? "REKAM ditolak: masih menyimpan sesi sebelumnya"
                      : !buf ? "REKAM ditolak: PSRAM tidak tersedia"
                      : last_number >= RECORDER_NUMBER_MAX ? "REKAM ditolak: nomor rekaman habis, hapus dulu (h<n>)"
                      : part_max <= 0 ? "REKAM ditolak: LittleFS penuh, tarik data dulu" : nullptr;
    if (reject) {
        Serial.println(reject);
        const bool waiting = writing;
        display_message(waiting ? "TUNGGU" : acquisition_source() != SOURCE_ADC || power_mode() >= 0 || menu_is_open() ? "TOLAK" : "PENUH",
                       waiting ? "masih menyimpan" : acquisition_replay() ? "hanya sensor ADC" : "rekam ditolak");
        return;
    }
    session_limit = (size_t)part_max * RECORDER_N;
    n = 0;
    n_breaks = 0;
    paused = false;
    stopped_full = false;
    part_reported = 1;
    memset(leadoff_part, 0, sizeof leadoff_part);
    memset(missed_start, 0, sizeof missed_start);
    acquisition_zero_missed();
    active = true;
    Serial.printf("REKAM mulai (maks %d bagian = %u detik)\n", part_max, (unsigned)(session_limit / ECG_FS));
}

void recorder_pause(void)
{
    if (!active) { Serial.println("REKAM: tidak sedang merekam"); return; }
    paused = !paused;
    if (paused && n && (!n_breaks || breaks[n_breaks - 1] < n)) {
        if (n_breaks < BREAKS_MAX) breaks[n_breaks++] = n;
        else Serial.println("PERINGATAN: batas jeda penuh, segmen ini lebur dengan berikutnya");
    }
    Serial.printf("REKAM %s n=%u (%.1f detik)\n", paused ? "jeda" : "lanjut", (unsigned)n,
                  (float)n / ECG_FS);
}

bool recorder_dump(int number)
{
    finish_write();
    if (number <= 0) number = last();
    char p[24];
    file_name(number, p, sizeof p);
    File f = number > 0 ? LittleFS.open(p, "r") : File();
    if (!f) { Serial.println("Belum ada rekaman."); return false; }
    Serial.println("---MULAI---");
    while (f.available()) Serial.write(f.read());
    Serial.println("---SELESAI---");
    f.close();
    return true;
}

bool recorder_delete(int number)
{
    finish_write();
    char p[24];
    file_name(number, p, sizeof p);
    const bool ok = LittleFS.remove(p);
    Serial.printf("rekam: hapus %s %s\n", p, ok ? "OK" : "GAGAL (tidak ada)");
    return ok;
}

void recorder_print_list(void)
{
    int numbers[LIST_MAX];
    const int k = recorder_list(numbers, LIST_MAX);
    Serial.printf("rekam: %d berkas, LittleFS %u/%u KB\n", k,
                  (unsigned)(LittleFS.usedBytes() / 1024), (unsigned)(LittleFS.totalBytes() / 1024));
    for (int i = 0; i < k; i++) {
        char p[24];
        file_name(numbers[i], p, sizeof p);
        File f = LittleFS.open(p, "r");
        Serial.printf("  %3d  %6u B  %s\n", numbers[i], (unsigned)f.size(), f.readStringUntil('\n').c_str());
        f.close();
    }
}
size_t recorder_sample_n(int number)
{
    char p[24];
    file_name(number, p, sizeof p);
    File f = LittleFS.open(p, "r");
    if (!f) return 0;
    const String h = f.readStringUntil('\n');
    f.close();
    const int k = h.indexOf(" n=");
    return k < 0 ? 0 : (size_t)atol(h.c_str() + k + 3);
}

size_t recorder_load(int number, uint16_t *buf, size_t max_count)
{
    finish_write();
    char p[24];
    file_name(number, p, sizeof p);
    File f = number > 0 ? LittleFS.open(p, "r") : File();
    if (!f) return 0;
    uint8_t block[READ_BLOCK];
    size_t k = 0;
    uint32_t v = 0;
    bool has_digits = false, comment = false;
    for (int m; k < max_count && (m = f.read(block, sizeof block)) > 0;) {
        for (int j = 0; j < m && k < max_count; j++) {
            const char c = block[j];
            if (c == '\n') {
                if (has_digits && !comment) buf[k++] = (uint16_t)min<uint32_t>(v, 4095);
                v = 0; has_digits = comment = false;
            } else if (c == '#' && !has_digits) comment = true;
            else if (c >= '0' && c <= '9' && !comment) { v = v * 10 + (c - '0'); has_digits = true; }
        }
    }
    if (has_digits && !comment && k < max_count) buf[k++] = (uint16_t)min<uint32_t>(v, 4095);
    f.close();
    return k;
}
#endif
