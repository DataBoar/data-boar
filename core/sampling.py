"""
Sampling policy facade (row-cap cascade for SQL targets).

**Slice — desacoplamento core vs conectores**

- **Policy (this package):** hierarchical caps — per-table → per-target ``sample_limit`` →
  ``fnmatch`` patterns on table name → ``file_scan.sample_limit`` (see ``SamplingPolicy``).
  Optional YAML fragments: ``sql_sampling_file`` / ``sql_sampling_files`` (merged in
  ``config.loader`` before normalize).
- **SQL / dialects:** ``WHERE <col> IS NOT NULL``, ``LIMIT`` / ``TOP`` / ``ROWNUM``, and
  future ``TABLESAMPLE`` hooks live in **``connectors.sql_sampling``** (:class:`SamplingManager`)
  so connectors stay thin executors.

``SamplingProvider`` is an alias of :class:`~core.sampling_policy.SamplingPolicy` (same
implementation).
"""

from core.sampling_policy import SamplingPolicy

# Operator-facing alias (same class: hierarchical limits, no SQL generation here).
SamplingProvider = SamplingPolicy

__all__ = ["SamplingPolicy", "SamplingProvider"]
