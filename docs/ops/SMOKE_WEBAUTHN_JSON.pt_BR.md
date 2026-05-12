# Smoke: WebAuthn JSON RP (subconjunto operador / CI)

**English:** [SMOKE_WEBAUTHN_JSON.md](SMOKE_WEBAUTHN_JSON.md)

**Plano:** [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) fase **1a**; **ADR:** [0033](../adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md).

**Escopo:** Cobertura **pytest** automatizada para os endpoints JSON opcionais **`/auth/webauthn/*`** (sem navegador nem autenticador real). Cerimônias **FIDO2** completas com passkey ficam como verificação **manual** fora deste subconjunto.

---

## Smoke autônomo (qualquer máquina com o repositório)

Na raiz do repositório (Windows):

```powershell
.\scripts\smoke-webauthn-json.ps1
```

O gate completo antes do merge continua sendo **`.\scripts\check-all.ps1`** (este script não substitui).

### O que isso prova

Consulte a tabela em [SMOKE_WEBAUTHN_JSON.md](SMOKE_WEBAUTHN_JSON.md) (mesmos testes; nomes de função em inglês no código).

---

## Integração manual (opcional)

1. Defina **`api.webauthn.enabled: true`**, **`api.webauthn.origin`** / **`rp_id`** alinhados à origem HTTPS, e **`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`** antes de **`main.py --web`**.
1. Use um **front-end** mínimo ou devtools para exercitar WebAuthn contra os endpoints JSON; veja [USAGE.md](../USAGE.pt_BR.md) e [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md).
1. O **HTML do painel** **ainda não** exige login por este cookie até a fase **1b+** do **[#86](https://github.com/FabioLeitao/data-boar/issues/86)**.
