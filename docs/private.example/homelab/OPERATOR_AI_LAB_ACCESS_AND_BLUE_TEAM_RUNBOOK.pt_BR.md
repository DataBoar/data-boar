# Runbook do operador — acesso ao assistente (IA), racional de segurança e próximos passos blue team

**Copie para `docs/private/homelab/`** e preencha detalhes por host. **Nunca** faça commit de IPs reais, chaves ou tokens. Este arquivo serve para **não esquecer o porquê** das decisões e **o que** habilitar a seguir — não substitui controlo de mudanças formal.

**Relacionado:** [CREDENTIALS_AND_LAB_SECRETS.pt_BR.md](CREDENTIALS_AND_LAB_SECRETS.pt_BR.md) · [LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md](LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md) · [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md](OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md) · [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)

---

## 1. Para que serve este runbook

Configurações de homelab e UniFi acumulam-se rápido. Sem notas, é fácil esquecer a **intenção** (por que uma regra ou supressão existe) e sub-investir em **evidência** (logs, alertas, revisões). Este documento junta:

- **Segurança operacional** (o que rever e com que frequência).
- **Acesso ao assistente (Cursor)** (o que ele pode usar *a partir do teu PC* — nunca uma identidade cloud separada).
- **Maturidade blue team** (visibilidade, detecção, resposta), de forma incremental e realista para lab.

---

## 2. Decisões para não “limpar” sem relembrar o motivo

Regista **valores reais** só na cópia em `docs/private/homelab/`.

| Tema                              | Intenção típica                                                                                                                  | Antes de alterar                                                                                                                                                                                    |
| ----                              | -----------------                                                                                                                | ----------------                                                                                                                                                                                    |
| **TLS / `unifi.local` vs IP**     | O SAN do certificado bate com **hostname**; **HTTPS pelo IP** quebra validação (`WRONG_PRINCIPAL`).                              | Manter **`hosts`** / DNS; URL base da API = `<https://unifi.loca>l` no `.env`.                                                                                                                      |
| **Chaves API (Integrations)**     | **Owner** muitas vezes precisa de **criar/revogar** chaves; contas de automação podem **usar** chaves sem ver a UI Integrations. | Rodar após paste/vazamento; nomear chaves por função + data.                                                                                                                                        |
| **Supressão IPS (ex.: SSH scan)** | Reduzir **falsos positivos** ou ruído de comportamento conhecido do lab.                                                         | Documentar **ID da assinatura + motivo + data**; rever anualmente.                                                                                                                                  |
| **Nomes de políticas de filtro**  | Nomes como “Off” com filtros ativos confundem o teu “eu futuro”.                                                                 | Renomear para refletir a realidade (ex.: `Trusted-filtered`).                                                                                                                                       |
| **Typos em honeypot / subnet**    | Prefixo errado (ex.: `182.x` vs `192.x`) quebra cobertura.                                                                       | Confirmar que o IP do honeypot está **dentro** da VLAN pretendida; com zoom baixo na UI, **0** e **8** num octeto confundem — validar na tabela privada.                                            |
| **DHCP gateway + DNS por VLAN**   | Os clientes devem receber o **LAB-ROUTER-01 `.1` (ou GW escolhido)** **dessa** subnet, não o gateway de outra VLAN.                        | UniFi **Redes → DHCP** + **Wi‑Fi → VLAN correta**; preencher tabela privada em [LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md](LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md); renovar lease após mudanças. |
| **Double NAT no WAN**             | CPE da operadora à frente do LAB-ROUTER-01; aceitável mas afeta **port forward**, **VPN**, alguns jogos.                                   | Documentar “double NAT aceite” ou planejar bridge/IP público.                                                                                                                                        |
| **Isolamento IoT + exceções**     | **Negar** por padrão IoT → interno; **permitir** só caminhos documentados.                                                      | Rever após qualquer mudança de VLAN ou dispositivo IoT.                                                                                                                                             |

---

## 3. O que dar ao assistente mais tarde (autonomia segura *na tua máquina*)

O assistente **não** tem conta Ubiquiti. Corre **só** no Cursor no **teu** equipamento, com **o teu** shell e arquivos.

| Capacidade                     | Como                                                                                                                              | Segredos                                                 |
| ----------                     | ----                                                                                                                              | --------                                                 |
| **API Network Integration**    | `.env` em `docs/private/homelab/` (ex.: `.env.api.LAB-ROUTER-01-se.local`), `LAB_LAB-ROUTER-01_API_BASE_URL=<https://unifi.loca>l`, TLS de confiança. | Chave API **nunca** no git; rodar se exposta.            |
| **Scripts smoke / inventário** | `scripts/LAB-ROUTER-01-api-smoke-from-env.ps1`, `scripts/LAB-ROUTER-01-api-inventory-from-env.ps1` (opcional `-SaveJson` para `reports/` privado).    | Idem.                                                    |
| **SSH ao LAB-ROUTER-01 (opcional)**      | Usuário dedicado + chave **ed25519** dedicada; `~/.ssh/config`; restringir **gestão** a IPs de confiança se possível.             | Chave privada só no **teu** posto; nunca no repositório. |
| **Probes SNMP**                | `.env.snmp.*` gitignored; scripts `scripts/snmp-*.ps1`.                                                                           | Credenciais SNMP só em env privado.                      |

**Não:** colar chaves ou passwords no chat. **Sim:** revogar e rodar se houver suspeita de exposição.

---

## 4. Segurança operacional — rotina

| Cadência                         | Ação                                                                                                                                       |
| --------                         | ----                                                                                                                                       |
| **Mensal**                       | Rever **Alarm Manager** / quedas de ISP; confirmar data **atualizada** das assinaturas IPS; verificar **firmware** nos dispositivos UniFi. |
| **Trimestral**                   | Revisão da **matriz firewall / IoT**: VLANs vs regras; remover **allow** obsoletas; confirmar **DNS** do IoT.                              |
| **Após mudança de VLAN ou SSID** | Revalidar **isolamento guest**, acesso de **gestão** e **exceções** (documentar em notas privadas).                                        |

---

## 5. Observabilidade — próximos passos (consolidação do lab)

Alinhado a [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md):

1. **Fase C (logs):** **Promtail + Loki + Grafana** (ou VM única) — enviar **syslog** do LAB-ROUTER-01 para o colector; firewall **só LAB-ROUTER-01 → colector**.
1. **Retenção + disco:** definir dias; evitar encher discos pequenos em portáteis.
1. **Fase E opcional:** **Wazuh** manager numa **VM com RAM suficiente**; agentes em Linux do lab — **depois** dos logs centralizados.

---

## 6. Capacidade blue team (escada realista)

| Nível              | Foco                                                                                                          |
| -----              | ----                                                                                                          |
| **0 — Evidência**  | **Logs** centralizados + **tempo** correto (NTP).                                                             |
| **1 — Deteção**    | **IPS/IDS** UniFi + **notificações**; alertas Grafana/Loki em falhas de auth / picos (quando existirem logs). |
| **2 — Correlação** | Mesma janela temporal entre **gateway**, **hosts** e **apps** (syslog + Wazuh opcional).                      |
| **3 — Resposta**   | **Playbook** privado: “se WAN cair”, “se IPS disparar”, “se chave vazar”.                                     |

O produto Data Boar no repositório é à parte; **blue team do lab** fica em runbooks **privados** e planos de observabilidade.

---

## 7. Lembrete de uma linha para a próxima sessão

*“`.env` privado para API UniFi; `unifi.local` e não IP; Owner gere chaves; expandir syslog antes do Wazuh; revisão trimestral IoT/firewall.”*
