# Segregação de rede no lab — diretriz genérica (público)

**English:** [LAB_NETWORK_SEGREGATION_GUIDELINE.md](LAB_NETWORK_SEGREGATION_GUIDELINE.md)

**Estado:** **Stub** — expandir quando houver tempo. Esta página é **genérica** de propósito: ajuda **colaboradores** a alinhar **lógica de VLAN** e **ordem de regras** sem colocar **dados do site** no Git.

**Par privado:** Runbook **concreto** (subnets reais, hostnames, política do operador) fica só em **`docs/private/homelab/`** (gitignored). **Não** colar mapas RFC1918, intervalos de redes de terceiros nem listas **nomeadas** de produtos comerciais de segurança/scan em Markdown **rastreado**.

---

## 1. Público e âmbito

| Cabe aqui | Não cabe aqui |
| --------- | ------------- |
| Padrão **lógico**: VLAN de lab vs LAN confiável vs intervalos internos não confiáveis | **IDs** de VLAN, **IPs** ou **SSIDs** reais, nomes de empresas |
| Ideias de **ordem** de regras (negar caminhos antes de liberar WAN) | Blocklists **específicas** de produto que mudam o tempo todo |
| Lembrar **DNS/DHCP** intencionais por VLAN | Passo a passo de **uma** build concreta da UI do controlador |

---

## 2. Modelo de ameaça (resumo)

Um **portátil de lab** pode precisar de **Internet** para **updates de SO/firmware** sem iniciar sessões para **redes de terceiros** em que não confias (LANs de consultoria, VPNs de cliente, Wi‑Fi de escritório compartilhado, etc.). **Segmentação** no gateway (ex. **Traffic Rules** UniFi) + **política de DNS** reduz **contacto acidental** mais do que “mesmo SSID e rezar”.

---

## 3. Padrão genérico (sem listas comerciais)

1. **VLAN dedicada** (em geral com **SSID** próprio) só para equipamentos de **lab**.
1. **Grupos de endereços** no gateway: (a) **servidores de lab** ainda necessários (SSH, portas de app), (b) **prefixos internos não confiáveis** a bloquear — **preencher só em notas privadas**, não aqui.
1. **Ordem sugerida** de regras de firewall:
   - **Bloquear** → grupos internos não confiáveis (§3.1b).
   - **Permitir** → grupo de servidores de lab (portas mínimas se a UI permitir).
   - **Permitir** → **Internet** / WAN (updates, HTTPS).
   - Opcional: **bloquear** acesso à VLAN de **gestão** do gateway a partir do lab se administras o equipamento sempre de outra estação.
1. **DNS:** resolvedores **coerentes** por VLAN; evitar enviar DNS do lab para um **resolver corporativo** que não controlas, salvo decisão explícita.
1. **Verificação:** no host de lab, confirmar **gateway**, **DNS**, **HTTPS** para um host de teste conhecido e **falha esperada** para um IP de teste documentado **só em privado**.

---

## 4. O que **nunca** entra neste doc público

- **Hostnames** ou endereços **RFC1918** reais da tua LAN.
- Identificadores de **cliente**, **consultoria** ou **empregador**.
- **Enumerações** de **EDR**, **scan** ou **SOC** SaaS com nomes comerciais (mudam; a política fica em **runbook privado** ou ticket interno).

---

## 5. Como expandir este stub depois

Ao promover conteúdo de um runbook **privado**:

1. Trocar cada IP literal por **exemplos** estilo **`10.0.0.0/24`** ou placeholders.
2. Remover ferramentas de terceiros **nomeadas**; manter formulações como “**prefixos internos não confiáveis**” e “**listas deny na nuvem** (mantidas em privado).”
3. Acrescentar **um** exemplo numérico só com subnets **placeholder** (**VLAN 100**, **10.0.100.0/24**, etc.).
4. Cruzar com **[HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md)** para contexto SNMP/VLAN.

---

## 6. Ver também

- [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md) — LAB-ROUTER-01-SE, padrões de VLAN/firewall, SNMP.
- [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) — matriz multi-host; detalhes de LAN em privado.
- [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md) — árvore **`docs/private/`**.

**Última atualização:** 2026-03-31 (criação do stub).
