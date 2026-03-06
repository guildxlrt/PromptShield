# Implementation Plan: Fix vector engine scoring

**Branch**: `004-vector-engine-scoring`

## Summary
Revert the vector engine to use the top-1 nearest neighbor and recalibrate `confidence_threshold` to restore detection parity with ChromaDB.

Replaces top-3 average with np.argmax to match original ChromaDB
behavior. Averaging was diluting confidence scores and causing
attacks to fall below detection threshold.

confidence_threshold left unchanged pending manual calibration
against real text-embedding-3-small embeddings.

## Technical Context
- Target: `promptshield/detection/vector_engine.py` and `promptshield/config.py` (or similar).
- Change `np.argsort(scores)[-3:].mean()` to `np.argmax(scores)`.
- Use a script to measure score distributions and update the threshold accordingly.

## Constitution Check
- [x] II. Tiered Local Detection Pipeline: Ensuring the local embedding similarity is accurately calibrated for the pipeline.
