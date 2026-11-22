PY := $(if $(wildcard .venv/bin/python),.venv/bin/python,python)
REC ?= 100

.PHONY: data data-all check plot0 plot1 plot1seg prep split split-multi train eval quantize export poc pull pull-power analyze plot broker-info test clean help

help:
	@grep -E '^[a-z0-9-]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

data:  ## download MIT-BIH to data/raw/mitdb (run once)
	$(PY) scripts/download_data.py $(DB)
data-all: ## + svdb & incartdb (Phase A, ~1 GB) -> data/raw/<db>/
	$(PY) scripts/download_data.py --all
check: ## check .hea/.dat/.atr completeness
	$(PY) scripts/check_dataset.py
plot0: ## verify Phase 0: annotated R-peak overlay (REC=<record>, default 100)
	$(PY) scripts/plot_phase0.py $(REC)

plot1: ## verify Phase 1a: raw vs bandpass (time domain + PSD)
	$(PY) scripts/plot_phase1.py $(REC)
plot1seg: ## verify Phase 1b: segmentation + per-window z-score
	$(PY) scripts/plot_phase1_segment.py $(REC)

data/processed/per_record/.stamp: config.py src/preprocessing.py src/features_rr.py
	$(PY) scripts/prep_beats.py && touch $@
prep: data/processed/per_record/.stamp  ## extract beats + labels + RR per record

data/processed/train.npz: data/processed/per_record/.stamp config.py src/dataset.py
	$(PY) scripts/build_split.py
split: data/processed/train.npz  ## build train.npz (DS1) & test.npz (DS2)
split-multi: ## Phase A: train_multi.npz + test_ds2.npz + test_<db>.npz
	$(PY) scripts/build_split.py --combined

train: data/processed/train.npz  ## train the model on DS1 → artifacts/model_fp32.keras
	$(PY) scripts/train_model.py
eval: ## evaluate float32 on DS2 → confusion matrix + metrics table
	$(PY) scripts/eval_fp32.py
quantize: ## INT8 PTQ + re-evaluation + delta table
	$(PY) scripts/quantize_int8.py
export: ## copy artifacts to firmware/ & laporan/
	bash ../scripts/export_artifacts.sh

pull: ## pull a recording from the board (N=number, default last) -> data/recordings/<date-time>.csv
	$(PY) scripts/pull_recording.py $(N)
pull-power: ## pull the standalone power sweep result (N=number, default last) -> artifacts/metrics/daya/
	$(PY) scripts/pull_power.py $(N)
analyze: ## analyze a recording: make analyze FILE=data/recordings/xxx.csv [TITLE="plot title"]
	$(PY) scripts/analyze_recording.py $(FILE) $(basename $(notdir $(FILE))) $(if $(TITLE),"$(TITLE)")
plot: ## ECG plot of the best 60 seconds: make plot FILE=data/recordings/xxx.csv [START=seconds]
	$(PY) scripts/plot_recording.py $(FILE) $(if $(START),--start $(START))
broker-info: ## WiFi SSID, LAN IP, ports 1883/8080, wifi_secrets.h entry suggestion
	$(PY) scripts/broker_info.py

poc: ## verify the 8 PRD DoD items mechanically
	$(PY) scripts/check_poc.py

test: ## assert the numeric DoD items
	$(PY) -m pytest tests/ -q
clean: ## delete derived artifacts; data/raw & the trained model are SAFE
	rm -rf data/processed artifacts/metrics/*.png artifacts/metrics/*.csv
