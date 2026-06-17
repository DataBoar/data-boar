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

```yaml
# config.yaml
licensing:
  mode: enforced
  license_path: /caminho/para/qa-enterprise.lic
  public_key_path: /caminho/para/license-pub-v1.pem
```

Ou via ambiente:

```bash
export DATA_BOAR_LICENSE_PATH=/caminho/para/qa-enterprise.lic
export DATA_BOAR_LICENSE_PUBLIC_KEY_PATH=/caminho/para/license-pub-v1.pem
```

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
