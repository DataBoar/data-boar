# LAB-OP — CAPEX / OPEX & Procurement (plano rastreado)

**Status:** Pending
**Date:** 2026-04-02
**Authors:** Fabio Leitao
**Priority:** H2

**Âmbito:** Infra **do operador** (LAB-OP): hardware, rede, energia/HVAC, segurança física, software, assinaturas, tokens de IA, treinamento. Sem preços, links ou nomes de lojas — detalhes reais no arquivo privado gitignored.

**Arquivo privado (detalhes e preços):** `docs/private/homelab/LAB_OP_SHOPPING_LIST_AND_POWER.pt_BR.md`

**Relação com outros planos:**

| Tema | Plano / Doc |
| ---- | ----------- |
| Observabilidade (métricas/logs/SIEM) | [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md) |
| Firewall/L3/acesso/sequência | [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md) |
| Validação de produção (homelab) | `docs/ops/HOMELAB_VALIDATION.pt_BR.md` |

---

## Princípio de compra

> **Evidência antes de despesa.** Todo item deve ter uma justificativa rastreável (host report, incidente real, Lynis warning, temperatura, queda de energia, gargalo medido). Promover itens P2→P1→P0 somente quando houver evidência ou risco iminente.

**Camadas de prioridade:**
- **P0 (prioritário agora):** elimina risco real de downtime, segurança ou travamento de entregas.
- **P1 (necessário em breve):** melhora robustez, repetibilidade, qualidade operacional.
- **P2 (sonhos / horizonte futuro):** upgrades significativos quando houver orçamento e evidência.

---

## 1. Computadores e hosts (LAB-OP)

### 1.1 Inventário atual (resumido por classe)

| Host | Classe | Papel principal | Hardware relevante (do host report) | Gap / oportunidade |
| ---- | ------ | --------------- | ------------------------------------ | ------------------- |
| **LAB-NODE-01** | ThinkPad LAB-NODE-01 Gen 3 | workstation dev + LMDE 7 | i7-1365U, 16 GiB DDR5 (1 slot livre), NVMe 1 TB WD SN740 | RAM limitada para observabilidade pesada; sem swap (intencional) |
| **L-series** | ThinkPad L-series (14-inch class) | dev secondary / roaming | (dados incompletos; preencher com host report) | RAM/disco a confirmar; PC Windows principal de desenvolvimento tem DDR4 SODIMM tipicamente |
| **lab-op** | Servidor x86 de lab (classe legada) | Docker Swarm mgr | Ver inventário privado | CPU antiga; candidato a substituição quando VT-d / RAM forem requisito |
| **<lab-host-2>** | Mini PC Void Linux | utility / proxy / gateway | 8 GiB RAM, SATA SSD, zram 2 GB | uv + Python 3.14 — bem equipado para tarefas leves |
| **lab-sbc** | ARM SBC (classe Pi) | probe / SNMP / alertas | Ver inventário privado | RAM/SD limitados; não é candidato a Wazuh |

### 1.2 Upgrades de hosts (P0/P1/P2)

| Item | Prioridade | Justificativa |
| ---- | ---------- | ------------- |
| **RAM LAB-NODE-01: 16 → 32 GiB** (DDR5 SODIMM 1×16 GiB) | P0 | Observabilidade, VMs locais, builds maiores. Slot livre confirmado. |
| **RAM (PC principal de dev)** (confirmar slot + tipo) | P1 | Completar com host report do PC Windows principal de desenvolvimento antes de comprar. |
| **Servidor x86 "torre" / Proxmox** | P1 | Hospedar Grafana + Loki + Wazuh sem afetar workstations. Host **lab-op** legado muito limitado. |
| **Substituir host lab-op legado** | P1 | Substituir por máquina com VT-d, IOMMU, RAM expandível para Swarm/Proxmox. |
| **SBC ARM → geração mais nova** | P2 | Probe atual funciona; upgrade abriria containerização leve. |
| **SSD NVMe externo (backup criptografado)** | P0 | Cópia offline de evidências, config, snapshots BTRFS. |

### 1.3 Em storage (equipamentos que temos mas aguardam)

> Preencher no arquivo privado com o inventário real, modelos, estado (funcional/quebrado/aguardando peça).

---

## 2. Rede (LAN, Wi-Fi, firewall, redundância)

