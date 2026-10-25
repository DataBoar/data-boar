# Detecção de dados de menores: configuração e ajuste fino

A aplicação pode detectar quando os dados coletados podem se referir a **menores de idade** (por exemplo, idade ou data de nascimento em colunas) e tratá-los com **máxima sensibilidade**, com tratamento diferenciado nos relatórios (LGPD Art. 14, GDPR Art. 8). Esta página descreve como **configurar e ajustar** a funcionalidade pelo **arquivo de configuração externo**, sem alterar código da aplicação.

**English:** [MINOR_DETECTION.md](MINOR_DETECTION.md)

---

## O que é detectado

- **Nomes de colunas** que sugerem data de nascimento ou idade, em **inglês e português brasileiro**, incluindo siglas (ex.: DOB, DDN, NASC, idade, age).
- **Valores amostrados**: idades numéricas (ex.: `17`) ou datas que, interpretadas como data de nascimento, impliquem idade abaixo do **limite** configurável (padrão **18**). Esses achados são sinalizados como **possível dado de menor** (`DOB_POSSIBLE_MINOR`) e recebem uma recomendação de alta prioridade no relatório.

O racional de desenho e tabelas históricas de nomes de coluna estão no plano arquivado **`PLAN_MINOR_DATA_DETECTION`** em `docs/plans/completed/` (no checkout; sem link daqui neste guia ao operador).

---

## Arquivo de config: onde e o quê

O **limite de idade menor/maior de idade** é definido no **arquivo de configuração principal** (ex.: `config.yaml` ou o arquivo indicado por `CONFIG_PATH`). Não é necessário alterar código.

| Chave                             | Tipo     | Padrão    | Descrição                                                                                                                                                                                                                                                                                                                                                                                                           |
| ---                               | ---      | ---       | ---                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `detection.minor_age_threshold`   | inteiro  | **18**    | Idade abaixo deste valor (inclusive) é tratada como possível menor. Use ex.: 21 se sua política tratar pessoas com menos de 21 anos como menores.                                                                                                                                                                                                                                                                   |
| `detection.minor_full_scan`       | booleano | **false** | Quando **true**, apenas para **bancos de dados**: se a amostra da coluna sugerir possível menor (DOB_POSSIBLE_MINOR), o conector reamostra essa coluna com um limite maior (`minor_full_scan_limit`) e roda a detecção de novo. Se o achado continuar como possível menor, ele é salvo (opcionalmente com norm_tag “(full-scan confirmed)”). **Opcional; padrão desligado** para não sobrecarregar tabelas grandes. |
| `detection.minor_full_scan_limit` | inteiro  | **100**   | Número máximo de valores a buscar quando `minor_full_scan` é true. Ignorado quando `minor_full_scan` é false.                                                                                                                                                                                                                                                                                                       |
| `detection.minor_cross_reference` | booleano | **true**  | Quando true, o gerador de relatório cruza achados de possível menor com outros achados na **mesma tabela** (banco) ou **mesmo caminho** (sistema de arquivos). Se a mesma tabela/caminho tiver dado identificador ou de saúde (ex.: nome, CPF/RG/SSN, saúde), as linhas de possível menor recebem **Minor confidence** = **“high (cross-ref)”** e uma recomendação específica de alta confiança é adicionada.       |

Se a seção **`detection`** for **omitida**, o limite permanece **18** e a aplicação se comporta como antes (sem erros). Incluir a seção permite ajustar o limite sem quebrar execuções existentes.

---

## Como ajustar e refinar

### 1. Usar o padrão (18)

Não faça nada: omita a seção `detection`. Qualquer pessoa com menos de 18 anos (por idade ou inferida pela data de nascimento) será sinalizada como possível menor.

### 2. Aumentar o limite (ex.: política under-21)

Se sua organização trata pessoas com menos de 21 anos como menores, defina o limite em 21 no arquivo de config:

```yaml
# config.yaml
targets: []
report:
  output_dir: .
sqlite_path: audit_results.db

detection:
  minor_age_threshold: 21
```

Em seguida execute a auditoria como de costume (`python main.py --config config.yaml` ou pela API). Colunas que pareçam de idade/DOB com valores que indiquem idade &lt; 21 serão sinalizadas como possível menor.

### 3. Reduzir o limite (ex.: apenas crianças pequenas)

Para sinalizar apenas idades bem baixas (ex.: menores de 14), defina:

```yaml
detection:
  minor_age_threshold: 14
```

### 4. Exemplo completo com outras opções

```yaml
targets:

- name: meu-banco

    type: database
    host: localhost
    database: app_db
    # ...
file_scan:
  extensions: [.csv, .xlsx, .txt]
  recursive: true
report:
  output_dir: ./reports
  min_sensitivity: LOW

# Opcional: possível dado de menor (LGPD Art. 14, GDPR Art. 8)
detection:
  minor_age_threshold: 18   # padrão; altere para 21 (ou outro) se necessário
  minor_full_scan: false    # opcional: reamostrar coluna com minor_full_scan_limit quando DOB sugerir menor (padrão off)
  minor_full_scan_limit: 100  # máx. linhas na passada de full-scan (apenas banco)
  minor_cross_reference: true # coluna Minor confidence e recomendação de alta confiança quando mesma tabela/path tem identificador/saúde

sqlite_path: audit_results.db
scan:
  max_workers: 1
```

