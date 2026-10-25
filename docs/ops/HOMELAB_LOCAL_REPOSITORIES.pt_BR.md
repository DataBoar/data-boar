# Repositórios locais no homelab (registry Docker + apt Debian)

**Objetivo:** Planejar **registry Docker local** e **repositório apt Debian local** para o homelab, sequenciado **depois** do **servidor Proxmox** estar pronto.

**Documento completo (EN, exemplos e estimativas):** [HOMELAB_LOCAL_REPOSITORIES.md](HOMELAB_LOCAL_REPOSITORIES.md)

---

## Resumo

**Quando:** Após **Proxmox** instalado, **≥1 VM/LXC** com **disco** suficiente (≥20 GB para registry + apt subset; ≥50 GB se espelhar Debian completo).

**Docker registry:** **`registry:2`** (simples) ou **Harbor** (UI + scanning). **Storage:** ~1–3 GB para Data Boar + bases + DBs; planeje **≥10 GB** para crescimento.

**Apt repo:** **reprepro** (pacotes `.deb` próprios) ou **apt-mirror** (espelhar Debian/Ubuntu). **Storage:** ~5–20 GB para subset + custom; **≥50 GB** para múltiplos releases.

**Relação:** Repo **local** = teste de `.deb` antes do **público** ([PLAN_SELF_UPGRADE §9](../plans/PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md#9-alternative-delivery-package-manager-and-signed-artifacts-winget-like-deb-apt)); **offline** lab; **pulls** mais rápidos.

**Segurança:** Registry **inseguro** em **VLAN** confiável é aceitável para lab; **TLS + auth** para prática prod-like. Apt: **GPG signing** recomendado.
