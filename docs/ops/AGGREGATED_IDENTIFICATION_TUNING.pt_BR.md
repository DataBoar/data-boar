# Ajuste de identificação agregada (guia prático da Fase C)

Este runbook ajuda operadores a ajustar o comportamento de identificação agregada em condições reais de scan, especialmente quando a cobertura é parcial ou quando há categorias de alto arrependimento.

Referência de base: [../SENSITIVITY_DETECTION.pt_BR.md](../SENSITIVITY_DETECTION.pt_BR.md#identificação-agregada-configuração-e-exemplos)

---

## Objetivo rápido

Escolher um perfil de configuração que equilibre:

- **Recall** (capturar possíveis situações de reidentificação)
- **Ruído** (quantidade de linhas de revisão sugerida para triagem)
- **Realidade da cobertura** (dataset completo vs janelas amostradas/incrementais)

---

## Perfis práticos

### Perfil A: Linha de base conservadora (padrão)

Use quando os scans são amplos e a capacidade de revisão é limitada.

```yaml
detection:
  aggregated_identification_enabled: true
  aggregated_min_categories: 2
  aggregated_incomplete_data_mode: false
  aggregated_single_high_risk_suggested_review: false
```

Comportamento esperado:

- Saída estável e conservadora.
- Menos linhas MEDIUM de revisão sugerida.

### Perfil B: Scans com cobertura parcial

Use para datasets amostrados, janelas curtas de data ou rollout por etapas de conectores.

```yaml
detection:
  aggregated_identification_enabled: true
  aggregated_min_categories: 2
  aggregated_incomplete_data_mode: true
  aggregated_single_high_risk_suggested_review: false
```

Comportamento esperado:

- O limiar efetivo de categorias cai em 1 (mínimo 1).
- Melhor recall com evidência incompleta, com aumento moderado de ruído.

### Perfil C: Contexto de saúde com alto arrependimento

Use quando perder sinais potenciais de reidentificação ligados a saúde é mais custoso do que revisar casos extras.

```yaml
detection:
  aggregated_identification_enabled: true
  aggregated_min_categories: 2
  aggregated_incomplete_data_mode: true
  aggregated_single_high_risk_suggested_review: true
```

Comportamento esperado:

- Categoria única `health` ainda pode aparecer como MEDIUM de revisão sugerida.
- Maior recall, maior carga de triagem.

---

## Mini exemplos de evidência (comportamento do Cross-ref por perfil)

Estes exemplos mostram como a saída da aba Cross-ref pode mudar quando os toggles são ajustados.

### Exemplo 1: extrato amostrado de RH (gênero + cargo; sem coluna de saúde na amostra)

- Categorias observadas na amostra: `gender`, `job_position`
- Configuração declarada: `aggregated_min_categories: 2`

| Perfil                            | Resultado esperado no Cross-ref                     | Motivo                                                                        |
| ---                               | ---                                                 | ---                                                                           |
| A (padrão)                        | Linha aparece (contexto MEDIUM de revisão sugerida) | Duas categorias atingem o limiar mínimo.                                      |
| B (modo incompleto)               | Linha aparece (igual ao A)                          | O modo incompleto não reduz limiar que já foi atingido.                       |
| C (incompleto + alto risco único) | Linha aparece (igual ao A/B)                        | A regra de alto risco único não é necessária quando o limiar já foi atingido. |

### Exemplo 2: extrato amostrado de clínica (apenas sinal de saúde encontrado)

- Categorias observadas na amostra: somente `health`
- Configuração declarada: `aggregated_min_categories: 2`

| Perfil                            | Resultado esperado no Cross-ref | Motivo                                                  |
| ---                               | ---                             | ---                                                     |
| A (padrão)                        | Sem linha                       | Uma categoria fica abaixo do limiar.                    |
| B (modo incompleto)               | Linha aparece                   | O limiar efetivo cai em 1 (de 2 para 1).                |
| C (incompleto + alto risco único) | Linha aparece                   | Também satisfaz a regra de saúde como alto risco único. |

### Exemplo 3: execução com política estrita (`aggregated_min_categories: 3`) e duas categorias detectadas

- Categorias observadas na amostra: `address`, `phone`

| Perfil                            | Resultado esperado no Cross-ref | Motivo                                                                |
| ---                               | ---                             | ---                                                                   |
| A (padrão)                        | Sem linha                       | Duas categorias < limiar estrito (3).                                 |
| B (modo incompleto)               | Linha aparece                   | O limiar efetivo vira 2, agora atendido.                              |
| C (incompleto + alto risco único) | Linha aparece (igual ao B)      | O modo incompleto já é suficiente; alto risco único não é necessário. |

---

## Fluxo operacional (recomendado)

1. Rode um scan base com o Perfil A.
1. Se a cobertura for parcial, rode novamente com o Perfil B.
1. Se o risco de domínio for alto (forte presença de saúde), avalie o Perfil C.
1. Compare os deltas no relatório:
   - total de linhas Cross-ref
   - total de linhas MEDIUM de revisão sugerida
   - tempo de análise humana
1. Mantenha o perfil com menor ruído que ainda capture os riscos esperados.

---

## Política de rollout sugerida

- Comece com Perfil A em ambientes tipo produção.
- Ative Perfil B por alvo quando a cobertura de dados for sabidamente parcial.
- Ative Perfil C apenas para alvos de alto arrependimento e registre o motivo nas notas do scan/log de mudança.

---

## Dicas de troubleshooting

- Ruído alto: desative primeiro `aggregated_single_high_risk_suggested_review` e reavalie.
- Poucos achados com dados amostrados: ative `aggregated_incomplete_data_mode`.
- Mapeamento de categoria inesperado: revise regras customizadas em `detection.quasi_identifier_mapping`.