### 2.1 Inventário atual (sem IPs ou nomes reais)

| Item | Modelo | Papel | Gap / oportunidade |
| ---- | ------ | ----- | ------------------- |
| LAB-ROUTER-01 | (ver private) | firewall + router + IDS/IPS | único ponto de falha; config backup periódico crítico |
| Switch | (ver private) | L2 | sem redundância de link |
| APs | UniFi | Wi-Fi | dependentes do LAB-ROUTER-01 |

### 2.2 Melhorias de rede (P0/P1/P2)

| Item | Prioridade | Justificativa |
| ---- | ---------- | ------------- |
| **Backup de config LAB-ROUTER-01/switch/AP** (automatizado) | P0 | Sem backup, qualquer falha de hardware = horas de reconfiguração. |
| **2º link de internet** (failover/dual-WAN) | P1 | Latência zero em caso de queda do ISP primário. Essencial quando clientes dependem de uptime. |
| **UPS para rede** (LAB-ROUTER-01 + switch + ONT/modem) | P0 | Sem UPS, uma queda de energia derruba toda a LAN mesmo que os servidores sobrevivam. |
| **LAB-ROUTER-01 reserva** (cold spare) | P1 | Swap em minutos vs dias esperando entrega. |
| **Segmentação VLAN (lab vs guests vs IoT)** | P1 | Já parcialmente feito; documentar e validar isolamento. |
| **Switch/links 2.5G/10G entre hosts críticos** | P2 | Para movimentação de dados (backups, snapshots, NAS). |

---

## 3. Energia, Enel, solar, UPS

### 3.1 Estado atual (preencher medições no arquivo privado)

- Consumo estimado (kWh/mês): ___
- Pico de demanda: ___
- Circuito do lab: ___A, ___mm², ___AWG
- Geração solar instalada: ___kWp
- Quedas: frequência e duração registradas: ___

### 3.2 Itens de energia (P0/P1/P2)

| Item | Prioridade | Justificativa |
| ---- | ---------- | ------------- |
| **UPS para rede** (ver §2.2) | P0 | Uptime de rede independente da energia. |
| **UPS para hosts críticos** (LAB-NODE-01 + servidor) | P1 | Shutdown limpo evita corrupção de FS (BTRFS, ZFS). |
| **Medição de consumo real** (tomada inteligente / clamp) | P1 | Sem medição, não é possível dimensionar UPS ou avaliar ROI solar. |
| **Expansão de placas solares** | P1 | Reduz OPEX de energia se o lab crescer; avaliar após medição real. |
| **Aumento de carga (Enel)** | P1 | Solicitar somente se medições indicarem que o ramal/quadro está no limite. |
| **Armazenamento de energia (bateria)** | P2 | Para ilhas de energia críticas sem depender da rede Enel. |
| **Automação de cargas** (desligar não-críticos na queda) | P2 | Maximiza autonomia do UPS/bateria. |

---

## 4. HVAC — ar-condicionado e ambiente

### 4.1 Objetivo

- Proteger hardware contra temperatura/umidade fora da faixa operacional.
- Manter conforto do operador (sem "morrer no calor" ou comprometer saúde).
- Evitar throttling de CPU por temperatura (afeta performance de build/scan).
- Reduzir risco de falha prematura de componentes eletrônicos.

### 4.2 Análise dos modelos vistos (fotos do operador)

| Marca | Linha | BTU | Inverter | Gás | Observações técnicas | Prioridade |
| ----- | ----- | --- | -------- | --- | -------------------- | ---------- |
| **LG** | Dual Inverter | (confirmar; foto parcialmente legível) | Sim | (confirmar) | LG tem boa reputação de assistência técnica e eficiência; confirmar nível de ruído (dB) e consumo nominal em W; garantia 10 anos no compressor (inverter) | P1/P2 |
| **Elgin** | Inverter R32 | 12.000 BTU | Sim | R32 | R32 tem menor GWP que R410a; Elgin é nacional (assistência capilar); 12.000 BTU serve para ambientes ~15–20 m²; confirmar nível de ruído e ENCE/Procel | P1 |

**Decisões a tomar (preencher no privado):**

