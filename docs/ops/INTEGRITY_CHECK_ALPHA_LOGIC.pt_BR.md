# Verificação de integridade e lógica alpha (especificação de desenho)

**English:** [INTEGRITY_CHECK_ALPHA_LOGIC.md](INTEGRITY_CHECK_ALPHA_LOGIC.md)

**Hub de navegação de integridade:** [INTEGRITY_HUB.pt_BR.md](INTEGRITY_HUB.pt_BR.md) ([EN](INTEGRITY_HUB.md)) — mapa completo de runtime, release e superfícies ADR.

Este documento é uma **especificação de desenho** para verificação **opcional** de integridade em runtime de artefatos críticos do Data Boar (fontes Python, extensões nativas opcionais e hashes de referência assinados). **Não** garante que todo o comportamento abaixo já esteja implementado no produto principal até existir ADR e código explícito.

## Objetivos

- Detectar modificação inesperada de bits implantados antes de relatórios de alta confiança.
- Falhar com segurança: preferir saída **degradada e claramente rotulada** a claims silenciosos de conformidade.
- Produzir **evidência auditável** (log estruturado) para revisão de segurança.

## Pseudo-especificação

### 1) Hashing na subida

Em subida controlada (feature flag opcional, ex.: `DATA_BOAR_INTEGRITY_CHECK=1`):

1. Enumerar **caminhos críticos** (lista configurável), por exemplo:
   - subconjunto de `core/*.py`, `pro/*.py` e módulos empacotados (ex.: `boar_fast_filter` quando presente).
2. Calcular **SHA-256** por arquivo (ou digest canônico da wheel para extensões).
3. Comparar com um **manifesto known-good** (JSON ou documento assinado) versionado com o release.

O manifesto deve ser **mantido pelo engenheiro de release** e versionado junto ao release.

### 2) Cross-check

- **Match:** operação normal; opcionalmente registrar `integrity_ok` em nível debug.
- **Mismatch:** entrar em **estado tinted** (abaixo).

### 3) Estado tinted (discrepância)

Quando qualquer hash crítico falhar:

- Definir flag em nível de processo (conceitualmente `__IS_TINTED__ = True`; a implementação pode usar singleton de módulo ou export via ambiente).
- Expor **metadados explícitos de versão/build** indicando suspeita de adulteração (texto exato é decisão de produto; não deve personificar release estável).
- Ativar **modo limitado** nos geradores de relatório:
  - limitar tamanho da narrativa exportada (ex.: primeiras N linhas);
  - inserir marca d’água visível de **não confiável** em saídas legíveis por humanos;
  - evitar alegar completude regulatória.

### 4) Auditoria

Anexar registro estruturado a `security_alert.log` (ou destino SIEM):

- timestamp, hostname, versão do Data Boar, lista de caminhos com hash esperado vs observado;
- sem dados brutos do cliente.

## Notas operacionais

- **Performance:** hashear árvores grandes a cada start pode ser caro; restrinja a lista ou agende execução.
- **Extensões:** módulos nativos podem residir em `site-packages`; hasheie o **artefato instalado** resolvido em runtime, não só `pro/*.pyd` na árvore de fontes.
- **Assinatura:** manifestos “known-good” devem ser **assinados** ou distribuídos por canal confiável do operador (fora do escopo deste texto).

## Relacionados

- [RELEASE_INTEGRITY.pt_BR.md](RELEASE_INTEGRITY.pt_BR.md) ([EN](RELEASE_INTEGRITY.md))
