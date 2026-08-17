# Credenciais do operador: camada env + vault no tempo (pt-BR)

**English:** [OPERATOR_CREDENTIALS_FROM_ENV.md](OPERATOR_CREDENTIALS_FROM_ENV.md)

**Objetivo:** Documentar o jeito **estável** de passar senhas, PATs e tokens para o Data Boar — e como isso permanece **compatível** com Bitwarden hoje e com **Fase B** / vaults corporativos depois.

**Não** substitui [OPERATOR_SECRETS_BITWARDEN.pt_BR.md](OPERATOR_SECRETS_BITWARDEN.pt_BR.md) (hábitos do vault humano) nem [PLAN_SECRETS_VAULT.md](../plans/PLAN_SECRETS_VAULT.md) (backlog `@vault:` no app).

---

## 1. Camadas (o que é estável vs o que evolui)

| Camada | Papel | Status |
| ------ | ----- | ------ |
| **A — YAML rastreado** | Só nomes: `pass_from_env`, `token_from_env`, `api_key_from_env`, … | **Contrato de produto estável** (Fase A entregue) |
| **B — Ambiente do processo** | **Valores** secretos presentes quando o `main.py` sobe | **Estável**; o que os conectores leem de fato |
| **C — Ponte opcional em disco** | `~/.config/databoar/*.env` (`chmod 0600`) + `scripts/databoar-env-load.*` | **Conveniência**; dispensável se você injeta env de outro jeito |
| **D — Vault do operador** | Bitwarden (CLI/`bw`), vaults de empresa no futuro | **Fonte humana / enterprise** → injeta em **B** |
| **E — Refs in-app / vault externo** | `@vault:…`, HashiCorp / KMS em nuvem (plano Fase B+) | **Backlog**; resolve em memória/env no load |

**Regra:** Não inventar um segundo canal de segredo no YAML que contorne **A→B**. Novos produtos de vault devem **preencher variáveis de ambiente** (ou a resolução `@vault:` já planejada no loader) com os **mesmos nomes** apontados pelos `*_from_env`.

```text
  Bitwarden / HCP Vault / Secret K8s / systemd EnvironmentFile
                         │
                         ▼
              ambiente do SO (camada B)
                         │
                         ▼
         config *_from_env  →  conector / API
```

Arquivos em disco ficam **ao lado** desse caminho como ponte local — não como a história “única” para empresas que já operam vault.

---

## 2. Menor privilégio (toda credencial)

Qualquer origem (PAT, senha de DB, conta de share):

1. **Somente leitura** quando o conector só amostra (HubSpot Private App: os seis escopos **read** em [ADDING_CONNECTORS.pt_BR.md](../ADDING_CONNECTORS.pt_BR.md) §7 — sem write, sem webhooks).
2. **Grants estreitos** em SQL (SELECT só nos schemas necessários).
3. **Share / FS:** ACL mínima de pasta para a identidade do scan.
4. **Um segredo por sistema** no item do vault (e de preferência um arquivo `*.env` por sistema em `~/.config/databoar/`) para a rotação não forçar reescrita de alvos não relacionados.

---

## 3. Layouts recomendados

### 3.1 Empresas / vault primeiro (preferido quando disponível)

1. Guarde o segredo no Bitwarden (ou vault corporativo).
2. No início da sessão, injete no env — exemplos:

```bash
export BW_SESSION="$(bw unlock --raw)"
export HUBSPOT_PRIVATE_APP_TOKEN="$(bw get password 'Data Boar — HubSpot Private App')"
uv run python main.py --config /caminho/para/config.yaml
```

```powershell
$env:BW_SESSION = (bw unlock --raw)
$env:HUBSPOT_PRIVATE_APP_TOKEN = (bw get password "Data Boar — HubSpot Private App")
uv run python main.py --config C:\caminho\para\config.yaml
```

3. O YAML só nomeia a variável (`token_from_env` / padrão `HUBSPOT_PRIVATE_APP_TOKEN`).

O mesmo padrão vale para **`EnvironmentFile=` do systemd**, **secrets Docker/K8s → env**, ou agente de vault corporativo que escreve env antes do start.

