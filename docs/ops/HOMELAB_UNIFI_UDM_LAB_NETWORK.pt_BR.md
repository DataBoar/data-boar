# LAB-ROUTER-01-SE — VLANs, firewall e SNMP no lab (antes do servidor de monitoração)

**Objetivo:** Usar o **UniFi Dream Machine SE** para **tráfego de lab isolado** e **SNMP local** enquanto o **Proxmox / stack de monitoração** não está pronto.

**Importante:** O repositório e o assistente **não** acessam sua LAN. SNMP e a UI UniFi são configurados **por você**, a partir de uma máquina na rede.

**Referência oficial:** [SNMP Monitoring in UniFi Network](https://help.ui.com/hc/en-us/articles/33502980942615-SNMP-Monitoring-in-UniFi-Network) (Ubiquiti).

---

## Resumo

1. **SNMP:** **Definições → CyberSecure → Traffic Logging** (conforme artigo Ubiquiti; preferir **SNMPv3**). **UDP 161** só a partir de IPs de gestão/poller — **nunca** na WAN.
1. **Antes do servidor de monitoração:** num portátil Linux (ex. Zorin), `apt install snmp` e **`snmpwalk`** contra o IP do LAB-ROUTER-01; OID de interfaces `1.3.6.1.2.1.2.2` (ver doc EN para exemplo).
1. **VLANs:** padrão **LAN confiável / lab / IoT**; regras **negar** IoT→lab; detalhes (IDs, subnets) só em **`docs/private/homelab/`** — [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md). *Snapshot do operador (privado): **`LAB_SECURITY_POSTURE.md`** **§1.1**.*
1. **Data Boar:** só precisa de **IP/DNS e portas** no `config.yaml`; VLANs definem **o que o firewall deixa passar**.
1. **DHCP / gateway / DNS / honeypot:** modelo em **[LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md](../private.example/homelab/LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md)** — copiar para **`docs/private/homelab/`**, preencher a tabela de inventário (RFC1918 só local) e usar os comandos de verificação ao ajustar VLANs.
1. **Futuro (colaboradores):** diretriz **pública** e **anonimizada** para segregação “portátil de lab vs redes internas não confiáveis” — **[LAB_NETWORK_SEGREGATION_GUIDELINE.pt_BR.md](LAB_NETWORK_SEGREGATION_GUIDELINE.pt_BR.md)** ([EN](LAB_NETWORK_SEGREGATION_GUIDELINE.md)); por agora **stub**; passos concretos só em **`docs/private/homelab/`**.

**Documento completo (EN):** [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md)
