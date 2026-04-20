# Adversarial Audit

This file records the adversarial checks run during hardening and the fixes applied.

## Scope

- core engines
- multipage Streamlit flows
- rerun/state behavior
- retrieval fallback behavior
- script/bootstrap sanity

## Checks Performed

### Static / import checks
- `python3 -m compileall main.py core pages fine_tuning`
- direct imports for `vision_engine.py`
- direct schema validation for `function_calling.py`

### Retrieval sanity checks
- built a local `rag_engine.py` index from sample documents
- ran retrieval against a real question
- confirmed top chunks returned cleanly

### Service startup checks
- Streamlit startup smoke tests on multiple ports
- LightRAG startup and port validation
- judge-runner script syntax validation

## Findings And Fixes

### 1. Missing planned engine modules

**Finding**
- the repo plan referenced `rag_engine.py`, `vision_engine.py`, and `function_calling.py`
- those modules did not exist

**Fix**
- added all three modules in `core/`

### 2. NeuroRead hard-failed if LightRAG was unavailable

**Finding**
- the page stopped completely when LightRAG was down
- this was risky in live demos and diverged from the original architecture plan

**Fix**
- added local `rag_engine.py` fallback mode
- `NeuroRead` now works even without LightRAG, with chunk-based grounded retrieval

### 3. Repeated rerun-state bug across several pages

**Finding**
- several pages generated outputs inside `if st.button(...)` blocks
- exports or follow-up actions disappeared on rerun

**Affected pages fixed**
- `07_GraphiQ.py`
- `09_CodeBuddy.py`
- `10_DSASage.py`
- `15_IdeaSpark.py`
- `16_FeatureForge.py`

**Fix**
- added `st.session_state` persistence via `page_state.py`
- rewired exports to use persisted output instead of transient local variables

### 4. NeuroRead export formatting assumed LightRAG-only references

**Finding**
- local fallback references used chunk IDs/scores, but export formatting assumed `reference_id` + `file_path`

**Fix**
- export now formats source lines correctly for both LightRAG and local fallback retrieval

### 5. Follow-up context quality was weak in grounded Q&A

**Finding**
- one-shot questions worked, but follow-up questions felt disconnected

**Fix**
- added short conversation memory to:
  - `NeuroRead`
  - `PaperAnalyzer`
- LightRAG queries now pass `conversation_history`

## Remaining Risks

1. LightRAG still depends on a separate running server in the preferred path
2. `vision_engine.py` requires a vision-capable Ollama model to be truly useful in runtime
3. many pages still rely on prompt quality rather than trained adapters
4. no fine-tuned checkpoints have been produced yet, so all adapter recommendations remain unexecuted strategy until GPU runs happen

## Overall Result

The app is materially more robust than before this audit, especially around:

- fallback retrieval
- page rerun behavior
- export reliability
- architecture alignment with the project plan
