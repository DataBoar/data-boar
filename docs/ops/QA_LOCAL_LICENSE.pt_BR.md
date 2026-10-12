# QA com `licensing.mode: enforced` — licença local assinada

> **Language:** [English](QA_LOCAL_LICENSE.md)

O bypass por variável de ambiente (`DATA_BOAR_ENV=development` / `DEBUG=1` /
`DATA_BOAR_TIER_OVERRIDE`) foi **removido** (#719). O **único** caminho para
testar o modo enforced é uma licença assinada real. As licenças de QA são
deliberadamente:

- **Curtas** — 60 dias por padrão (um token vazado morre sozinho).
- **Vinculadas à máquina** — o claim `dbmfp` prende a licença ao fingerprint
  de uma máquina; ela se recusa a rodar em qualquer outra
  (`MACHINE_MISMATCH`).
- **Tier enterprise por padrão** — superfície completa de QA.

## 1. Setup único de chaves (máquina emissora — operador)

Mantenha a chave **privada** Ed25519 fora do Git (ex.: `~/.keys/data-boar/`).
Veja `docs/private.example/licensing/README.md` para gerar as chaves.

O `LicenseGuard` em runtime verifica EdDSA e também ML-DSA-65 quando o token traz `dbmldsa_sig` (`decode_license_jwt_hybrid`). Essa chave ML-DSA é a âncora empacotada ou uma rotação aceita. `DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_*` falha fechado (`untrusted_key_override`). Token sem o claim continua só Ed25519 — veja [LICENSING_SPEC.pt_BR.md](../LICENSING_SPEC.pt_BR.md).

### Opcional: chave de assinatura cifrada (passphrase)

A chave de assinatura pode ficar como um PEM PKCS#8 cifrado com AES. O emissor
(`scripts/issue_dev_license_jwt.py`) resolve a passphrase nesta ordem:

1. **Variável de ambiente** `DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD` — o
   caminho não interativo para automação. O Maestro (`Handle-LicensingMatrix.ps1`)
   roda sem terminal, então exporte-a **antes** de executar o handler:

   ```bash
   export DATA_BOAR_LICENSE_ISSUER_PRIVATE_KEY_PASSWORD='sua-passphrase'
   ```

2. **Prompt interativo** — em um TTY sem a variável definida, o emissor pergunta
   `License signing key passphrase:` e lê sem exibir o que é digitado.
3. **Chave sem cifra** — não precisa de passphrase (compatível com o fluxo atual).

Uma chave cifrada sem a variável de ambiente e sem TTY encerra com uma mensagem
acionável (nunca um traceback cru).

## 2. Emitir licença para ESTA máquina

```bash
uv run python scripts/issue_dev_license_jwt.py \
  --private-key-pem-file ~/.keys/data-boar/license-signing-v1-pkcs8.pem \
  --out ~/.keys/data-boar/qa-enterprise.lic
```

Padrões: `--dbtier enterprise --days 60 --dbmfp auto` (vinculada à máquina
que executa o comando).

## 3. Emitir para a máquina de um testador (remoto)

O testador imprime o fingerprint e envia ao operador:

```bash
uv run python scripts/issue_dev_license_jwt.py --show-machine-fingerprint
```

O operador emite com o fingerprint explícito:

```bash
uv run python scripts/issue_dev_license_jwt.py \
  --private-key-pem-file ~/.keys/data-boar/license-signing-v1-pkcs8.pem \
  --dbmfp <fingerprint-hex-do-testador> \
  --out qa-tester.lic
```

Envie apenas o arquivo `.lic` — nunca a chave privada.

## 4. Instalar e rodar enforced

A chave pública oficial de verificação já vai **embarcada** na instalação
(`license-pub-v1.pem`). A âncora ML-DSA-65 (`license-mldsa-pub-v1.pem`, SHA-256
`37faef8ff167cf01a0fc6a2bc8b7cfcac6bfe5651360051b1eb00a0a60fa85b8`) vem no
mesmo wheel para rotação e verificação híbrida opcional; `dbmldsa_sig` ainda
não é obrigatório. Um `.lic` válido e vinculado à máquina basta — sem
env/config de pubkey numa instalação limpa (#1331). Um
`DATA_BOAR_LICENSE_PUBLIC_KEY_*`, `DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_*`,
`licensing.public_key_path` ou `licensing.mldsa_public_key_path` falha
fechado (`untrusted_key_override`, #1992). Rotação de chave é
`licensing.rotation_attestation_path`: as duas âncoras embarcadas precisam
assinar `data-boar/license-key-rotation/v1` mais a época.

```yaml
# config.yaml
licensing:
  mode: enforced
  license_path: /caminho/para/qa-enterprise.lic
```

Ou via ambiente:

```bash
export DATA_BOAR_LICENSE_PATH=/caminho/para/qa-enterprise.lic
```

### Precedência do caminho da licença (#1940)

O `LicenseGuard` resolve o arquivo JWT nesta ordem:

1. **`DATA_BOAR_LICENSE_PATH`** — sempre vence quando aponta para um caminho
   não vazio (após `strip`). Valor só com espaços em branco conta como não
   configurado.
2. **`licensing.license_path`** no `config.yaml` — mesma regra de trim; vale
   quando (1) está ausente ou em branco.
3. **Path canônico da org** — só quando (1) e (2) estão ambos ausentes/em
   branco **e** o arquivo existe:
   - Linux: `$XDG_CONFIG_HOME/databoar/license.jwt` ou
     `~/.config/databoar/license.jwt`
   - macOS: `~/Library/Application Support/databoar/license.jwt`
   - Windows: `%AppData%\databoar\license.jwt`

O nome do diretório é **`databoar`** (org), não o slug do repo `data-boar`.
O `license-studio sign -deploy auto` grava aqui; um JWT pode cobrir vários
bestiais. Um caminho explícito em env ou config **nunca** é substituído em
silêncio — se o arquivo não existir, o enforcement continua **fail-closed**
(`missing_license_file`, #719). O fallback canônico só decide **onde ler**;
validação de assinatura e claims não muda.

Confira `GET /health` / `GET /about`: o estado precisa ser **VALID** com
`dbtier: enterprise`. Sem licença válida, o modo enforced **falha fechado**
(scans negados com 403/Safe-Hold) — veja `docs/LICENSING_SPEC.md`.

## Notas

- Containers/pools de VM: defina um `DATA_BOAR_MACHINE_SEED` estável **antes**
  de imprimir o fingerprint e mantenha a mesma seed em runtime, ou o
  fingerprint não vai bater.
- O Maestro (`Handle-LicensingMatrix.ps1`) emite os três `.lic` de tier com
  os mesmos padrões de 60 dias + vínculo de máquina.
- Toda decisão de enforcement é registrada no logger
  `data_boar.licensing.audit` (prefixo `LICENSE_AUDIT`).
