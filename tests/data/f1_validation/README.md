# F1 validation fixtures (Phase 1)

Labeled synthetic files for detection precision/recall/F1 (#835).

- **Manifest:** `ground_truth.yaml`
- **Splits:** `measure/` (publish metrics) vs `calibrate/` (threshold tuning only)
- **Harness:** `uv run python scripts/validate_detection_f1.py`
- **Published baseline:** `docs/VALIDATION.md`

Regenerate with:

```bash
uv run python scripts/generate_f1_validation_fixtures.py
```
