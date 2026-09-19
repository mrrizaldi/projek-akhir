# Orkestrator jalur model. Urutan fase mengikuti PRD_Model_Aritmia_TinyML.pdf.
# Logika algoritma ada di src/ (modul) & scripts/ (eksekusi) — bukan di sini.
PY := $(if $(wildcard .venv/bin/python),.venv/bin/python,python)
REC ?= 100          # record buat target plot: make plot0 REC=114

.PHONY: data data-semua check plot0 plot1 plot1seg prep split train eval quantize export poc pull analisis test clean help

help:
	@grep -E '^[a-z0-9-]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

## ── Fase 0 — data & verifikasi loader ────────────────────────────────────────
data:  ## download MIT-BIH ke data/raw/mitdb (sekali jalan)
	$(PY) scripts/download_data.py $(DB)
data-semua: ## + svdb & incartdb (Fase A, ~1 GB) -> data/raw/<db>/
	$(PY) scripts/download_data.py --semua
check: ## cek kelengkapan .hea/.dat/.atr
	$(PY) scripts/check_dataset.py
plot0: ## verifikasi Fase 0 — overlay R-peak anotasi
	$(PY) scripts/plot_fase0.py $(REC)

## ── Fase 1 — preprocessing (golden reference) ────────────────────────────────
plot1: ## verifikasi Fase 1a — raw vs bandpass (domain waktu + PSD)
	$(PY) scripts/plot_fase1.py $(REC)
plot1seg: ## verifikasi Fase 1b — segmentasi + z-score per window
	$(PY) scripts/plot_fase1_segment.py $(REC)

## ── Fase 2 — beat, label, fitur RR ───────────────────────────────────────────
data/processed/per_record/.stamp: config.py src/preprocessing.py src/features_rr.py
	$(PY) scripts/prep_beats.py && touch $@
prep: data/processed/per_record/.stamp  ## ekstrak beat+label+RR per record

## ── Fase 3 — split inter-patient ─────────────────────────────────────────────
data/processed/train.npz: data/processed/per_record/.stamp config.py src/dataset.py
	$(PY) scripts/build_split.py
split: data/processed/train.npz  ## rakit train.npz (DS1) & test.npz (DS2)

## ── Fase 5-7 ─────────────────────────────────────────────────────────────────
train: data/processed/train.npz  ## latih model di DS1 → artifacts/model_fp32.keras
	$(PY) scripts/train_model.py
eval: ## evaluasi float32 di DS2 → confusion matrix + tabel metrik
	$(PY) scripts/eval_fp32.py
quantize: ## PTQ INT8 + evaluasi ulang + tabel delta
	$(PY) scripts/quantize_int8.py
export: ## salin artefak ke firmware/ & laporan/
	bash ../scripts/export_artifacts.sh

## ── Akuisisi dari device ─────────────────────────────────────────────────────
pull: ## tarik rekaman dari board -> data/recordings/<tanggal-jam>.csv
	$(PY) scripts/pull_recording.py
analisis: ## analisis rekaman: make analisis FILE=data/recordings/xxx.csv
	$(PY) scripts/analyze_recording.py $(FILE) $(basename $(notdir $(FILE)))

## ── Fase 8 — checklist PoC ───────────────────────────────────────────────────
poc: ## verifikasi 8 item DoD PRD secara mekanis
	$(PY) scripts/check_poc.py

## ── Verifikasi & bersih-bersih ───────────────────────────────────────────────
test: ## assert DoD yang berupa angka
	$(PY) -m pytest tests/ -q
clean: ## hapus artefak turunan; data/raw & model terlatih AMAN
	rm -rf data/processed artifacts/metrics/*.png artifacts/metrics/*.csv
