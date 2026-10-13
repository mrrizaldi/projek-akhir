import os
import wfdb
from config import RAW_DIR
from src.io_mitdb import load_record  # noqa: E402
record_id = "114"  # yang kebalik channel-nya, bagus buat sanity check
CHANNEL = "MLII"  
# windowed read langsung dari disk (jangan baca full 30 menit trus slice manual)
fs = 360
start_sec, duration_sec = 0, 10

record = wfdb.rdrecord(
  f"{RAW_DIR}/{record_id}",
  sampfrom=0,
  sampto=1800,
  # channels=channel
)
channel = record.sig_name.index(CHANNEL)
record1 = wfdb.rdrecord(
  f"{RAW_DIR}/{record_id}",
  sampfrom=start_sec * fs,
  sampto=(start_sec + duration_sec) * fs,
  channels=[channel]
)

annotation = wfdb.rdann(
  f"{RAW_DIR}/{record_id}", "atr",
  sampfrom=0,
  sampto=3600
) 
signal, r_locations, symbols, fs = load_record(record_id)

# print(annotation.symbol)
# print(annotation.sample)
# print(signal)
# print(r_locations)
# print(symbols)
# annotation.sample[is_beat]
# print(r_locations)
# print(symbols)
# print(fs)
# print(channel)
# print(os.path.join(RAW_DIR, record_id))
# print(f"{RAW_DIR}/{record_id}")
wfdb.plot_wfdb(
    record=record1,
    annotation=annotation,
    # plot_sym=True,          # label simbol beat di atas tiap R-peak
    time_units="seconds",
    title=f"Record {record_id} — {record.sig_name}",
    figsize=(12, 6),
)

# wfdb.plot_all_records(
#     f"{RAW_DIR}",
# )