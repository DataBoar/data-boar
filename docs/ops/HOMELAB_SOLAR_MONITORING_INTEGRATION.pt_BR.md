# Monitoração solar no homelab — o que dá para integrar (e o que não dá)

**O assistente/repo não acessa** sua **LAN**, **VLAN** nem as **APIs do fabricante** com suas credenciais.

**Documento completo (EN):** [HOMELAB_SOLAR_MONITORING_INTEGRATION.md](HOMELAB_SOLAR_MONITORING_INTEGRATION.md)

---

## Resumo

1. **“Shine”** pode ser **Solis** (SolisCloud + logger tipo **ShineWiFi**) ou ecossistema **Growatt/ShineMonitor** (app estilo **ShinePhone**, API em [api.shinemonitor.com](https://api.shinemonitor.com/)) — confirmar pelo **rótulo do inversor** e pela **app**.
1. **SolisCloud:** API com chaves via portal/suporte — ver doc oficial em inglês §2.
1. **ShineMonitor:** HTTP GET + autenticação com **SHA-1**, `company-key`, token — ver §3 no EN.
1. **LAN:** opcional **Modbus** / página local do logger — só na **VLAN** certa, **sem** expor à internet.
1. **4 kWp** é pico DC; à **noite** geração **0** é normal; **nobreak** e **disjuntores** seguem o plano em [HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md](HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md).

**Notas locais:** arquivo **só no seu disco** em **`docs/private/homelab/`** (gitignored — ver [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md)); modelo §6 no EN.
