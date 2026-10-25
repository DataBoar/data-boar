# Credenciais e segredos do lab — entrega segura (sem colar no chat)

**English:** [CREDENTIALS_AND_LAB_SECRETS.md](CREDENTIALS_AND_LAB_SECRETS.md)

**Objetivo:** Usar SNMP, API keys e senhas do LAB-OP (ex.: UniFi LAB-ROUTER-01-SE) **sem** colar segredos no chat do Cursor nem em arquivos **rastreados** no Git.

---

## Regras

1. **Nunca** colar senhas, community strings, tokens ou chaves privadas **no diálogo**.
1. **Nunca** commitar segredos em **`main`** — nem em `.mdc`, `AGENTS.md`, skills nem `docs/` públicos.
1. **OK** guardar cópias só do operador em **`docs/private/`** (gitignored), ciente do risco em disco (backup, encriptação, pCloud).

---

## Ordem recomendada

| Método                                                                         | Quando                                                                                                                                                                                                                                                     |
| ------                                                                         | ------                                                                                                                                                                                                                                                     |
| **Bitwarden CLI (`bw`)**                                                       | Já referido no `homelab-host-report.sh`; bom para obter segredo na hora do script.                                                                                                                                                                         |
| **Cofre do SO** (Windows Credential Manager, etc.)                             | Jobs interativos ou agendados numa máquina.                                                                                                                                                                                                                |
| **Variáveis de ambiente só na sessão**                                         | Definir **`$env:VAR`** no **terminal integrado** **antes** de pedir ao agente para correr um script; o mesmo terminal executa o comando. **Não** contar só com “a IA limpa a variável” — **fechar o terminal** ou terminar a sessão quando não precisares. |
| **Arquivo gitignored** **`docs/private/homelab/.env.snmp.local`** (nome exato) | Copie de **`docs/private.example/homelab/env.snmp.local.example`**; um arquivo por máquina; nunca commit.                                                                                                                                                  |

---

## Variáveis de ambiente (exemplo SNMP / UniFi)

Só **nomes** nos docs rastreados; **valores** vêm da tua cabeça ou do vault.

Exemplos sugeridos: `LAB_LAB-ROUTER-01_SNMP_HOST`, `LAB_LAB-ROUTER-01_SNMP_V3_USER`, `LAB_LAB-ROUTER-01_SNMP_AUTH_PASS`, `LAB_LAB-ROUTER-01_SNMP_PRIV_PASS`. Preferir **SNMPv3** (ver [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](../../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md)).

**Passos concretos (PowerShell, arquivo `.env` gitignored, `snmp-LAB-ROUTER-01-lab-probe.ps1`):** ver seção **“SNMPv3 + snmp-LAB-ROUTER-01-lab-probe.ps1”** e **“SNMP on Windows (PowerShell + WSL)”** no EN [CREDENTIALS_AND_LAB_SECRETS.md](CREDENTIALS_AND_LAB_SECRETS.md). **`apt-get` é dentro do WSL/Linux**, não no PowerShell; no Windows instala-se o pacote `snmp` **na distro WSL**. A IA **não** lê variáveis do teu PC; **não** colar segredos no chat.

### Importante: variáveis na sessão **não** criam o arquivo

Quando você faz `$env:LAB_LAB-ROUTER-01_SNMP_HOST = "..."` no PowerShell, isso vale **só naquela janela**. **Nenhum** `.env.snmp.local` é gravado automaticamente. Para o Agendador de Tarefas e para `snmp-LAB-ROUTER-01-lab-probe-to-log.ps1`, você precisa **criar** o arquivo em **`docs/private/homelab/.env.snmp.local`** (copiando o modelo).

### Como deve ser o conteúdo (SNMPv3)

Modelo rastreado com valores **sintéticos** (substitua pelos reais): **[env.snmp.local.example](env.snmp.local.example)**

Resumo do formato (sem espaços em volta do `=`):

```text
LAB_LAB-ROUTER-01_SNMP_HOST=<IP do gateway/LAB-ROUTER-01 na LAN>
LAB_LAB-ROUTER-01_SNMP_V3_USER=<usuário SNMPv3>
LAB_LAB-ROUTER-01_SNMP_AUTH_PASS=<senha de autenticação SHA>
LAB_LAB-ROUTER-01_SNMP_PRIV_PASS=<senha de privacidade AES>
```

Os quatro nomes (`LAB_LAB-ROUTER-01_SNMP_*`) têm que ser **exatamente** esses — são os que os scripts leem. O equipamento (UniFi etc.) tem que estar com SNMPv3 configurado com o **mesmo** usuário e par de senhas.

---

## Métricas de rede

1. **Agora:** `snmpwalk` / contadores de interface a partir de um host na LAN (script em `scripts/` lê `env`).
1. **Depois:** Prometheus SNMP exporter + Grafana, ou UI UniFi — opcional.

---

**Vários equipamentos SNMP (switch, etc.):** [SNMP_LAB_TARGETS.pt_BR.md](SNMP_LAB_TARGETS.pt_BR.md) — arquivos `.env` por alvo, Linux `snmp-lab-ifwalk.sh`, SNMPv2c manual.

**Relacionado:** [PRIVATE_OPERATOR_NOTES.md](../../PRIVATE_OPERATOR_NOTES.md) · [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](../../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md).