### 3.1b Docker / Podman — mesmos arquivos `KEY=value` (degrau 2 → 3)

Prefira **injeção pelo orquestrador** (degrau **3**): Secret Compose/K8s → environment, ou `podman run -e VAR=…`. Se você já tem um arquivo `KEY=value` no host (degrau **2**), passe-o **sem** `source` dentro da imagem:

```bash
podman run --rm \
  --env-file "${HOME}/.config/databoar/hubspot.env" \
  -e CONFIG_PATH=/data/config.yaml \
  -v "${PWD}/data:/data:Z" \
  fabioleitao/data_boar:lab
```

Compose (**não** versionar valores reais):

```yaml
services:
  data-boar:
    env_file:
      - ./secrets/hubspot.env   # gitignored KEY=value
```

Padrão da chave de API do painel: [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md) §6. Follow-up: issue **#1611**.

### 3.2 Solo / lab — arquivos env XDG (ponte opcional)

```text
~/.config/databoar/          # mkdir; chmod 700
  hubspot.env                # chmod 0600 — HUBSPOT_PRIVATE_APP_TOKEN=…
  postgres-lab.env           # DEMO_DB_PASSWORD=…
  agent-sessions.env         # opcional; usado por primary-linux-agent-sessions.sh
```

```bash
mkdir -p ~/.config/databoar && chmod 700 ~/.config/databoar
. ./scripts/databoar-env-load.sh hubspot   # ou omita o nome para carregar todos *.env
uv run python main.py --validate-config --config /caminho/para/config.yaml
uv run python main.py --config /caminho/para/config.yaml
```

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\databoar"
. .\scripts\databoar-env-load.ps1 -Name hubspot
uv run python main.py --config C:\caminho\para\config.yaml
```

Sobrescrever diretório: **`DATA_BOAR_ENV_DIR`**.

**Não** faça commit desses arquivos. Prefira migrar segredos de alto valor para o Bitwarden e tratar `*.env` como cache descartável depois que a injeção via vault funcionar.

### 3.3 Nada em disco (possível, mais toil)

`export` / `$env:` só na vida do shell, ou colar da UI do vault uma vez por sessão. Mesmo contrato **A→B**; mais digitação, menos resíduo em filesystem.

---

## 4. HubSpot (exemplo)

| Item | Valor |
| ---- | ----- |
| YAML | `type: hubspot` (`token_from_env` opcional) |
| Nome de env padrão | `HUBSPOT_PRIVATE_APP_TOKEN` |
| Arquivo XDG (opcional) | `~/.config/databoar/hubspot.env` |
| Item no vault (opcional) | mesmo nome de env como campo custom / senha |

Escopos e Forms vs CRM: [ADDING_CONNECTORS.pt_BR.md](../ADDING_CONNECTORS.pt_BR.md) §7.

---

## 5. Alinhamento com o roadmap

| Trilha | O que entra |
| ------ | ----------- |
| **Fase A (feita)** | `*_from_env` + redação GET `/config` — [PLAN_SECRETS_VAULT.md](../plans/PLAN_SECRETS_VAULT.md) |
| **Este doc + loaders** | **B** documentado + **C** opcional; texto vault-forward |
| **Caminho Bitwarden** | [OPERATOR_SECRETS_BITWARDEN.pt_BR.md](OPERATOR_SECRETS_BITWARDEN.pt_BR.md) — injeta em **B** |
| **Fase B (backlog)** | Store local criptografado / `@vault:` / vault externo — ainda **nomes no YAML**, valores fora do Git |

Quando a Fase B chegar, configs com `*_from_env` continuam válidas; refs de vault viram caminho extra de resolução, não um rename quebrando vars HubSpot/SQL.

---

## Ver também

- [USAGE.pt_BR.md](../USAGE.pt_BR.md) — credenciais a partir do ambiente
- [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md) — chave da API do painel (EN)
- [SECURITY.md](../../SECURITY.md) — arquivo de config e segredos
- [TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md) — `databoar-env-load.*`
