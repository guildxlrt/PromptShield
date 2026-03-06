# Implementation Plan: Fix vector engine scoring

**Branch**: `004-vector-engine-scoring`

## Summary
Revert the vector engine to use the top-1 nearest neighbor and recalibrate `confidence_threshold` to restore detection parity with ChromaDB.

## Technical Context
- Target: `promptshield/detection/vector_engine.py` and `promptshield/config.py` (or similar).
- Change `np.argsort(scores)[-3:].mean()` to `np.argmax(scores)`.
- Use a script to measure score distributions and update the threshold accordingly.

## Constitution Check
- [x] II. Tiered Local Detection Pipeline: Ensuring the local embedding similarity is accurately calibrated for the pipeline.
