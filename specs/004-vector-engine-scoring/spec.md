# Feature Specification: Fix vector engine scoring

**Feature Branch**: `004-vector-engine-scoring`
**Created**: 2026-03-06
**Status**: Draft
**Input**: Fix vector engine scoring: revert to top-1 nearest neighbor and recalibrate confidence_threshold to restore detection parity with the original ChromaDB implementation

## User Scenarios & Testing

### User Story 1 - Restore Detection Parity
The vector engine should correctly classify inputs based on the nearest neighbor rather than an average of top-3.
**Acceptance Scenarios**:
1. **Given** a malicious prompt, **When** it is scanned, **Then** it is evaluated against the single best matching vector score.
2. **Given** a prompt, **When** scored, **Then** the best score is compared to the recalibrated confidence threshold.
3. **Given** a known attack prompt, **Then** it should score higher than a safe prompt.

## Requirements
- **FR-001**: Change `scan_vector` to use the top-1 score instead of averaging the top-3.
- **FR-002**: Recalibrate `confidence_threshold` to a measured value on the cosine similarity scale `[0.0, 1.0]`.
