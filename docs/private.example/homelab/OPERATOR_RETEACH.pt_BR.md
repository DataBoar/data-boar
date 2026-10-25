# Fatos do operador — preencher uma vez e reutilizar (gitignored — nunca no GitHub)

**English:** [OPERATOR_RETEACH.md](OPERATOR_RETEACH.md)

**Finalidade:** Único lugar para **acrescentar / editar** o que você “reensina”, para o assistente poder **`read_file`** neste caminho **sem `@`** (padrão do repositório). **Não fazer commit** de dados reais — mantenha-os só em **`docs/private/homelab/`**.

**Idioma:** Este **template rastreado** está em **português do Brasil (pt-BR)**; a cópia **privada** pode ser **só pt-BR** ou você pode manter **EN + pt-BR** localmente. Evite **português europeu** (*ficheiro*, *partilhar*, *secção*, *utilizador*, *tem de*, etc.) — ver **`.cursor/rules/docs-pt-br-locale.mdc`** e **`tests/test_docs_pt_br_locale.py`** para arquivos `.md` versionados.

**Ordem de leitura (agente):** `AGENT_LAB_ACCESS.md` → **`OPERATOR_SYSTEM_MAP.md`** → **`LAB_SOFTWARE_INVENTORY.md`** → **`OPERATOR_RETEACH.md`** (este arquivo na árvore **privada**) → `HARDWARE_CATALOG.md` / `WHAT_TO_SHARE_WITH_AGENT.md` conforme necessário.

---

## A. Já está em outros arquivos privados (não repetir, salvo correção)

- Apelidos de hosts, hardware, portas de API, caminhos — ver **`AGENT_LAB_ACCESS.md`**, **`HARDWARE_CATALOG.md`**, **`WHAT_TO_SHARE_WITH_AGENT.md`**.

---

## B. Preencher o que falta (colar sob cada título — cópia privada)

### B1 — Estação principal (hardware exato)

- **MTM / número do produto:** …
- **BIOS / firmware do sistema:** …
- **CPU (modelo exato):** …
- **RAM:** …
- **Disco principal (tamanho + % uso grosseiro):** …

### B2 — Elétrica / climatização (medido ou placa)

- **Contexto (cidade / local):** …
- **Kill-A-Watt** (W) por equipamento ou “TBD”
- **Nobreak** placa **VA / W** (se houver)
- **Ar split / refrigeração** (instalado vs reserva): tabelas com **modelo**, **elétrico**, **gás refrigerante** — **sem** segredos

### B3 — UniFi / LAN (somente interno)

- **WAN → LAN / NAT:** …
- **Site / rótulos do console / versões:** …
- **VLANs / sub-redes:** …
- **Wi‑Fi (SSID → rede) — sem senhas:** …
- **SNMP:** versão, qual host faz *polling* (só o papel)

### B4 — Solar (sem segredos de API aqui)

- **Inversor** marca + modelo
- **Datalogger** modelo
- **Nome do app** (opcional)
- **Portal na nuvem** (padrão de URL OK; **sem** senhas)
- **IP / VLAN do logger**
- **Família de equipamentos** (fabricante)

### B5 — Runner Linux secundário (opcional — “burst”)

- **Modelo / MTM / papel**
- **SO:** ex. Ubuntu LTS + **Docker**
- **Após a primeira sessão na rede:** RAM/SSD/CPU, hostname, faixa de IP, alias **SSH** `Host` → **`OPERATOR_SYSTEM_MAP`** + **`LAB_SOFTWARE_INVENTORY`**

### B6 — Resto do chat que ainda não está em disco

- Apontadores para **`LAB_SECURITY_POSTURE.md`**, **`LAB_SOFTWARE_INVENTORY.md`**, dumps de firewall, etc.

#### Zerando **B1–B6** — próximos passos (operador)

| Bloco  | O que fazer (operador)                            | Onde espelhar (docs privados)                                  |
| -----  | ----------------------                            | ------------------------------                                 |
| **B1** | Confirmar BIOS/MTM nas ferramentas do fabricante  | Esta seção **B1** + opcional **`WHAT_TO_SHARE_WITH_AGENT.md`** |
| **B2** | Placas / medidas opcionais                        | Bullets **B2**                                                 |
| **B3** | UniFi (versões, papel do SNMP)                    | **B3** + **`LAB_SECURITY_POSTURE.md`**                         |
| **B4** | Placa do inversor + nome do app                   | **B4**                                                         |
| **B5** | SO + Docker; **`scripts/homelab-host-report.sh`** | Mapa + inventário + **`HARDWARE_CATALOG`**                     |
| **B6** | Versões de runtime por host                       | **`LAB_SOFTWARE_INVENTORY.md`**, **`LAB_SECURITY_POSTURE.md`** |

---

## C. Último preenchimento (privado)

**Data:** AAAA-MM-DD · **Por:** operador

**Notas:** Texto livre — ainda **sem senhas** nem **chaves de API** neste arquivo.

---

## Automação (sem hostname de lab no repositório)

Para **POST `/scan`** e consultar **`/status`** em qualquer URL base do Data Boar, use **`scripts/poll_dashboard_scan.py`** com **`--base`** ou **`DATA_BOAR_BASE`** — não um script solto em **`.cursor/`** com hostname fixo.
