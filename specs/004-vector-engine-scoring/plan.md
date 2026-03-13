# Implementation Plan: Fix vector engine scoring

**Branch**: `004-vector-engine-scoring` | **Status**: ⚠️ **PARTIALLY IMPLEMENTED** (FR-002 threshold recalibration deferred)

## Summary
Revert the vector engine to use the top-1 nearest neighbor and recalibrate `confidence_threshold` to restore detection parity with ChromaDB.

Replaces top-3 average with np.argmax to match original ChromaDB
behavior. Averaging was diluting confidence scores and causing
attacks to fall below detection threshold.

**Status Note (2025)**: FR-001 (top-1 nearest neighbor) is ✅ **implemented** in `promptshield/detection/vector_engine.py` (see `np.argmax(scores)`). FR-002 (threshold recalibration) is ⚠️ **deferred** — the confidence threshold remains at the default 0.42, pending manual calibration against measured `text-embedding-3-small` score distributions. See benchmark results for current detection accuracy.

## Technical Context
- Target: `promptshield/detection/vector_engine.py` and `promptshield/config.py` (or similar).
- Change `np.argsort(scores)[-3:].mean()` to `np.argmax(scores)`.
- Use a script to measure score distributions and update the threshold accordingly.

## Constitution Check
- [x] II. Tiered Local Detection Pipeline: Ensuring the local embedding similarity is accurately calibrated for the pipeline.