| Questão | Status |
| ------- | ------ |
| HVAC atual está suficiente para a temperatura de pico do lab? | ___ |
| Qual a temperatura máxima medida no ambiente do lab (verão)? | ___ |
| O "HVAC reserva" está funcional e pronto para swap? | ___ |
| Faz sentido instalar um 2º equipamento (redundância)? | ___ |
| Instalação: precisa de nova tomada 220V ou adaptação elétrica? | ___ |

**Recomendação preliminar (sujeita a medições):**

- Se o HVAC atual falha ou não cobre a sala do lab: **Elgin 12.000 BTU R32 Inverter** é o candidato P1 por custo/benefício e assistência nacional.
- Se há orçamento e deseja mais qualidade/silêncio: **LG Dual Inverter** (confirmar BTU e preço) como P1/P2.
- **Antes de comprar**: medir temperatura real do lab em dia quente, verificar estado do HVAC reserva, e confirmar que a instalação elétrica suporta (bitola, disjuntor, tomada).

### 4.3 Itens HVAC (P0/P1/P2)

| Item | Prioridade | Justificativa |
| ---- | ---------- | ------------- |
| **Manutenção preventiva do HVAC atual** (limpeza, gás) | P0 | Antes de substituir, verificar se manutenção resolve. |
| **Novo HVAC para o lab** (inverter, R32) | P1 | Se temperatura de pico comprometer o hardware ou o operador. |
| **Sensor de temperatura/umidade com log** | P1 | Sem dados, não há evidência para justificar HVAC ou UPS. |
| **HVAC reserva funcional** (revisão/conserto) | P1 | Se o reserva estiver quebrado, consertá-lo é mais barato que comprar novo. |
| **Redundância de HVAC** (2 equipamentos) | P2 | Ambiente 24/7 mission-critical; para lab pessoal, manutenção preventiva é suficiente. |

---

## 5. Segurança física e operacional

| Item | Prioridade | Justificativa |
| ---- | ---------- | ------------- |
| Etiquetagem e organização de cabos | P0 | Reduz erro humano; facilita manutenção. |
| Sensor de temperatura/umidade (com log SNMP/MQTT) | P1 | Evidência objetiva para decisões de HVAC e UPS. |
| Câmera/monitoramento local | P2 | Segurança física adicional. |

---

## 6. Ferramentas, cabos, peças de reposição

