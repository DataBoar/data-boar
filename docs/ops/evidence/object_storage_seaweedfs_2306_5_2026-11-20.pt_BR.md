# Prova local object storage — SeaweedFS (fatia 2306.5, issue #2312)

**Data:** 2026-11-20. **Desenho:** `docs/desenho/2306.md`. Evidência do que foi executado — **não** conclusão jurídica.

| Campo | Valor |
| ----- | ----- |
| SeaweedFS | `30GB 4.54` |
| Imagem / digest | `chrislusf/seaweedfs:latest` / `sha256:4b42c212543a…` |
| Podman | 5.4.2 · Debian 13 (kernel `7.2.12+deb13-amd64`) |
| Aceitação | 48 passed em `tests/test_object_storage_acceptance.py` |

TLS autoassinado + `SSL_CERT_FILE`; endpoint `https://127.0.0.1:19443`; credenciais só em env `<redacted>`.

**Resultados:** R-3 **PROVADO** (6 listados / 6 varridos; encoding URL; `//` → `dup.txt`); R-5 **PROVADO** (path + `us-east-1`); R-8 **PROVADO** (`Server: SeaweedFS 30GB 4.54`).

**Nota do build:** rodou do branch do épico, não de uma versão publicada. O runtime avisou `INTEGRITY TAMPER DETECTED … runtime self-marked -alpha (development / not CI-validated)`, porque os módulos críticos divergem da âncora validada, o esperado num branch ainda não lançado. A prova cobre o código do conector no branch, não uma versão assinada.

**Não provado:** S3 AWS, R2, MinIO nesta rodada, IAM, SSE-KMS, performance.

Detalhes e comandos: [object_storage_seaweedfs_2306_5_2026-11-20.md](object_storage_seaweedfs_2306_5_2026-11-20.md). Artefatos em `~/.cache/claude-pm/2306.5/`.
