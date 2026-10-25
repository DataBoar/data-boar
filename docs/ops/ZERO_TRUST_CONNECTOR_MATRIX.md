# Zero trust connector matrix (least privilege baseline)

**Português (Brasil):** [ZERO_TRUST_CONNECTOR_MATRIX.pt_BR.md](ZERO_TRUST_CONNECTOR_MATRIX.pt_BR.md)

Use this matrix to define minimum permissions and guardrails per connector category.

| Connector class | Credential posture | Scope boundary | Data minimization | Audit expectation |
| --- | --- | --- | --- | --- |
| Filesystem | Read-only service account | Approved paths only | Sampling limits configured | Session log + target manifest |
| SQL DB | Read-only DB user, least schema grants | Explicit schema/table allowlist | Column and row limits by policy | Query scope evidence + run metadata |
| NoSQL | Read-only role in selected collections | Collection allowlist | Sample cap and key masking | Connection scope + collection list |
| API/REST | Token with read-only scopes | Endpoint allowlist | Payload sampling and redaction | Request scope + response classification |
| SharePoint/Dataverse | Dedicated app principal with minimal read rights | Site/list/table allowlist | Extract only required fields | Access scope + tenant-aware logs |
| SMB/NFS shares | Read-only mount/user | Share/path allowlist | File-type + size sampling policies | Mount/session trace |
| Cloud object storage | Read-only IAM role/policy | Bucket/prefix allowlist | Object sampling thresholds | Object inventory trace + run ID |

## Mandatory controls for every connector

- Dedicated credentials (no shared super-user accounts).
- Explicit allowlist of targets in each run.
- No secret material in tracked docs.
- Run-level metadata stored for traceability.
- Review cadence for credentials and scope at least quarterly.