| Item | Prioridade | Justificativa |
| ---- | ---------- | ------------- |
| Cabos Ethernet cat6 (rezerva) | P0 | Custo mínimo, elimina atraso em reconfiguração. |
| Kit de manutenção (chaves Torx/Phillips, spudger, ESD) | P0 | Para T-series and L-series ThinkPads e outros notebooks; sem isso, manutenção é inviável. |
| Carregadores/fontes reserva para notebooks | P1 | Fora de linha podem demorar semanas para repor. |
| KVM 2 portas para manutenção sem monitor extra | P1 | Reduz toil em manutenção de hosts headless. |
| Estoque mínimo de peças (SSD 2.5", M.2, fans) | P2 | Reduz downtime de hosts legacy. |

---

## 7. Biometria (fingerprint / face) para Linux

| Item | Prioridade | Justificativa |
| ---- | ---------- | ------------- |
| Verificar suporte nativo (LAB-NODE-01 Goodix `27c6:6594` já detectado) | P0 | Goodix já aparece no USBGuard como `allow`; verificar `libfprint` support. |
| Leitor USB fingerprint compatível com libfprint | P1 | Para hosts sem leitor embutido. |
| Webcam IR / face recognition (Windows Hello-like) | P2 | Menos padronizado no Linux; tratar como "nice to have". |

---

## 8. Software, licenças, assinaturas e tokens

### 8.1 OPEX recorrente (assinaturas)

| Item | Propósito | Impacto se cancelar | Prioridade |
| ---- | --------- | ------------------- | ---------- |
| **GitHub** (plano atual) | CI, PRs, segurança, Actions | Perde Actions minutos grátis e features de segurança | P0 |
| **Cursor** (IDE + AI agent) | Produtividade central do dev | Bloqueia fluxo de trabalho atual | P0 |
| **Modelos/tokens** (Anthropic/OpenAI/Gemini) | WRB, revisões técnicas, agentes | Reduz qualidade das revisões externas | P1 |
| **Domínio(s)** | Website, emails, identidade | Perda de identidade digital | P0 |
| **Grafana Cloud** (free tier ou paid) | Observabilidade lab-op | Substituível por self-hosted | P1/P2 |
| **SonarQube** (self-hosted ou Cloud) | Qualidade de código | Substituível; self-hosted já configurado | P1 |
| **Docker Hub** (plano) | Distribuição de imagens | Free tier limitado; pago se volume crescer | P1 |

### 8.2 Tokens de IA (estimativa de uso/custo)

> Detalhar no arquivo privado com valores reais e cadência.

- **Claude/Anthropic (via Cursor):** uso diário intensivo; custo principal.
- **Gemini (Google):** revisões WRB; uso eventual.
- **OpenAI:** eventual, dependendo de integração.

**Recomendação:** monitorar gasto mensal e avaliar se o plan atual (Pro/Ultra) é o mais custo-efetivo para o volume de uso.

### 8.3 Treinamento e cursos (OPEX ou CAPEX único)

| Item | Prioridade | Justificativa |
| ---- | ---------- | ------------- |
| **CWL** (cyber) — BTF → C3SA | P0 | Cadência combinada; pago; impacta certificações e credibilidade |
| **AI (Academy/outros)** | P1 | Alinhamento com ritmo do mercado |
| **Infra / Linux / observability** | P1 | Suporta LAB-OP e entregáveis do produto |
| **Cloud / DevOps / SRE** | P2 | Expansão de capacidade técnica futura |

---

## 9. Oportunidades de melhoria por categoria (resumo executivo)

### Curto prazo (P0 — fazer agora)

1. **RAM LAB-NODE-01** (16→32 GiB, DDR5 SODIMM): slot livre confirmado, custo baixo vs impacto alto.
2. **UPS para rede** (LAB-ROUTER-01 + switch): sem isso, qualquer queda derruba tudo.
3. **Backup automático de config LAB-ROUTER-01**: risco alto, custo zero (script).
4. **Manutenção preventiva do HVAC atual**: antes de comprar, verificar estado.
5. **SSD externo criptografado**: backup de evidências offline.
6. **Kit de manutenção**: desbloqueador de hardware crítico.

### Médio prazo (P1 — próximos 6 meses)

7. **Novo HVAC** (Elgin ou LG inverter, confirmar BTU) — se temperatura comprometer lab.
8. **Sensor de temperatura com log** — evidência objetiva.
9. **2º link de internet** (failover ISP).
10. **Servidor x86 para Proxmox** (aposentar LAB-NODE-02 E6430).
11. **UPS para hosts críticos** (LAB-NODE-01 + servidor).
12. **Expansão/revisão solar** — após medição de consumo real.

### Longo prazo (P2 — horizonte futuro)

13. **Pi 4/5** em lugar do Pi 3B.
14. **Switch 2.5G/10G** entre hosts críticos.
15. **LAB-ROUTER-01 cold spare** (2º firewall).
16. **Armazenamento de energia** (bateria).
17. **Redundância de HVAC**.
18. **Servidor dedicado de observabilidade** (Wazuh, Graylog, etc.).

---

## 10. Sequência de investimento sugerida

```
Fase 1 (agora, baixo custo):
  RAM LAB-NODE-01 → UPS rede → backup LAB-ROUTER-01 → SSD externo → kit manutenção

Fase 2 (quando houver orçamento):
  Sensor temperatura → HVAC (se necessário) → 2º link internet
  → UPS hosts críticos → servidor Proxmox

Fase 3 (crescimento):
  Solar (expansão) → Pi 4/5 → switch 2.5G → LAB-ROUTER-01 spare
  → observabilidade pesada (Wazuh/Graylog)
```

---

## 11. Acompanhamento

- **Lista privada (preços reais):** `docs/private/homelab/LAB_OP_SHOPPING_LIST_AND_POWER.pt_BR.md`
- **Lista pública (exemplo sem preços):** `docs/ops/LAB_OP_SHOPPING_LIST_EXAMPLE.md`
- **Dependências de infra:** [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md)
- **Stack de observabilidade:** [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md)
- **PLANS_TODO.md:** linha LAB-OP CAPEX/OPEX & Procurement.

**Estado:** 🔄 Ativo — promover itens P2→P1→P0 conforme evidências dos host reports e incidentes reais.
