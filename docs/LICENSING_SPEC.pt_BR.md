# Especificação de licenciamento (runtime)

**English:** [LICENSING_SPEC.md](LICENSING_SPEC.md)

Especificação técnica do enforcement comercial **opcional**. O padrão é o modo **open** (nenhum token exigido).

## Modos

| Modo       | Config / env                                                                      | Comportamento                                                                                                        |
| ----       | ------------                                                                      | ----------                                                                                                           |
| `open`     | `licensing.mode: open` ou ausente; `DATA_BOAR_LICENSE_MODE=enforced` pode escalar | Funcionalidade completa; token de licença opcional; status mostra **OPEN**                                           |
| `enforced` | `licensing.mode: enforced`                                                        | Token assinado válido é exigido para ingest/digest; estados inválido/expirado/revogado/adulterado bloqueiam os scans |

### Sem bypass por ambiente (#719)

O estado de enforcement é determinado **somente** por `licensing.mode: enforced` mais uma licença assinada válida. Variáveis de ambiente nunca podem desabilitá-lo:

- `DATA_BOAR_LICENSE_MODE=open` é **ignorado** quando o YAML define `mode: enforced`

  (a tentativa é registrada como evento de auditoria CRITICAL). A variável de ambiente só pode
  **escalar** `open` → `enforced`.

- `DATA_BOAR_ENV=development`, `DEBUG=1` e o antigo

  `DATA_BOAR_TIER_OVERRIDE` têm efeito **zero** sobre o licenciamento. O override de tier de dev/CI
  foi removido — use uma licença de QA assinada e emitida localmente
  (`scripts/issue_dev_license_jwt.py`).

- Sem uma licença válida no modo enforced, o runtime **falha fechado** (fail-closed):

  os scans são negados (Safe-Hold / HTTP 403) e o tier de recursos é limitado a
  Community — nunca "open".

Toda decisão de enforcement (allow / deny / clamp / expire) é registrada no
logger `data_boar.licensing.audit` com o prefixo `LICENSE_AUDIT`.

Variáveis de ambiente sobrescrevem o YAML quando definidas:

- `DATA_BOAR_LICENSE_MODE` — `enforced` (somente escalada; `open` não rebaixa o `enforced` do YAML)
- `DATA_BOAR_LICENSE_PATH` — caminho do arquivo JWT (`.lic`)
- `DATA_BOAR_LICENSE_PUBLIC_KEY_PATH` — arquivo PEM com a chave **pública Ed25519** (somente verificação)
- `DATA_BOAR_LICENSE_PUBLIC_KEY_PEM` — PEM inline (alternativa ao caminho; somente dev/CI)
- `DATA_BOAR_LICENSE_REVOCATION_PATH` — arquivo JSON listando IDs de licença revogados
- `DATA_BOAR_RELEASE_MANIFEST_PATH` — manifesto JSON opcional para integridade (ver [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) ([pt-BR](RELEASE_INTEGRITY.pt_BR.md)))
- `DATA_BOAR_EXPECTED_BUILD_DIGEST` — SHA-256 hex opcional; se definido, é comparado ao digest de build embutido

## YAML (`config.yaml`)

```yaml
licensing:
  mode: open                    # open | enforced
  public_key_path: ""           # PEM público Ed25519
  license_path: ""              # arquivo JWT assinado
  revocation_list_path: ""      # lista JSON de revogação opcional
  manifest_path: ""             # manifesto de release opcional
  machine_bind_strict: false    # se true, o mfp do token precisa bater com o fingerprint do host
```

## Payload do JWT de licença (claims)

Assinado com **Ed25519** (JWS `EdDSA`). Claims padrão:

| Claim | Significado           |
| ----- | -------               |
| `sub` | ID da licença (único) |
| `iat` | Issued-at (unix)      |
| `exp` | Expiração (unix)      |

Claims customizados (com namespace para evitar colisões):

