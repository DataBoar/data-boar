# Alvos SNMP no lab — quando vale a pena, arquivos `.env` e comandos (Linux)

**English:** [SNMP_LAB_TARGETS.md](SNMP_LAB_TARGETS.md)

**Objetivo:** Decidir se vale adicionar **mais equipamentos** além do gateway (LAB-ROUTER-01/roteador), como **switches gerenciáveis**, **NAS** ou **firewall**, e como manter **credenciais separadas** por arquivo em `docs/private/homelab/` (gitignored).

---

## Vale a pena?

| Situação                                                                                     | Vale?                                                                                                     |
| --------                                                                                     | -----                                                                                                     |
| Durante **testes** de carga/scan e se quiser ver **tráfego por interface** no core vs no switch | Sim — poll **periódico** leve (IF-MIB) ou logs agendados.                                                 |
| **Produção** com alertas, retenção longa, gráficos                                           | Melhor **Prometheus + snmp_exporter** / Zabbix / UniFi UI — este repo só dá **probes manuais/agendados**. |
| Equipamento só com **SNMPv2c** (community)                                                   | O script atual é **v3 SHA/AES**; para v2c use **`snmpwalk` manual** (comandos abaixo).                    |

---

## Padrão de arquivos (vários equipamentos)

Use **um arquivo por alvo**, **mesmas quatro chaves** (`LAB_LAB-ROUTER-01_SNMP_*` — nome histórico; serve para **qualquer** alvo v3):

| Arquivo (exemplo)        | Equipamento                                                                         |
| -----------------        | -----------                                                                         |
| `.env.snmp.local`        | Gateway / LAB-ROUTER-01 (padrão dos scripts Windows)                                          |
| `.env.snmp.LAB-ROUTER-01-se.local` | **LAB-ROUTER-01 SE** (ou outro gateway com arquivo `.env` dedicado — mesmo formato de chaves) |
| `.env.snmp.switch.local` | Switch gerenciado                                                                   |
| `.env.snmp.nas.local`    | NAS (se expuser SNMPv3 e OID compatível)                                            |

## PowerShell (Windows + WSL):

```powershell
.\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1 -EnvFile docs\private\homelab\.env.snmp.switch.local -WslDistro Debian
.\scripts\snmp-LAB-ROUTER-01-lab-probe-to-log.ps1 -EnvFile docs\private\homelab\.env.snmp.switch.local -WslDistro Debian -MaxLines 200
```

Modelo sintético do switch: **`env.snmp.switch.local.example`**.

**Agendador (Task Scheduler):** nos **Argumentos** do `powershell.exe`, inclui **`-EnvFile "docs\private\homelab\.env.snmp.LAB-ROUTER-01-se.local"`** (caminho completo ou relativo à raiz do clone, conforme já usas no teste manual) quando não fores usar o default `.env.snmp.local`.

### Observabilidade no lab (futuro)

Os probes deste repo são **pontuais** (CLI + log gitignored). Para **retenção, alertas e dashboards**, faz sentido evoluir para um stack no lab, por exemplo:

- **Prometheus** + **snmp_exporter** (métricas SNMP com labels e consultas PromQL);
- **Zabbix** (templates SNMP, triggers, mapas);
- **Uptime Colleague-Ma** (HTTP/TCP/ping; SNMP é limitado mas útil para disponibilidade simples);
- **Netdata** (visão rápida por host; integrações variam).
- **Wazuh** (SIEM/XDR no lab — **vulns**, hardening, relatórios centralizados; **depois** da stack mínima lab-op — ver [LAB_OP_MINIMAL_CONTAINER_STACK.md](../../ops/LAB_OP_MINIMAL_CONTAINER_STACK.pt_BR.md) §6).
- **Sequência completa de observabilidade** (Grafana, Prometheus ou InfluxDB, Loki ou Graylog+OpenSearch): [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md).

Nada disso substitui o `.env` gitignored aqui — o NMS passa a ser a **fonte operacional**; este repositório continua útil para **debug** e **documentação** de OIDs/comandos.

---

## Linux (lab-op, <lab-host-2>, SBC, etc.)

**Pré-requisito:** `sudo apt install -y snmp` (ou equivalente na distro).

**Script do repositório** (a partir da raiz do clone):

```bash
bash scripts/snmp-lab-ifwalk.sh docs/private/homelab/.env.snmp.local
bash scripts/snmp-lab-ifwalk.sh docs/private/homelab/.env.snmp.switch.local
```

