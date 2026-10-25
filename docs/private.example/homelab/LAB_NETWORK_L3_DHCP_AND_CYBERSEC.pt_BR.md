# Lab L3 — gateway padrão DHCP, DNS e CyberSecure (UniFi / LAB-ROUTER-01)

**Finalidade:** Registrar **por que** cada VLAN deve entregar aos clientes o **gateway L3 e o DNS corretos** (do ponto de vista dessa VLAN), como isso se relaciona com **CyberSecure** (DNS encriptado, IPS, honeypots) e **como validar** no posto ou no dispositivo. **Não** coloque a tabela real de subnets no git — copie este arquivo para `docs/private/homelab/` e preencha a tabela de inventário com **os teus** valores RFC1918.

**Relacionado:** [OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.pt_BR.md](OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.pt_BR.md) · [CREDENTIALS_AND_LAB_SECRETS.pt_BR.md](CREDENTIALS_AND_LAB_SECRETS.pt_BR.md) · [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md](../../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md) · [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)

---

## 1. Modelo mental (o que é “certo”)

- Em cada **VLAN**, o **default gateway** dos hosts costuma ser o **IP do LAB-ROUTER-01 nessa subnet** (muitas vezes **`.1`** num `/24`).
- O **DHCP** deve anunciar esse endereço como **roteador padrão** (opção **3**), para os clientes não herdarem gateway de outra VLAN.
- **DNS** (opção **6**) pode ser o **mesmo** IP (LAB-ROUTER-01 como forwarder), **Pi-hole**, **DNS interno** ou upstream — **por política**; o importante é ser **intencional** por VLAN (IoT vs confiável, etc.).
- Uma **convenção** como “terceiro octeto = VLAN ID” ajuda humanos e runbooks; o **roteamento não depende disso** — só importa **subnet ↔ gateway** coerentes.

---

## 2. UniFi — checklist concreto (por rede)

Repetir para **cada** rede/VLAN (ex.: Default, IoT, Oficial, convidados):

1. **Definições → Redes** → selecionar a rede.
1. Confirmar **ID da VLAN** alinhado a switches e SSIDs.
1. Confirmar **gateway / router** da rede = **IP do LAB-ROUTER-01 nessa subnet** (em geral **`.1`**).
1. Em **DHCP**:
   - Intervalo **dentro** da subnet.
   - **Router / gateway padrão** no DHCP = igual ao passo 3.
   - **Servidores DNS** = o que você quer **nessa** VLAN (muitas vezes o LAB-ROUTER-01 `.1`; ajuste se usar outro resolvedor).
1. **Definições → Wi‑Fi** → cada SSID → **rede / VLAN** aponta para a rede **pretendida** (ex.: SSID IoT → rede IoT apenas).

**Depois de mudar:** renovar DHCP num cliente de teste (desligar/ligar Wi‑Fi ou `ipconfig /release` + `/renew` no Windows).

---

## 3. CyberSecure (visão geral — alinha às notas do lab)

Funcionalidades **no controlador** ou **por rede**; rótulos de menu mudam um pouco com versões do UniFi OS.

| Área                            | O que anotar nas notas privadas                                           | Por que importa                                                              |                        |                                                                                                                      |
| ----                            | --------------------------------                                          | ---------------                                                              |                        |                                                                                                                      |
| **DNS encriptado**              | **Predefined** e quais fornecedores (ex.: Quad9, variantes Cloudflare)    | Clientes podem contornar política local se DNS não estiver alinhado ao DHCP. |                        |                                                                                                                      |
| **Prevenção de intrusão (IPS)** | Ligado/desligado; **redes** no âmbito; data de atualização de assinaturas | Superfície de detecção; supressões com **ID + motivo** em outro documento.      |                        |                                                                                                                      |
| **Honeypot**                    | Tabela **Rede                                                             | Subnet                                                                       | Endereço do honeypot** | O IP do honeypot **precisa estar** **dentro** da subnet listada; muitos desenhos usam **`.2`** com gateway **`.1`**. |