| Claim                  | Tipo     | Significado                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                           |
| -----                  | ----     | -------                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |                                                                                                                                                                                                                                                                                                                           |
| `dbcid`                | string   | ID do cliente                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |                                                                                                                                                                                                                                                                                                                           |
| `dbcname`              | string   | Nome de exibição do cliente                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                           |
| `dbenv`                | string   | Ambiente alvo: `production`, `qa`, `uat`, `homologation`, `debug`, `trial`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |                                                                                                                                                                                                                                                                                                                           |
| `dbmfp`                | string \ | array                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Fingerprint(s) de máquina esperado(s). String hex única = um host; **array de strings hex = pacote de deployment** (#718 + #846): o runtime aceita quando o seu próprio fingerprint ∈ pacote. Vazio/ausente = qualquer host. **Claim malformado (tipo errado) falha fechado** (`INVALID`) — nunca degrada para "unbound". |
| `dbtrial`              | bool     | Trial / POC: limita as linhas do relatório e aplica marca-d'água                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |                                                                                                                                                                                                                                                                                                                           |
| `dbmaxrows`            | int      | Máximo de linhas de dados no relatório quando trial (ex.: 15)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |                                                                                                                                                                                                                                                                                                                           |
| `dbissuer`             | string   | ID do operador emissor (ex.: fingerprint de chave SSH ou e-mail)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |                                                                                                                                                                                                                                                                                                                           |
| `dbkid`                | string   | ID da chave de assinatura para rotação                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |                                                                                                                                                                                                                                                                                                                           |
| `dbgrace`              | int      | Fim do período de graça (unix); após `exp`, permanece **GRACE** até este horário                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |                                                                                                                                                                                                                                                                                                                           |
| `dbmax_workers`        | int      | Máximo de workers de scan em paralelo (#551) — na prática, o número de **alvos varridos simultaneamente**. **Somente modo enforced:** o engine limita `scan.max_workers` a `min(scan.max_workers, dbmax_workers)`. Ausente/zero numa licença usável → aplicam-se os padrões do tier (Community **2** / Pro **4** / Enterprise **ilimitado**; ratificado em 2026-06-11, #853). **Pro+** é dirigido por claim: tokens emitidos carregam `dbmax_workers: 8` (o claim vence o padrão do tier). O modo open nunca limita. O clamp é fail-soft e auditado (`workers_clamped`, WARNING). |                                                                                                                                                                                                                                                                                                                           |
| `dbmax_deployments`    | int      | Máximo de **sites de produção licenciados** distintos (fingerprints) para este token (#846). **Enforced na emissão:** o emissor gera o pacote `dbmfp` com no máximo essa quantidade de entradas; o runtime lê o claim em `LicenseContext.max_deployments` (superfície de auditoria/relatório) e valida apenas o **próprio** fingerprint ∈ pacote. **0** pode significar **ilimitado** quando o contrato permite (Enterprise). Padrão Pro = **2** (ratificado pelo operador em 2026-06-11: on-prem + 1 cloud/branch) — ver `DEFAULT_PRO_DEPLOYMENTS` em `core/licensing/guard.py`. |                                                                                                                                                                                                                                                                                                                           |
| `dbdeployment_pack_id` | string   | ID de um **add-on comercial** (ex.: "+5 sites") para trilha de auditoria/refill (#846); exposto em `LicenseContext.deployment_pack_id`. Emissor: `scripts/issue_dev_license_jwt.py --dbmfp-pack <hex,hex,...> [--pack-id ...]`.                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                           |

**Verificação multi-site (fronteira honesta, #718 + #846):** Implementada via opção (1) — **array** de fingerprints permitidos no claim `dbmfp` (pacote de deployment). O runtime valida apenas que o **seu próprio** `compute_machine_fingerprint()` (hostname + `DATA_BOAR_MACHINE_SEED` opcional) está no pacote — a contagem **global** de deployments é enforced na **emissão** (o emissor assina um pacote com no máximo `dbmax_deployments` fingerprints); o runtime não consegue contar outros sites. Alternativas mantidas como referência: (2) registro **online** (custo de privacidade + operação); (3) **múltiplos JWTs** com o mesmo `dbcid`, um fingerprint cada. Ver [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) ([pt-BR](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md)) §Deployments, cópias e sites.

## Estados do ciclo de vida

| Estado             | Significado                                                                     |
| -----              | -------                                                                         |
| `OPEN`             | Enforcement desligado; build de comunidade / dev                                |
| `VALID`            | Assinatura do token OK, não expirado (ou em graça), não revogado, máquina OK    |
| `GRACE`            | Após `exp` mas antes de `dbgrace`                                               |
| `EXPIRED`          | Após a graça                                                                    |
| `REVOKED`          | ID da licença na lista de revogação                                             |
| `UNLICENSED`       | Enforced mas sem token ou token ilegível                                        |
| `INVALID`          | Assinatura ruim ou JWT malformado                                               |
| `MACHINE_MISMATCH` | `dbmfp` definido e não bate com o host                                          |
| `TAMPERED`         | Verificação de integridade de release / manifesto falhou                        |
| `CRACKED`          | Reservado para futuros sinais anti-tamper (ex.: falhas de checagem de bytecode) |

## Fingerprint de máquina

Computado como hex **SHA-256** sobre uma string estável construída a partir de:

- Hostname (curto)
- Opcional: `DATA_BOAR_MACHINE_SEED` (definido no deployment para estabilidade em Docker/VM)

Docker: defina `DATA_BOAR_MACHINE_SEED` com um segredo específico do deployment para que containers da mesma imagem compartilhem um fingerprint licenciado.

## Formato do arquivo de revogação

JSON:

```json
{
  "revoked_license_ids": ["license-uuid-1", "license-uuid-2", "jti-token-id", "k1"]
}
```

**Kill-switch matching (#717):** cada entrada pode nomear um **ID de licença** (claim `sub`), um **ID de token** (claim `jti`) ou um **ID de chave de assinatura** (claim `dbkid`). Qualquer match falha **fechado**: estado `REVOKED`, marca-d'água `REVOKED`, tier efetivo limitado a **Community**, mais um evento de auditoria `license_revoked` dedicado (WARNING) com o campo correspondente (`license_revoked:sub|jti|dbkid`). Revogar um `dbkid` desabilita **todos** os tokens assinados com aquela chave — a alavanca de emergência para uma chave de assinatura comprometida.

**Distribuição:** a lista é lida de `DATA_BOAR_LICENSE_REVOCATION_PATH` (env) ou `licensing.revocation_list_path` (YAML) no momento da avaliação (inicialização / reavaliação) — **sem hot-reload por design**; reinicie o processo (ou o container) para captar uma lista atualizada. Um arquivo local é o padrão amigável a ambientes air-gapped.

## Comportamento de trial / POC

Quando `dbtrial` é true:

- O scan pode rodar (se válido em tudo mais), mas a **geração do relatório** limita os achados a `dbmaxrows` e anexa linhas sintéticas de "teaser" (com marca-d'água).
- Logs e a aba de info do relatório indicam **TRIAL**.

## Regra de bloqueio

Quando o modo é **enforced** e o estado não é `VALID` nem `GRACE` (e não é `OPEN`):

- **CLI**: `start_audit` lança `LicenseBlockedError`; mensagem impressa em stderr.
- **API**: `POST /scan`, `POST /start`, `POST /scan_database` retornam **403** com `detail.license_state`.

Health e About continuam respondendo para que os operadores vejam **por que** o sistema está restrito.

## Extensões futuras (lembrete de planejamento — tiers de parceiro / SKUs de consultoria)

Quando você **mudar ou endurecer** o licenciamento por IP e lucratividade, poderá introduzir **programas comerciais separados** (ex.: **cliente final direto** vs **parceiro / pro / enterprise** — nomes e contratos exatos a definir com a área jurídica). Um objetivo: permitir que **parceiros** usem um direito de uso de **nível parceiro** para atender aos engajamentos dos **clientes deles** sem colapsar no mesmo SKU de um usuário final single-tenant.

**Não implementado hoje.** Direções possíveis (a validar jurídica e produtualmente):

| Ideia                       | Observações                                                                                                                                                       |             |                                                                                                      |
| ----                        | -----                                                                                                                                                             |             |                                                                                                      |
| **Claims JWT customizados** | ex.: `dbprogram` ou `dbtier` (`direct` \                                                                                                                          | `partner` \ | `enterprise`, …) e `dbmax_customers` / `dbconsulting_allowed` opcionais — nomes ilustrativos apenas. |
| **Enforcement**             | `LicenseGuard` e os metadados do relatório leriam os claims e bloqueariam ou marcariam com marca-d'água o uso **não autorizado** de consultoria ou multi-cliente. |             |                                                                                                      |
| **Emissão**                 | O emissor privado ([`FabioLeitao/license-studio`](https://github.com/FabioLeitao/license-studio) — só operador) emite **templates** de token diferentes por SKU; o log de auditoria registra o programa/tier.              |             |                                                                                                      |

Mantenha esta seção em sincronia com [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) ([pt-BR](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md)) ("Tiers futuros de produto" e **IP de marca, narrativa e experiência** — mascote, data soup, dashBOARd, apresentação de relatório/UI, recursos complementares). **Não adicione claims a tokens de produção até que contratos e preços estejam definidos.**

### Extensão futura: pacotes de recursos dirigidos por direito de uso e kill switch

Ainda não implementado. Alvo de planejamento: quando os contratos de tier estiverem congelados, os claims de licença poderão dirigir
quais capacidades opcionais ficam disponíveis em runtime e quais extras de instalador são permitidos.

| Ideia de claim / controle                             | Propósito                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| ---                                                   | ---                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `dbtier` (`standard`, `pro`, `partner`, `enterprise`) | Fonte única de verdade para o tier de direito de uso em runtime, info do relatório e trilha de auditoria. **Implementação (2026-04):** quando `licensing.mode` é **enforced** e o token é **VALID** ou **GRACE**, o caminho de verificação copia este claim para `LicenseContext.dbtier` e `GET /health` → `license.dbtier`; o código do dashboard o mapeia para o tier interno em gates de recurso **opcionais** (ex.: POC de maturidade) ao lado de `licensing.effective_tier` (só de lab) no YAML. **Gate do POC de maturidade:** `docs/plans/completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md` § *Next slice*; regressão: `tests/test_api_assessment_poc.py` (`test_assessment_enforced_jwt_dbtier_*`). |
| `dbmax_workers` (int)                                 | **Implementado (#551/#853)** — limite de **workers de scan em paralelo** (≈ alvos concorrentes). Escada ratificada: Community **2** · Pro **4** · Pro+ **8** (dirigido por claim) · Enterprise **ilimitado** — ver [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) ([pt-BR](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md)).                                                                                                                                                                                                                                                                                                                                                     |
| `dbmax_targets` (int)                                 | Limite opcional de **alvos configurados** por sessão ou envelope de deployment; **0** pode significar ilimitado quando o contrato permite.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `dbfeatures` (lista de strings)                       | Flags de recurso explícitas, independentes dos padrões do tier (ex.: `compressed_scan`, `content_type_cloaking`, futuro `ai_heuristics_plus`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `dbkill` / overlays de revogação                      | Desabilitação de emergência de capacidades vulneráveis/abusadas sem precisar publicar uma atualização completa do app.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `dbextras_profile` (`core`, `plus`, `full`)           | Mapeia o direito de uso para os pacotes de dependência permitidos (`.[nosql]`, `.[datalake]`, etc.) em ambientes controlados.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

## Esboço de política operacional (a refinar no plano + jurídico):

1. **Enterprise**: permite todos os perfis de extras homologados (`full`) e todos os controles opcionais de runtime; **workers/targets**: **ilimitado** no direito de uso (sujeito ao host), salvo se o contrato restringir.
1. **Pro / Partner**: permite um subconjunto curado (por exemplo cloaking/checagens de content-type e heurísticas premium selecionadas), nega pacotes de alto custo por padrão; **workers/targets**: **acima dos limites open-core**, não necessariamente ilimitado; alguns **ingredientes premium** podem ser **exclusivos de Enterprise**.
1. **Open core / community** (sem token pago): quando o enforcement está ativo para um **build** que embute padrões de tier, alinhe com a política de **1–2 workers** e **alvos limitados** — ver [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) ([pt-BR](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md)) §Escala e concorrência.
1. **Standard** (se usado como rótulo): apenas o runtime core, com uma allowlist curta de opções de baixo risco (exemplo: scan de arquivo compactado).
1. **Postura de enforcement**: falha fechado para opções premium não permitidas no modo `enforced`, mas mantém orientação explícita ao operador em logs/docs.

**Nota sobre `uv`/extras:** a instalação automática de dependências precisa ser **opt-in** e auditável (prefira comando explícito do operador ou perfil de instalador), nunca mutação silenciosa de pacotes durante o runtime do scan. Registre as decisões de direito de uso nas superfícies de auditoria quando implementadas.
