# Staging / lab configuration (fuzzy + format hints)

**Português:** use os mesmos caminhos; o texto detalhado está em `docs/SENSITIVITY_DETECTION.pt_BR.md`.

For **non-production** runs where you want typo-tolerant column names (FN reduction) enabled:

1. Start from **`deploy/config.example.yaml`** (or your existing `config.yaml`).
1. Merge the keys from **`deploy/config.staging.example.yaml`**: `sensitivity_detection.fuzzy_column_match`, optional **`connector_format_id_hint`** (Plan §4: `VARCHAR(N)` + ID-like name → MEDIUM), and optional `detection.persist_low_id_like_for_review`.
1. Install **`rapidfuzz`**:
   - `uv sync --group dev`, or
   - `pip install ".[detection-fuzzy]"` from the repo root.
1. If **false positives** increase, raise **`fuzzy_column_match_min_ratio`** (e.g. `88`–`92`) or set **`fuzzy_column_match: false`**. If **`FORMAT_LENGTH_HINT_ID`** noise appears on generic `*_id` columns, set **`connector_format_id_hint: false`** (no separate ratio knob yet).

Operator context: [Corporate-Entity-C_ANALISE_2026-03-18.md](../docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md) (staging + recommendations mapping).
