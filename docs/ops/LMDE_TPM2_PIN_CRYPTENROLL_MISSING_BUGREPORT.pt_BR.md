# Bug report (copy/paste): LMDE sem `systemd-cryptenroll` bloqueia TPM2+PIN no LUKS

**English:** [LMDE_TPM2_PIN_CRYPTENROLL_MISSING_BUGREPORT.md](LMDE_TPM2_PIN_CRYPTENROLL_MISSING_BUGREPORT.md)

## Onde reportar (canais recomendados)

- **Primário (LMDE)**: abrir issue no `linuxmint/lmde7-beta` (GitHub).
- **Guia**: [Reporting an issue](https://linuxmint.github.io/reporting-an-issue.html)

## Resumo

Em um sistema LMDE 7 instalado, o utilitário `systemd-cryptenroll` não está disponível (`command not found` / binário ausente). Isso bloqueia o enrollment via TPM2 para LUKS (incluindo o padrão comum “TPM2 + PIN”), que é importante para usuários que precisam de criptografia de disco com autenticação de boot (corporates / alta garantia / ameaça “evil maid”).

Como workaround, `clevis+tpm2` pode oferecer desbloqueio TPM-only, mas isso não cobre o mesmo UX/postura de segurança de TPM2+PIN “de fábrica”.

## Ambiente

- **Distro**: LMDE 7 “Gigi”
- **Objetivo**: LUKS2 com unlock assistido por TPM2 (idealmente TPM2 + PIN)
- **Observado**: `systemd` está instalado/rodando, mas `systemd-cryptenroll` está ausente dos paths típicos.

## Reprodução (mínimo)

No LMDE instalado:

```bash
command -v systemd-cryptenroll || true
ls -la /usr/bin/systemd-cryptenroll /usr/lib/systemd/systemd-cryptenroll 2>/dev/null || true
dpkg -L systemd | grep -i cryptenroll || true
apt-cache search --names-only cryptenroll || true
```

## Esperado

- `systemd-cryptenroll` disponível como parte do tooling do systemd no LMDE (como em distros Debian-family), permitindo:
  - `systemd-cryptenroll --tpm2-device=auto --tpm2-with-pin=yes ...`

## Observado

- `systemd-cryptenroll` não é encontrado / não é distribuído, forçando o uso de ferramentas alternativas.

## Por que isso importa (breve)

- TPM2+PIN equilibra melhor conveniência vs proteção contra ataques offline/“evil maid” do que TPM-only.
- A ausência do utilitário empurra usuários para escolhas operacionais mais fracas (passphrase curta, TPM-only, ou digitar passphrase em todo boot).

## Direção sugerida

- Distribuir `systemd-cryptenroll` no LMDE 7 (ou documentar qual pacote o fornece no LMDE).
- Se a exclusão for intencional, documentar o caminho suportado para TPM2+PIN + LUKS no LMDE.