**Dica de UI:** com zoom baixo no browser, **0** e **8** no **terceiro octeto** (ex.: `…40…` vs `…48…`) confundem — **aumenta o zoom** ou copia os valores para a tabela privada.

---

## 4. Falhas comuns (quando as “combinações” parecem erradas)

| Sintoma                           | Causa provável                                                                                    |
| -------                           | ---------------                                                                                   |
| Faixa de IP certa, gateway errado | IP estático ou lease antigo; SSID mapeado para rede errada.                                       |
| DNS inesperado                    | DNS manual no cliente; DNS encriptado + DHCP diferente — **definir** comportamento de referência. |
| Honeypot “não faz nada”           | IP fora da subnet; typo `192` vs `182`; linha errada no CyberSecure.                              |

---

## 5. Comandos de verificação (sem segredos)

## Windows (PowerShell):

```powershell
Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null } | Format-List InterfaceAlias,IPv4Address,IPv4DefaultGateway,DnsServer
Test-NetConnection -ComputerName <gateway-ip> -Port 443
```

**Windows** — cache DNS (depuração):

```powershell
Get-DnsClientCache
```

## Linux:

```bash
ip -4 route show default
resolvectl status 2>/dev/null || grep -E '^nameserver' /etc/resolv.conf
ping -c 2 <gateway-ip>
```

**Opcional:** num host que deva resolver o LAB-ROUTER-01 por nome:

```powershell
Resolve-DnsName unifi.local
```

(Exige split DNS ou `hosts` — ver runbook sobre **`unifi.local`** vs IP cru para TLS.)

---

## 6. Tabela de inventário privada (copiar para `docs/private/homelab/` e preencher)

| Nome da rede (UniFi) | VLAN ID | Subnet (CIDR)    | Gateway LAB-ROUTER-01 | DNS DHCP (pretendido)  | Honeypot (se houver) | SSID(s) |
| -------------------- | ------- | -------------    | ----------- | ---------------------- | -------------------- | ------- |
| *ex.: Default*       | *…*     | *10.0.x.0/24* | *.1*        | *.1 ou …*              | *.2*                 | *…*     |
| *ex.: IoT*           | *…*     | *10.0.x.0/24* | *.1*        | *…*                    | *.2*                 | *…*     |

Substitui `x` só na cópia **privada**.

---

## 7. Assistente (Cursor) — capacidades ligadas a este tema

## Hoje (no teu PC, mesma LAN):

- Ler **este runbook** e o inventário privado quando existir em `docs/private/homelab/`.
- Correr scripts **UniFi Network Integration** com `.env`: `scripts/LAB-ROUTER-01-api-smoke-from-env.ps1`, `scripts/LAB-ROUTER-01-api-inventory-from-env.ps1` (opcional `-SaveJson` para `reports/` privado).
- Correr **SNMP** com `LAB_LAB-ROUTER-01_SNMP_*` (ou arquivo `.env` carregado): `scripts/snmp-LAB-ROUTER-01-lab-probe.ps1`, etc.

**Não automático:** o assistente **não** entra no `unifi.ui.com` por ti — **tu** aplicas mudanças na UI; ele ajuda a transformar o resultado em **checklists** e **comandos**.

## Depois de mais preparação (futuro):

- **Syslog** do LAB-ROUTER-01 para **Loki** / logs centralizados → correlacionar eventos de gateway com hosts ([PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)).
- **Wazuh** (opcional) depois do pipeline de logs estável.
- **SSH** ao LAB-ROUTER-01 ou salto Linux com **chave dedicada** — nunca no repositório ([CREDENTIALS_AND_LAB_SECRETS.pt_BR.md](CREDENTIALS_AND_LAB_SECRETS.pt_BR.md)).

---

## 8. Lembrete de uma linha

*DHCP por VLAN: gateway = LAB-ROUTER-01 `.1` nessa subnet; DNS explícito; honeypot dentro da subnet; zoom na UI para validar octetos; tabela privada é fonte da verdade.*
