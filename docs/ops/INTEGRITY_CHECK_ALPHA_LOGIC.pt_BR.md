# Verificação de integridade e lógica alpha (especificação de desenho)

**English:** [INTEGRITY_CHECK_ALPHA_LOGIC.md](INTEGRITY_CHECK_ALPHA_LOGIC.md)

**Hub de navegação de integridade:** [INTEGRITY_HUB.pt_BR.md](INTEGRITY_HUB.pt_BR.md) ([EN](INTEGRITY_HUB.md)) — mapa completo de runtime, release e superfícies ADR.

Este documento é uma **especificação de desenho** para verificação **opcional** de integridade em runtime de artefatos críticos do Data Boar (fontes Python, extensões nativas opcionais e hashes de referência assinados). **Não** garante que todo o comportamento abaixo já esteja implementado no produto principal até existir ADR e código explícito.

## Objetivos

- Detectar modificação inesperada de bits implantados antes de relatórios de alta confiança.
- Falhar com segurança: preferir saída **degradada e claramente rotulada** a claims silenciosos de conformidade.
- Produzir **evidência auditável** (log estruturado) para revisão de segurança.

## Pseudo-especificação

### 1) Hashing na subida

Em subida controlada (feature flag opcional, ex.: `DATA_BOAR_INTEGRITY_CHECK=1`):

1. Enumerar **caminhos críticos** (lista configurável), por exemplo:
   - subconjunto de `core/*.py`, `pro/*.py` e módulos empacotados (ex.: `boar_fast_filter` quando presente).
2. Calcular **SHA-256** por arquivo (ou digest canônico da wheel para extensões).
3. Comparar com um **manifesto known-good** (JSON ou documento assinado) versionado com o release.

O manifesto deve ser **mantido pelo engenheiro de release** e versionado junto ao release.

### 2) Cross-check

- **Match:** operação normal; opcionalmente registrar `integrity_ok` em nível debug.
- **Mismatch:** entrar em **estado tinted** (abaixo).

### 3) Estado tinted (discrepância)

Quando qualquer hash crítico falhar:

- Definir flag em nível de processo (conceitualmente `__IS_TINTED__ = True`; a implementação pode usar singleton de módulo ou export via ambiente).
- Expor **metadados explícitos de versão/build** indicando suspeita de adulteração (texto exato é decisão de produto; não deve personificar release estável).
- Ativar **modo limitado** nos geradores de relatório:
  - limitar tamanho da narrativa exportada (ex.: primeiras N linhas);
  - inserir marca d’água visível de **não confiável** em saídas legíveis por humanos;
  - evitar alegar completude regulatória.

### 4) Auditoria

Anexar registro estruturado a `security_alert.log` (ou destino SIEM):

- timestamp, hostname, versão do Data Boar, lista de caminhos com hash esperado vs observado;
- sem dados brutos do cliente.

## Notas operacionais

- **Performance:** hashear árvores grandes a cada start pode ser caro; restrinja a lista ou agende execução.
- **Extensões:** módulos nativos podem residir em `site-packages`; hasheie o **artefato instalado** resolvido em runtime, não só `pro/*.pyd` na árvore de fontes.
- **Assinatura:** manifestos “known-good” devem ser **assinados** ou distribuídos por canal confiável do operador (fora do escopo deste texto).

## Implementado: Fase E — confiança no manifesto assinado + forense SQLite (#856 / #2168)

`core/integrity_anchor.py` e `core/integrity_signed_manifest.py`
implementam a espinha da detecção Alpha:

1. **Raiz de confiança (#2168):** SHA-256 da allowlist crítica de
   comportamento (spine + `connectors/*.py` + `core/licensing/*.py` + extras
   explícitos — ver `resolve_critical_modules()` em
   `core/integrity_anchor.py` e
   [PLAN_INTEGRITY_HARDENING.md](../plans/PLAN_INTEGRITY_HARDENING.md) § *behaviour-critical criterion*)
   é comparado a um manifesto **assinado no release**, empacotado em
   `core/licensing/integrity_manifest.json`. A assinatura é Ed25519 sobre
   um payload JSON canônico e verifica com a chave pública de licença já
   existente (`core/licensing/license-pub-v1.pem`). `validated` / `expected`
   só quando essa assinatura verifica **e** cada hash da allowlist casa.
   Árvore ausente, sem assinatura, ilegível, com chave errada, hash
   divergente ou downgrade fica `tampered`. Árvores 1.8.0 sem manifesto
   **não** viram `validated` por omissão.
2. **SQLite é forense, não árbitro:** `build_integrity_anchor` guarda
   hashes vistos, `signed_release_label`, `validated_at` e
   `build_digest_matched`. **`build_digest_matched` é um flag de match de
   build-digest, não uma assinatura criptográfica** (#1211): `True` só
   quando `DATA_BOAR_EXPECTED_BUILD_DIGEST` estava definido e casou com o
   digest embutido; env unset → `False`. A linha **sobrevive ao
   `--reset-data`**.
3. **Re-verificação no startup:** todo start (CLI e web, **qualquer** modo
   de licenciamento, incluindo `open`) reavalia o manifesto assinado.
   - **Upgrade assinado legítimo:** arquivos assinados casam com o rótulo
     novo → `validated` (sem comando do operador, sem `-alpha`).
   - **`--reconcile-integrity-anchor --confirm-upgrade-to=<versão-instalada>`**
     registra um evento `reconcile` e reavalia o mesmo manifesto assinado.
     Não pode produzir `validated` sozinho.
4. **TINTED / `-alpha` (E.4):** o estado adulterado força o rótulo
   `-alpha (development / not CI-validated)` na aba Info do report (linhas
   `Build trust` / `Integrity state`), no rodapé do dashboard, em
   `GET /about`, `GET /status`, `/health`, logs de startup (log CRITICAL
   + banner no stderr), e preflight CLI **`--version`** /
   **`--validate-config`** ([#1298](https://github.com/DataBoar/data-boar/issues/1298)).
   A severidade de `enterprise_surface` sobe para
   `elevated` com a razão `integrity_tampered` (alinhado ao ADR-0066).
5. **Clamp de workers em modo open:** `core/engine.py` limita
   `scan.max_workers` a `OPEN_MODE_WORKER_CAP = 2` no modo open. O clamp fica
   dentro da allowlist hasheada — remover o clamp altera `core/engine.py` e
   tinge o build.
6. **Forense (E.5):** `integrity_events` é uma tabela append-only
   (validation / re-verify / reconcile / tamper) preservada em wipes de dados.

### Modelo de ameaça honesto (E.6)

Isto é **evidência de adulteração, não prova de inviolabilidade.** A checagem
prova que os arquivos críticos casam com um manifesto assinado pela chave
pública de licença **já empacotada**. **Não** prova resistência se essa chave
pública empacotada for substituída. SQLite, `RECORD` da wheel e
`--reconcile-integrity-anchor` não são raiz de confiança. Drift de hash na
mesma versão ainda tingido. Mitigações: permissões de arquivo e um manifesto
assinado na TTY a cada release (`scripts/sign-integrity-manifest.py`). O
runtime captura com confiabilidade edições casuais, forks com gates removidos
e drift silencioso de deploy — que é o objetivo da detecção Alpha.

## Relacionados

- [RELEASE_INTEGRITY.pt_BR.md](RELEASE_INTEGRITY.pt_BR.md) ([EN](RELEASE_INTEGRITY.md))
