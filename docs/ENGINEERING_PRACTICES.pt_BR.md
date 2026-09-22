# Práticas de engenharia

**English:** [ENGINEERING_PRACTICES.md](ENGINEERING_PRACTICES.md)

Esta página declara a **doutrina de engenharia** do repositório Data Boar: comportamentos padrão que aplicamos em código, CI e fluxo do operador. **Não** é copy de marketing e **não** substitui os artefatos linkados abaixo — cada princípio aponta para o arquivo ou config que o implementa.

Os quatro princípios também aparecem na página pública [Práticas de engenharia](https://databoar.com.br/praticas-de-engenharia.html) (DataBoar/data-boar-site#89). **Este arquivo é a fonte canônica no repositório**; o site resume os mesmos links para visitantes.

---

## 1. Fail-closed por padrão

Quando uma condição de **segurança ou higiene não pode ser verificada**, a operação **nega** em vez de seguir com confiança parcial ou assumida.

### Disciplina no repositório

- **Gates em arquivos staged e na árvore rastreada** bloqueiam commits que batem com seeds privados do operador ou padrões proibidos de PII antes de entrarem no histórico compartilhado — veja a pilha de guardrails documentada em [SECURITY.pt_BR.md](SECURITY.pt_BR.md) (Filosofia de resposta a incidentes): `scripts/gatekeeper_audit.py`, `tests/test_pii_guard.py`, `.pre-commit-config.yaml` e `scripts/pii_history_guard.py`.
- **Gate local antes do push:** contribuidores rodam `./scripts/check-all.sh` / `.\scripts\check-all.ps1` (espelho em camadas do CI de qualidade e segurança) para que checagens falhas ou não verificáveis parem a mudança **localmente**, em vez de depois de uma rodada remota de CI — ritual em [QUALITY_WORKFLOW_RECOMMENDATIONS.pt_BR.md](QUALITY_WORKFLOW_RECOMMENDATIONS.pt_BR.md) e política de merge no [SECURITY.pt_BR.md](../SECURITY.pt_BR.md) raiz (fechamento de dependências: gate completo antes do merge).
- **Postura em runtime (produto):** chave de API opcional com `api.require_api_key`; validação estrita de `session_id`; export de log bloqueado quando a auto-varredura de PII falha (HTTP 422) — mesmas tabelas em [SECURITY.pt_BR.md](SECURITY.pt_BR.md). Licenciamento enforced marca instalações modificadas como **TAMPERED** quando digest ou manifesto divergem ([RELEASE_INTEGRITY.pt_BR.md](RELEASE_INTEGRITY.pt_BR.md), [ADR-0066](adr/ADR-0066-fail-closed-runtime-trust-tamper-posture.md)).

**Mapa de postura:** [SECURITY_GOVERNANCE_POSTURE_HUB.pt_BR.md](SECURITY_GOVERNANCE_POSTURE_HUB.pt_BR.md) ([EN](SECURITY_GOVERNANCE_POSTURE_HUB.md)).

---

## 2. Pin + cooldown

**Entradas da cadeia de suprimentos ficam fixadas em versões ou digests exatos**, e **releases novas upstream aguardam quarentena** antes de o Dependabot abrir um PR de atualização.

### Onde vive

- **Python:** `uv.lock` é o pin canônico (resolvido a partir de `pyproject.toml`); Dependabot `package-ecosystem: uv` mantém lock e manifesto alinhados — veja comentários no topo de [`.github/dependabot.yml`](../.github/dependabot.yml) e [ADR-0044](adr/ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md).
- **GitHub Actions:** passos de workflow referenciam **SHAs de commit**; ecossistema Dependabot `github-actions` atualiza esses pins em agenda.
- **Base de container:** digests de imagem no Dockerfile são mantidos via ecossistema Dependabot `docker` ([ADR-0074](adr/ADR-0074-supply-chain-layer1-digest-pins-and-rust-sca.md)).
- **Rust (`boar_fast_filter`):** Dependabot `cargo` em `rust/boar_fast_filter` com o mesmo cooldown e **merge manual apenas** ([#1763](https://github.com/DataBoar/data-boar/issues/1763); incidente arrayref documentado em `dependabot.yml`).
- **Cooldown:** os quatro ecossistemas acima definem **`cooldown: default-days: 7`** em [`.github/dependabot.yml`](../.github/dependabot.yml) — janela de quarentena de sete dias antes de propor uma versão recém-publicada.

**Evidência mais ampla de supply chain:** geração de SBOM e pilha de gates do CI — [ADR-0005](adr/ADR-0005-ci-quality-gates-and-supply-chain-scanning.md), [RELEASE_INTEGRITY.pt_BR.md](RELEASE_INTEGRITY.pt_BR.md) (seção SBOM).

---

## 3. Integridade verificada, não assumida

**Artefatos são checados por hash ou manifesto antes de confiar** — no deploy (guard de licenciamento em runtime) e na engenharia de release (reprodutibilidade de build).

### Mecanismos

- **Digest de build embutido:** SHA-256 determinístico sobre arquivos fonte críticos ordenados; divergência com `licensing.mode: enforced` → **TAMPERED**. Gerador: [`scripts/generate_build_digest.py`](../scripts/generate_build_digest.py). Env do operador: `DATA_BOAR_EXPECTED_BUILD_DIGEST`.
- **Manifesto de arquivos assinado (opcional):** JSON SHA-256 por caminho via [`scripts/generate_release_manifest.py`](../scripts/generate_release_manifest.py); verificado na inicialização quando configurado (`DATA_BOAR_RELEASE_MANIFEST_PATH` / `licensing.manifest_path`).
- **Anexos de release:** `build-digest.txt` e `release-manifest.json` no GitHub Releases; artefatos CycloneDX SBOM pelo workflow SBOM.

Especificação completa: **[RELEASE_INTEGRITY.pt_BR.md](RELEASE_INTEGRITY.pt_BR.md)** ([EN](RELEASE_INTEGRITY.md)). Hub de navegação: [ops/INTEGRITY_HUB.pt_BR.md](ops/INTEGRITY_HUB.pt_BR.md) ([EN](ops/INTEGRITY_HUB.md)).

---

## 4. Metadado primeiro

**A descoberta reporta o quê, onde e o formato — não exfiltração em massa de conteúdo bruto** — salvo quando o operador configura explicitamente amostragem limitada para detecção.

### Definição

O termo de glossário **Data Sniffing** nomeia a passada de descoberta e amostragem do motor: conectores descobrem estrutura, leem trechos **limitados** e rodam detecção de sensibilidade — **achados só de metadado, sem exfiltração** ([GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md), linha *Data Sniffing*).

### Alinhamento do produto

- Achados e relatórios são evidência **orientada a inventário** para fluxos de CISO/DPO — não conclusões jurídicas ([COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md), [ADR-0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)).
- Dicas de jurisdição e amostras de conformidade seguem o mesmo limite **só metadado, heurístico** ([ADR-0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md)).
- Resumo filosófico: [philosophy/THE_WHY.pt_BR.md](philosophy/THE_WHY.pt_BR.md) ([EN](philosophy/THE_WHY.md)).

---

## Documentação relacionada

- [README.pt_BR.md](README.pt_BR.md) ([EN](README.md)) — índice de documentação.
- [MAP.pt_BR.md](MAP.pt_BR.md) ([EN](MAP.md)) — navegação por preocupação.
- [SECURITY.pt_BR.md](SECURITY.pt_BR.md) ([EN](SECURITY.md)) — correções de segurança, testes e orientação ao técnico.
- [SECURITY_GOVERNANCE_POSTURE_HUB.pt_BR.md](SECURITY_GOVERNANCE_POSTURE_HUB.pt_BR.md) ([EN](SECURITY_GOVERNANCE_POSTURE_HUB.md)) — mapa de entradas de segurança, governança e proveniência.
