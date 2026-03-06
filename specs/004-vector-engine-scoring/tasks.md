# Task Plan: Fix vector engine scoring

**Feature Branch**: `004-vector-engine-scoring`

## Phase 1: TDD setup
- [x] T001
- [ ] T002 Measure score distribution (DEFERRED - User will run manually)
- [ ] T003 Update confidence_threshold (DEFERRED - User will update manually)
- [x] T004 Update promptshield/detection/vector_engine.py to use np.argmax(scores).
