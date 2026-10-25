# Playbook de recuperação de disco USB Time Machine e reaproveitamento (safe-first)

**English:** [TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.md](TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.md)

Use este runbook quando você tem um disco USB que era Time Machine do macOS e precisa recuperar dados **antes** de consertar/substituir o Mac.

## Escopo e modelo de segurança

- Objetivo A: recuperar dados agora.
- Objetivo B: reaproveitar o mesmo disco USB como alvo de backup externo (faixa P0 de storage).
- Regra de segurança: **não escrever no disco de origem** antes de validar recuperação/cópia.

## 0) Pré-requisitos

- Um host Linux no lab-op com espaço livre suficiente para a recuperação.
- Cabo USB/alimentação estável (evitar hub, se possível).
- Pacotes disponíveis:
  - `smartmontools`, `gddrescue`, `rsync`, `util-linux`
  - ferramentas opcionais conforme o filesystem (HFS+ vs APFS).

## 1) Intake e triagem (somente leitura)

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MODEL,SERIAL,MOUNTPOINT
sudo smartctl -a /dev/sdX
sudo fdisk -l /dev/sdX
```

- Troque `sdX` pelo disco correto (não partição).
- Se SMART indicar degradação séria, priorize clonagem com `ddrescue`.

## 2) Decidir trilha por filesystem

### Trilha A — Time Machine em HFS+ (cenários antigos)

```bash
sudo mkdir -p /mnt/tm_ro
sudo mount -t hfsplus -o ro /dev/sdXn /mnt/tm_ro
```

### Trilha B — Time Machine em APFS (macOS mais novo)

Suporte APFS em Linux costuma ser read-only e dependente de tooling/versão. Se a montagem APFS estiver instável no host:

- Fallback preferido: conectar temporariamente em um macOS funcional para exportar os dados.
- Se houver APFS read-only estável no seu ambiente Linux, manter estritamente em somente leitura e validar cópias com checksum.

## 3) Se saúde do disco estiver ruim: clonar primeiro

```bash
sudo ddrescue -f -n /dev/sdX /path/recovery/tm_image.img /path/recovery/tm_image.log
sudo ddrescue -d -r3 /dev/sdX /path/recovery/tm_image.img /path/recovery/tm_image.log
```

- Depois disso, trabalhar na imagem, não no disco original.

## 4) Copiar dados para fora (preservando metadados quando possível)

```bash
mkdir -p /path/recovery/export
sudo rsync -aHAX --info=progress2 /mnt/tm_ro/ /path/recovery/export/
```

Depois validar:

```bash
du -sh /mnt/tm_ro /path/recovery/export
```

Amostra de integridade (opcional):

```bash
find /path/recovery/export -type f | shuf -n 20 | xargs -I{} sha256sum "{}"
```

## 5) Só depois da recuperação: reaproveitar como backup externo P0

1. Manter uma cópia adicional (segunda localização) antes de apagar.
1. Limpar tabela de partição e recriar filesystem padrão de backup.
1. Exemplo (ext4):

```bash
sudo wipefs -a /dev/sdX
sudo parted -s /dev/sdX mklabel gpt
sudo parted -s /dev/sdX mkpart primary ext4 1MiB 100%
sudo mkfs.ext4 -L LABOP_EXT_BACKUP /dev/sdX1
```

4. Montar e aplicar política de backup (rotação + teste de restore).

## 6) Política mínima de backup após reaproveitar

- Manter pelo menos 3 cópias (produção + backup local + offsite/cloud quando possível).
- Agendar backup periódico e um teste de restore por mês.
- Registrar evidências de backup/restore em `docs/private/homelab/reports/`.

## 7) Recomendação de urgência para o seu caso

Dada a urgência P0 de storage/backup, faz sentido agir **agora**, nesta ordem:

1. Triagem e SMART.
1. Recuperação/cópia (ou `ddrescue` primeiro se degradado).
1. Validação dos dados recuperados.
1. Só então reaproveitar o disco USB como alvo de backup externo.

Essa sequência minimiza risco de perder dados antigos do Time Machine e, ao mesmo tempo, acelera a criação de um backup externo útil para o lab-op.
