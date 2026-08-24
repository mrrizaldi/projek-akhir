# Orkestrator jalur model. Urutan fase mengikuti PRD_Model_Aritmia_TinyML.pdf.
# Logika algoritma ada di src/ (modul) & scripts/ (eksekusi) — bukan di sini.
PY := python

.PHONY: data check plot0 plot1 prep split train eval quantize export test clean help

help:
	@grep -E '^[a-z0-9]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

## ── Fase 0 — data & verifikasi loader ────────────────────────────────────────
data:  ## download MIT-BIH ke data/raw/mitdb (sekali jalan)
	$(PY) scripts/download_data.py
check: ## cek kelengkapan .hea/.dat/.atr
	$(PY) scripts/check_dataset.py
plot0: ## verifikasi Fase 0 — overlay R-peak anotasi
	$(PY) scripts/plot_fase0.py 100

## ── Fase 1 — preprocessing (golden reference) ────────────────────────────────
plot1: ## verifikasi Fase 1 — raw vs bandpass, window N vs V
	$(PY) scripts/plot_fase1.py 100

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

## ── Verifikasi & bersih-bersih ───────────────────────────────────────────────
test: ## assert DoD yang berupa angka
	pytest tests/ -q
clean: ## hapus artefak turunan; data/raw & model terlatih AMAN
	rm -rf data/processed artifacts/metrics/*.png artifacts/metrics/*.csv
