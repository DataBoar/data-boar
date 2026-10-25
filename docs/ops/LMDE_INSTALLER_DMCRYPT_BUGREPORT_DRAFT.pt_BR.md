# Bug report (copy/paste): instalador do LMDE não mostra dm-crypt (`/dev/mapper/*`) no particionamento manual

Este texto é para os mantenedores do instalador do LMDE/Linux Mint (Ubiquity / UI de particionamento). Ele evita de propósito segredos e detalhes sensíveis do ambiente.

## Onde reportar (canais recomendados)

- **Primário**: abrir issue no GitHub do `linuxmint/ubiquity` (aba Issues).
- **Guia da comunidade**: [Reporting an issue](https://linuxmint.github.io/reporting-an-issue.html)

## Resumo

Ao instalar **LMDE** usando **particionamento manual**, mapeamentos **dm-crypt** já desbloqueados (ex.: `cryptsetup open … cryptroot` → `/dev/mapper/cryptroot`) **não aparecem** na lista de partições. Com isso, o instalador não permite selecionar o mapper como `/`.

Isso torna o caminho de particionamento manual inseguro: o usuário é empurrado para selecionar a partição “crua” por baixo (ex.: `/dev/nvme0n1p6`) e formatar — o que destrói o header do LUKS e quebra o fluxo pretendido de criptografia de disco.

## Impacto

- **Risco para o usuário**: é fácil “quebrar” a instalação criptografada ao formatar o device cru.
- **Problema de UX**: particionamento manual fica, na prática, não funcional para dm-crypt/FDE.
- **Custo de suporte**: leva a loop de tentativa/erro e recuperação manual.

## Ambiente

- **Distro**: LMDE 7 “Gigi” live ISO
- **Instalador**: “Install Linux Mint” (UI de particionamento manual baseada em Ubiquity)
- **Firmware**: UEFI, Secure Boot habilitado
- **Objetivo do layout**:
  - ESP (FAT32) montada em `/boot/efi` (existente)
  - ext4 `/boot`
  - root pretendido dentro de LUKS2 (btrfs)
- **Objetivo**: dual boot (Windows preservado), LUKS2 para root, snapshots btrfs depois

> Se necessário, posso adicionar versões exatas dos pacotes `ubiquity`/componentes do instalador; por favor indiquem o comando preferido no live session.

## Passos para reproduzir (mínimo)

1. Boot no live ISO do LMDE.
2. Preparar partições (ou usar uma partição alvo existente):
   - manter a ESP (FAT32)
   - criar ext4 `/boot`
   - criar uma partição grande para criptografar (ex.: `/dev/nvme0n1p6`)
3. No live, criar e desbloquear o dm-crypt:

```bash
sudo cryptsetup luksFormat /dev/nvme0n1p6
sudo cryptsetup open /dev/nvme0n1p6 cryptroot
```

4. Validar que o mapper existe (antes de abrir o instalador):

```bash
ls -la /dev/mapper/
lsblk -f
```

5. Abrir o instalador e ir para **Manual partitioning**.

## Comportamento esperado

- A UI lista `/dev/mapper/cryptroot` (ou equivalente) e permite selecioná-lo como `/` (e formatar como btrfs/ext4).

## Comportamento observado

- A UI não lista entradas `/dev/mapper/*`.
- Só aparece a partição crua (`/dev/nvme0n1p6`) como alvo selecionável para `/` e formatação.

## Evidências para anexar (sem dados sensíveis)

- **Screenshot 1**: tela de particionamento manual mostrando a ausência de `/dev/mapper/*`.
- **Saída de terminal**:
  - `ls -la /dev/mapper/` (mostra que o mapping `cryptroot` existe)
  - `lsblk -f` (mostra `crypto_LUKS` + mapping)

> Screenshots não estão incluídos neste rascunho versionado. Ao abrir a issue, anexe os screenshots coletados durante a tentativa de instalação.

## Workaround usado (funciona, mas não é óbvio)

Instalar primeiro em **btrfs sem criptografia** na partição crua, **não reiniciar**, e depois criptografar “in-place” com `cryptsetup reencrypt`, seguido de updates de initramfs/GRUB via chroot (detalhes disponíveis se necessário).

- Referência comunitária: `https://gist.github.com/Leniwcowaty/4b2c239ca74629cad60d4718f79ff600`

## Contexto adicional (breve)

No nosso setup, também tentamos chegar num UX “BitLocker-like” com FDE forte (LUKS) e menos atrito no boot:

- `systemd-cryptenroll` não estava disponível no LMDE instalado, então não conseguimos testar TPM2+PIN via `systemd-cryptenroll`.
- Usamos `clevis+tpm2` como workaround para reduzir a digitação de passphrase, mas isso tende a desbloqueio TPM-only a menos que haja uma camada extra de autenticação no boot.

Isto **não** é o núcleo deste bug report, mas aumentou o custo dos workarounds depois que o instalador falhou em expor `/dev/mapper/*` no particionamento manual.

Issue relacionada (TPM2+PIN / disponibilidade do `systemd-cryptenroll`): `https://github.com/linuxmint/live-installer/issues/177`

## Direção sugerida de correção

- No particionamento manual, atualizar/incluir `/dev/mapper/*` após o unlock do dm-crypt.
- Alternativamente, oferecer uma ação explícita “desbloquear volume criptografado” e, após o unlock, expor o mapper como alvo selecionável.

