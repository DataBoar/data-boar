# Varredura de desktops Windows por SMB: receita e modelo de medição (Fase 0)

**English:** [WINDOWS_DESKTOP_SMB_SCAN_RECIPE.md](WINDOWS_DESKTOP_SMB_SCAN_RECIPE.md)

> **Status: RASCUNHO SEM MEDIÇÕES.** Nenhum piloto foi executado. Toda afirmação sobre o
> comportamento em escala é uma **hipótese a confirmar ou refutar**. Não cite capacidade, duração
> nem "suporta N máquinas" a partir desta página. Plano: `docs/plans/PLAN_ENDPOINT_AGENT.md`
> (issue #2207).

## Objetivo

Alcançar desktops Windows que expõem um compartilhamento, usando o conector SMB existente,
**uma instância do Data Boar por VLAN**, e descobrir quanto isso custa antes de alguém desenhar um
agente de endpoint.

## Topologia

```text
Desktops VLAN 10  <--SMB-->  Instância Data Boar 10  --\
Desktops VLAN 20  <--SMB-->  Instância Data Boar 20  ---+--> revisão por instância
Desktops VLAN 30  <--SMB-->  Instância Data Boar 30  --/    (ver MULTI_INSTANCE_FINDINGS_CSV_POC.pt_BR.md)
```

## Configuração do alvo (uma entrada por máquina ou compartilhamento)

As chaves vêm do conector SMB e do `docs/USAGE.md`:

```yaml
- name: "desktop-piloto-001"
  type: smb
  host: "pc-001.corp.example"
  share: "C$"               # ou um compartilhamento dedicado; ver a hipótese de acesso abaixo
  path: "Users"
  user: "<conta de serviço>"
  pass: "<definida pelo tratamento de segredos do projeto, nunca um literal em arquivo versionado>"
  domain: "CORP"
  port: 445
  recursive: true
  allow_private_networks: true   # hosts RFC1918 exigem esta autorização (#1715); sem ela o SMB os recusa
```

## Hipóteses a testar (NÃO são fatos)

| # | Hipótese | Como testar | Resultado |
| - | -------- | ----------- | --------- |
| H1 | Exige conta com acesso administrativo em cada máquina (ou um compartilhamento dedicado por máquina) | Tentar uma conta de serviço somente leitura contra um compartilhamento administrativo e contra um dedicado | não medido |
| H2 | Máquinas desligadas ou fora da rede não são alcançadas | Contar hosts inalcançáveis por execução | não medido |
| H3 | Leituras em massa podem disparar alertas de proteção de endpoint | Combinar com a equipe de segurança antes da execução; registrar os alertas | não medido |
| H4 | Escala e tempo total são desconhecidos | Registrar as métricas abaixo | não medido |

## Protocolo do piloto (20 a 50 máquinas)

1. Obtenha aprovação por escrito dos responsáveis por desktops e segurança; escolha uma janela
   fora do horário comercial.
2. Escolha de 20 a 50 máquinas representativas (mistura de idade de hardware e perfil de usuário);
   nenhum dado de produção sai do local e os findings ficam só com metadados.
3. Rode uma instância para a VLAN do piloto; registre o início e o fim de cada alvo.
4. Preencha a tabela abaixo **a partir da saída da execução**, não de memória. Deixe "n/a" onde
   não foi capturado.
5. Pare imediatamente diante de qualquer impacto visível ao usuário ou de pedido da segurança.

## Modelo de medição (preencher após o piloto)

| Métrica | Valor | Como foi capturada |
| ------- | ----- | ------------------ |
| Máquinas-alvo | | |
| Máquinas alcançadas | | |
| Inalcançáveis, por causa (desligada, firewall, credenciais, outra) | | |
| Tempo por máquina (mediana, pior caso) | | |
| Tempo total da VLAN | | |
| Dados lidos por máquina (mediana, pior caso) | | |
| Carga de rede durante a execução (pico) | | |
| Findings por máquina (só metadados) | | |
| Falhas, por causa | | |
| Alertas de proteção de endpoint gerados | | |
| Impacto visível ao usuário relatado | | |

## Decisão que esta receita alimenta

Se o piloto mostrar que o caminho SMB é aceitável para uma classe de ambientes, documente aqui o
formato suportado com os números medidos. Se não for, isso é a evidência para a Fase 1 (agente de
endpoint) do plano. Qualquer um dos resultados é válido; uma afirmação sem medição não é.