---

## Nomes e formatos de coluna reconhecidos

O detector procura nomes de coluna (e conteúdo amostrado) que indiquem **DOB ou idade**. Nomes reconhecidos incluem:

| Conceito           | Inglês                               | Português brasileiro                           | Siglas                  |
| ---                | ---                                  | ---                                            | ---                     |
| Data de nascimento | date of birth, birth date, birthdate | data de nascimento, nascimento, data de nasc.  | DOB, DDN, DN, NASC, DTN |
| Idade              | age, person age                      | idade, idade_atual, idade_pessoa, faixa etária | AGE, IDD                |

**Formatos de data** no texto amostrado: `dd/mm/yyyy`, `yyyy-mm-dd`, `mm/dd/yyyy` (e variantes comuns). **Idade numérica**: inteiros na amostra (ex.: 0–120) quando o nome da coluna sugere idade.

Se o nome da coluna **não** sugerir DOB ou idade, um valor como `17` ou uma data na amostra **não** dispara sozinho o possível-menor (evita falsos positivos em colunas genéricas numéricas/de data).

---

## Cruzamento e coluna “Minor confidence”

Quando **`detection.minor_cross_reference`** está **true** (padrão), o gerador de relatório agrupa achados por **tabela** (banco) ou **caminho** (sistema de arquivos). Em cada grupo, se houver pelo menos um achado com **DOB_POSSIBLE_MINOR** e pelo menos um achado que pareça **identificador ou de saúde** (ex.: nome, CPF/RG/SSN, coluna ou padrão de saúde), todos os achados de possível menor desse grupo recebem **Minor confidence** = **“high (cross-ref)”** nas abas **Database findings** e **Filesystem findings**. Nesse caso, uma **linha extra de recomendação** é adicionada no topo da aba **Recommendations**: “DOB_POSSIBLE_MINOR (high confidence – cross-ref)”, explicando que a mesma tabela/arquivo contém DOB sugerindo menor e dado identificador/saúde, e deve ser tratado com alta prioridade pelo DPO. Defina **`minor_cross_reference: false`** para desativar e deixar a coluna Minor confidence vazia.

---

## Varredura completa (opcional, apenas banco de dados)

Quando **`detection.minor_full_scan`** está **true**, os conectores de **banco de dados** (PostgreSQL, MySQL, SQLite, etc.) passam a fazer o seguinte: após a amostra pequena usual da coluna ser escaneada, se o resultado indicar **DOB_POSSIBLE_MINOR**, o conector busca até **`minor_full_scan_limit`** valores (padrão **100**) dessa mesma coluna e roda a detecção novamente. Se o achado continuar como possível menor, ele é salvo; o **norm_tag** pode incluir “(full-scan confirmed)” para indicar que uma amostra maior foi usada. Isso é **opcional** e **desligado por padrão** para não impactar desempenho em tabelas grandes. Sistema de arquivos e outros tipos de alvo não fazem essa segunda passada.

---

## Relatório e recomendações

Achados sinalizados como possível menor recebem:

- **Sensibilidade:** HIGH
- **Padrão:** `DOB_POSSIBLE_MINOR` (possivelmente combinado com outros padrões)
- **Norm tag:** LGPD Art. 14 – possível dado de menor; GDPR Art. 8 (e “(full-scan confirmed)” quando a varredura completa foi usada)
- **Minor confidence:** “high (cross-ref)” quando o cruzamento encontrou identificador/saúde na mesma tabela/caminho; caso contrário vazio

No relatório Excel, a aba **Recommendations** inclui uma linha dedicada a possível dado de menor com **prioridade máxima** (CRÍTICA) e texto de tratamento diferenciado (consentimento, armazenamento, uso, compartilhamento, responsabilidade dos pais). Essa linha aparece **em primeiro** na aba de Recomendações. Quando o cruzamento identifica casos de alta confiança, uma linha adicional “DOB_POSSIBLE_MINOR (high confidence – cross-ref)” aparece no topo. Veja o código do gerador de relatório para o texto exato.

---

## Documentação relacionada

- **Índice da documentação** (todos os tópicos, ambos os idiomas): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
- Plano arquivado **`PLAN_MINOR_DATA_DETECTION`** em `docs/plans/completed/` — desenho histórico e checklist de conclusão (mantenedores).
- [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) ([EN](SENSITIVITY_DETECTION.md)) – Detecção de sensibilidade ML/DL e regex.
- [USAGE.pt_BR.md](USAGE.pt_BR.md) ([EN](USAGE.md)) – Configuração geral e uso da API.
