# Feature Specification: CLI Tool & SDK

**Feature Branch**: `002-cli-tool`  
**Created**: 2026-03-02  
**Status**: Draft  

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Python Library Interface (Priority: P1)

Developers can import PromptShield as a Python library and run scans programmatically in their applications.

**Why this priority**: Core value proposition. Developers want frictionless programmatic integration.

**Independent Test**: Can be fully tested by writing a simple Python script that imports `promptshield.Shield`, configures it with an API key, and calls `shield.scan()`.

**Acceptance Scenarios**:

1. **Given** a valid configuration, **When** calling `shield.scan(prompt="ignore instructions")`, **Then** the result correctly identifies a prompt injection with a high confidence score and blocked verdict.
2. **Given** an invalid API key, **When** the pipeline falls back to the LLM engine, **Then** an appropriate error is raised.

---

### User Story 2 - CLI Command Interface (Priority: P2)

Developers can use the `promptshield` CLI to scan text, initialize config, or check CI pipelines.

**Why this priority**: Allows for manual testing and automated CI workflows without writing custom Python wrappers.

**Independent Test**: Can be fully tested by running `promptshield scan "..."` in the terminal and verifying the output format and exit codes.

**Acceptance Scenarios**:

1. **Given** a malicious input string, **When** running `promptshield scan "..."`, **Then** the command outputs JSON and returns a non-zero exit code (1).
2. **Given** the `--pretty` flag, **When** running a scan, **Then** it outputs a colored, human-readable UI.
3. **Given** no existing configuration, **When** running `promptshield init`, **Then** a `.promptshield.yaml` file is generated.

---

### User Story 3 - Local Server Mode (Priority: P3)

Developers can run a local FastAPI server to consume PromptShield via HTTP from non-Python applications.

**Why this priority**: Supports polyglot environments where PromptShield is needed but the host application is not in Python.

**Independent Test**: Can be tested by running `promptshield server` and sending a POST request to `http://127.0.0.1:8765/v1/scan`.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** sending a valid POST request to `/v1/scan`, **Then** it returns the exact same JSON schema as the library/CLI outputs.
2. **Given** the server is running, **When** a malicious prompt is sent, **Then** the dogfooding mechanism processes the threat correctly.

### Edge Cases

- What happens when a scan request lacks sufficient context? (Defaults to zero context, relying only on user prompt).
- How does the system handle missing configuration files? (Falls back to env vars, then fails gracefully).
- How does the system handle an unavailable ChromaDB file? (It reseeds cleanly on startup).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `Shield` class that can be imported and instantiated without complex boilerplate.
- **FR-002**: System MUST provide a `promptshield` CLI with `scan`, `init`, and `server` subcommands.
- **FR-003**: System MUST expose a `/v1/scan` endpoint in server mode that matches the core scan contract.
- **FR-004**: System MUST return a unified scan contract containing `verdict`, `threat_type`, `confidence`, `reason`, `sanitized_prompt`, `scan_id`, and `pipeline_layer`.
- **FR-005**: Configuration MUST be resolved in the order: CLI flags > Environment Variables > `.promptshield.yaml`.
- **FR-006**: The detection pipeline MUST run entirely locally (Regex -> ephemeral ChromaDB -> LLM provider via API).
- **FR-007**: System MUST NOT include any billing, API key management, or multi-user architecture.
- **FR-008**: PyPI publication is deferred — not part of v1 scope. Current distribution method: git install via GitHub URL. Note that `pyproject.toml` is ready for PyPI when needed.

### Key Entities

- **ScanResult**: Data class/Pydantic model representing the output of a scan.
- **ShieldConfig**: Data class representing the resolved configuration of the system.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Programmatic scans taking the regex/embedding path resolve in < 500ms.
- **SC-002**: Programmatic scans requiring the LLM fallback path resolve in < 2s.
- **SC-003**: CLI returns a clean exit code 0 for safe prompts and 1 for blocked prompts.
- **SC-004**: The package can be installed and successfully executed on a clean Python 3.11 environment with minimal dependencies.