**Comando completo manual** (valores **sintéticos** — substitua pelos reais; não cole segredos em issues públicos):

```bash
export LAB_LAB-ROUTER-01_SNMP_HOST=192.0.2.10
export LAB_LAB-ROUTER-01_SNMP_V3_USER=synth_oper
export LAB_LAB-ROUTER-01_SNMP_AUTH_PASS=Syn_Auth_7kQm9pL2vN4wR8xT1
export LAB_LAB-ROUTER-01_SNMP_PRIV_PASS=Syn_Priv_3mK8nQ5wZ2cV6hJ0

snmpwalk -v3 -l authPriv -u "$LAB_LAB-ROUTER-01_SNMP_V3_USER" \
  -a SHA -A "$LAB_LAB-ROUTER-01_SNMP_AUTH_PASS" \
  -x AES -X "$LAB_LAB-ROUTER-01_SNMP_PRIV_PASS" \
  "$LAB_LAB-ROUTER-01_SNMP_HOST" \
  1.3.6.1.2.1.2.2
```

**SNMPv2c** (só se o equipamento **não** tiver v3 e aceitar community — trate `COMMUNITY` como senha):

```bash
snmpwalk -v2c -c "SYN_COMMUNITY_STR" 192.0.2.20 1.3.6.1.2.1.2.2
```

**Firewall:** permitir **UDP 161** do host que faz *poll* para o IP de **gestão** do equipamento — não exponha SNMP à Internet.

---

## Equipamentos comuns (referência rápida)

| Tipo                                 | SNMP típico                     | Notas                                                          |
| ----                                 | -----------                     | -----                                                          |
| **UniFi Dream Machine / gateway**    | v3 recomendado                  | Já coberto por `snmp-LAB-ROUTER-01-lab-probe.ps1`.                       |
| **Switch gerenciável** (UniFi, etc.) | v2c ou v3 conforme firmware     | Mesmo OID IF-MIB para contadores de interface.                 |
| **pfSense / OPNsense**               | v2c/v3 configurável             | OIDs diferentes para algumas métricas; IF-MIB costuma existir. |
| **NAS (Synology, etc.)**             | muitas vezes v2c ou MIB própria | Ver documentação do fabricante.                                |
| **UPS (APC Network)**                | v1/v2c comum                    | OIDs específicos; fora do escopo do script atual.              |

---

## CI (GitHub Actions) e “dados ao vivo”

**Runners hospedados na nuvem** (os padrão do GitHub) **não têm rota IP** para a tua LAN nem para o IP de gestão do LAB-ROUTER-01/firewall. **SNMP (UDP 161)** daí para o equipamento **não funciona** — não faz sentido adicionar ao `.github/workflows/` um job que chame `snmp-LAB-ROUTER-01-lab-probe` como fazemos no PC.

| Abordagem                                                                                                      | Viável?                                                                                                                                                          |
| ---------                                                                                                      | -------                                                                                                                                                          |
| **Task Scheduler no teu Windows** (como combinaste, ex. a cada **30 min**)                                     | Sim — recomendado para “olhar o log” localmente.                                                                                                                 |
| **Self-hosted runner** numa máquina **dentro** da mesma rede que o firewall                                    | Tecnicamente possível, mas aumenta superfície (runner exposto à internet de outra forma), credenciais no GitHub, e manutenção — só se houver política explícita. |
| **Prometheus + snmp_exporter** / NMS no lab                                                                    | Melhor para métricas contínuas e dashboards.                                                                                                                     |
| **Upload de artefato** a partir do teu PC (script manual que faz `gh run upload` ou cópia para bucket privado) | Possível como extensão operacional, **fora** do fluxo de CI público do repo.                                                                                     |

**Conclusão:** não incluímos no CI padrão deste repositório a execução automática do probe SNMP contra o teu lab. A visão “situação geral” fica no **log gitignored** + Agendador; quando precisares de evidência numa PR, usa **trechos redigidos** ou métricas agregadas sem MAC/IP.

---

## Privacidade

Logs e saída de `snmpwalk` podem incluir **MACs**, nomes de VLAN/interface e **contadores** — mantenha em `docs/private/`, sem commit.

**Relacionado:** [CREDENTIALS_AND_LAB_SECRETS.pt_BR.md](CREDENTIALS_AND_LAB_SECRETS.pt_BR.md) · [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](../../ops/HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md) · [reports/README.md](reports/README.md)
