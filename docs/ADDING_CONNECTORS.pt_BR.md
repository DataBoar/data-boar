# Como adicionar um novo conector

Este guia explica como adicionar um novo conector de fonte de dados ao **Data Boar**, para que alvos de um novo tipo (por exemplo Snowflake, uma API customizada ou outro banco) possam ser escaneados a partir do `config.yaml` e incluídos no mesmo fluxo de relatórios Excel/heatmap.

**English:** [ADDING_CONNECTORS.md](ADDING_CONNECTORS.md)

---

## 1. Onde os conectores se encaixam

- **Config:** Cada entrada em `targets` tem pelo menos `name`, `type` e campos específicos do tipo (ex.: `host`, `database`, `base_url`).
- **Registro:** Os conectores registram um **type** (e opcionalmente um **driver** para `type: database`) em `core.connector_registry`.
- **Resolução:** Para cada alvo, `connector_for_target(target)` retorna a classe do conector a usar. Para `type: database`, o **driver** (ex.: `postgresql+psycopg2`) é normalizado para um nome de engine (ex.: `postgresql`) e consultado no registro.
- **Engine:** `AuditEngine._run_target()` instancia o conector com `(target_config, scanner, db_manager)` (mais kwargs opcionais para filesystem/shares), e então chama `connector.run()`.

Um conector deve:

1. Implementar uma classe com **`run(self)`** que executa a varredura.
1. Usar **`self.scanner`** (ex.: `scan_column(column_name, sample_text)`) para detecção de sensibilidade.
1. Reportar resultados via **`self.db_manager.save_finding(...)`** e falhas via **`self.db_manager.save_failure(...)`**.
1. Opcionalmente implementar **`connect()`** e **`close()`** para o ciclo de vida da conexão; **`run()`** deve chamá-los (ex.: conectar no início, fechar em um bloco `finally`).

---

## 2. Contrato do conector (resumo)

| Exigência                   | Descrição                                                                                                                                                                                                                 |
| ---                         | ---                                                                                                                                                                                                                       |
| **Construtor**              | `__init__(self, target_config, scanner, db_manager, **kwargs)`. Para conectores de banco/API o engine só passa esses três; para filesystem e shares pode passar também `extensions`, `scan_sqlite_as_db`, `sample_limit`. |
| **`run()`**                 | Ponto de entrada. Conectar, descobrir/amostrar, chamar `scanner.scan_column(name, sample)`, depois `db_manager.save_finding(...)` ou `save_failure(...)`. Fechar recursos ao terminar.                                    |
| **`connect()` / `close()`** | Opcional, mas recomendado. Usar em `run()` para liberar conexões.                                                                                                                                                         |
| **Achados**                 | Usar `save_finding(source_type="database", ...)` para fontes tipo banco; `save_finding(source_type="filesystem", ...)` para arquivo/share; `save_finding(source_type="application", ...)` (ou `api`/`crm`/`saas`) para REST/CRM — planilha **Application findings**. |
| **Falhas**                  | Usar `save_failure(target_name, reason, details)` quando o alvo for inacessível ou houver erro.                                                                                                                           |

---

## 3. Passo a passo

### Passo 1: Criar o módulo do conector

Crie um novo arquivo em `connectors/`, por exemplo `connectors/snowflake_connector.py`.

- Implemente uma classe (ex.: `SnowflakeConnector`) com:
- `__init__(self, target_config, scanner, db_manager, sample_limit=5)` (compatível com a chamada do engine para conectores tipo banco).
- `connect()` – criar client/engine a partir de `target_config`.
- `close()` – descartar engine/fechar client.
- `run()` – chamar `connect()`, descobrir/amostrar, chamar `scanner.scan_column(...)`, chamar `db_manager.save_finding(...)` ou `save_failure(...)`, e em um bloco `finally` chamar `close()`.

### Passo 2: Registrar o conector

No final do módulo (ou atrás de um guard de import opcional), chame:

```python
from core.connector_registry import register

register("snowflake", SnowflakeConnector, ["name", "type"])
```

O terceiro argumento é a lista de chaves de config que devem existir (ex.: para validação ou documentação). O engine não exige isso; é apenas para documentação.

- Para um **driver de banco:** registre o nome do engine (ex.: `snowflake`) para que alvos com `type: database` e `driver: snowflake+connector` resolvam para sua classe (veja “Mapeamento de target type para conector” abaixo).
- Para um **alvo não-banco** (ex.: API, share): registre o tipo que aparecerá em `target.type` (ex.: `api`, `rest`, `sharepoint`).

### Passo 3: Mapear tipo de alvo para o conector (se necessário)

- **`type: database`:** A resolução está em `connector_for_target()` em `core/connector_registry.py`. O driver é normalizado para um nome de engine (ex.: `snowflake+connector` → `snowflake`). Se você registrou `"snowflake"`, não é preciso alterar nada; a lógica existente o utilizará.
- **Novo tipo de primeiro nível (ex.: `type: snowflake`):** Adicione um ramo em `connector_for_target()`:

  ```python
  if t == "snowflake":
      try:
          return get_connector("snowflake")
      except KeyError:
          return None
  ```

  No config use então `type: snowflake` (e opcionalmente ainda suporte `type: database` + `driver: snowflake...` registrando `snowflake` como acima).

### Passo 4: Dependência opcional (recomendado para backends pesados ou raros)

Se o conector precisar de uma biblioteca que não está nas dependências padrão (ex.: `snowflake-connector-python`), adicione um extra opcional em `pyproject.toml`:

```toml
[project.optional-dependencies]
bigdata = ["snowflake-connector-python>=3.0"]
```

Instalação para o usuário:

```bash
uv pip install -e ".[bigdata]"
```

No módulo do conector, proteja a importação e o registro para a aplicação não falhar quando a dependência estiver ausente:

```python
try:
    import snowflake.connector
    _SNOWFLAKE_AVAILABLE = True
except ImportError:
    _SNOWFLAKE_AVAILABLE = False

class SnowflakeConnector:
    # ...

if _SNOWFLAKE_AVAILABLE:
    register("snowflake", SnowflakeConnector, ["name", "type"])
```

### Passo 5: Registrar o módulo no engine

Para que o conector seja carregado e se registre, importe-o em `core/engine.py`:

```python
try:
    import connectors.snowflake_connector  # noqa: F401
except ImportError:
    pass
```

Use try/except se o conector for opcional (dependência opcional); caso contrário um import simples basta.

### Passo 6: Documentar a forma do config e exemplo

No README (ou neste doc), inclua:

- Quais **pacotes** instalar (ex.: `.[bigdata]` ou `pip install snowflake-connector-python`).
- A **forma do target** em YAML: `type`, `name` e chaves obrigatórias/opcionais (ex.: `account`, `user`, `password`, `database`, `schema`, `warehouse`).
- Um **exemplo** mínimo em snippet.

---

## 4. Achados tipo database vs filesystem vs application

- **Fontes tipo banco** (tabelas e colunas): use `save_finding(source_type="database", ...)` e passe pelo menos:
- `target_name`, `server_ip` (ou host), `schema_name`, `table_name`, `column_name`, `data_type`
- `sensitivity_level`, `pattern_detected`, `norm_tag`, `ml_confidence`
- Outros campos de DB são opcionais mas úteis nos relatórios.

- **Fontes tipo filesystem / share** (caminhos locais, SMB, NFS, WebDAV): use `save_finding(source_type="filesystem", ...)` e passe:
- `target_name`, `path`, `file_name`, `data_type`
- `sensitivity_level`, `pattern_detected`, `norm_tag`, `ml_confidence`

- **Application / API / CRM / SaaS** (REST, HubSpot e similares; ERP no futuro): use `save_finding(source_type="application", ...)` (aliases: `api`, `crm`, `saas`) com o mesmo formato path-like (`path` + `file_name`), ex.: tipo de objeto CRM + propriedade, ou `GET /users | email`. Aparecem na planilha Excel **Application findings**, não em **Filesystem findings**.

O scanner retorna um dict com pelo menos `sensitivity_level`, `pattern_detected`, `norm_tag`, `ml_confidence`; repasse-os para `save_finding`. Ignore ou não reporte linhas com `sensitivity_level == "LOW"` se quiser manter o comportamento atual.

---

## 5. Exemplo: conector Snowflake (estilo database)

Abaixo está um padrão mínimo para um conector Snowflake que reutiliza o mesmo fluxo “descobrir → amostrar → scan_column → save_finding” do conector SQL. Você pode adaptá-lo ao seu driver e chaves de config.

```python
# connectors/snowflake_connector.py
"""Snowflake connector: opcional, requer snowflake-connector-python. Use type: database, driver: snowflake."""
from typing import Any

from core.connector_registry import register

try:
    import snowflake.connector
    from sqlalchemy import create_engine
    _SNOWFLAKE_AVAILABLE = True
except ImportError:
    _SNOWFLAKE_AVAILABLE = False
    snowflake = None

def _build_url(target: dict[str, Any]) -> str:
    account = target.get("account", "")
    user = target.get("user", "")
    password = target.get("pass", target.get("password", ""))
    database = target.get("database", "")
    schema = target.get("schema", "PUBLIC")
    warehouse = target.get("warehouse", "")
    # Montar URL no estilo SQLAlchemy ou usar parâmetros do connector; aqui simplificado.
    return f"snowflake://{user}:{password}@{account}/{database}/{schema}?warehouse={warehouse}"

class SnowflakeConnector:
    def __init__(self, target_config: dict[str, Any], scanner: Any, db_manager: Any, sample_limit: int = 5):
        self.config = target_config
        self.scanner = scanner
        self.db_manager = db_manager
        self.sample_limit = sample_limit
        self.engine = None
        self._connection = None

    def connect(self) -> None:
        if not _SNOWFLAKE_AVAILABLE:
            raise RuntimeError("snowflake-connector-python necessário. Instale com: pip install snowflake-connector-python")
        url = _build_url(self.config)
        self.engine = create_engine(url)
        self._connection = self.engine.connect()

    def close(self) -> None:
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def discover(self) -> list[dict[str, Any]]:
        """Retorna lista de {schema, table, columns: [{name, type}]}."""
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        result = []
        for schema in inspector.get_schema_names():
            for table in inspector.get_table_names(schema=schema):
                columns = inspector.get_columns(table, schema=schema)
                result.append({
                    "schema": schema or "",
                    "table": table,
                    "columns": [{"name": c["name"], "type": str(c["type"])} for c in columns],
                })
        return result

    def sample(self, schema: str, table: str, column_name: str) -> str:
        """Retorna amostra de valores da coluna como uma única string (não armazenada)."""
        from sqlalchemy import text
        quoted = f'"{schema}"."{table}"."{column_name}"' if schema else f'"{table}"."{column_name}"'
        q = text(f"SELECT {quoted} FROM {quoted.rpartition('.')[0]} LIMIT {self.sample_limit}")
        try:
            rows = self._connection.execute(q).fetchall()
            return " ".join(str(r[0])[:200] for r in rows if r[0] is not None)
        except Exception:
            return ""

    def run(self) -> None:
        target_name = self.config.get("name", "snowflake")
        try:
            self.connect()
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        try:
            for item in self.discover():
                schema = item["schema"]
                table = item["table"]
                for col in item["columns"]:
                    cname = col["name"]
                    ctype = col["type"]
                    sample = self.sample(schema, table, cname)
                    res = self.scanner.scan_column(cname, sample)
                    if res["sensitivity_level"] == "LOW":
                        continue
                    self.db_manager.save_finding(
                        source_type="database",
                        target_name=target_name,
                        server_ip=self.config.get("account", ""),
                        engine_details="snowflake",
                        schema_name=schema,
                        table_name=table,
                        column_name=cname,
                        data_type=ctype,
                        sensitivity_level=res["sensitivity_level"],
                        pattern_detected=res["pattern_detected"],
                        norm_tag=res.get("norm_tag", ""),
                        ml_confidence=res.get("ml_confidence", 0),
                    )
        except Exception as e:
            self.db_manager.save_failure(target_name, "error", str(e))
        finally:
            self.close()

if _SNOWFLAKE_AVAILABLE:
    register("snowflake", SnowflakeConnector, ["name", "type", "account", "user", "database"])
```

## Exemplo de config (`config.yaml`)

```yaml
targets:

- name: "Warehouse_LGPD"

    type: database
    driver: snowflake
    account: "xy12345.us-east-1"
    user: "AUDIT_USER"
    pass: "secret"
    database: "COMPLIANCE_DB"
    schema: "PUBLIC"
    warehouse: "AUDIT_WH"
```

Instale a dependência opcional:

```bash
uv pip install -e ".[bigdata]"
```

Em `core/connector_registry.py` adicione um fallback para `type: database` para que `driver: snowflake` (ou `snowflake+connector`) mapeie para a chave de registro `snowflake`. E em `core/engine.py`:

```python
try:
    import connectors.snowflake_connector  # noqa: F401
except ImportError:
    pass
```

---

## 6. Exemplo: conector REST/API (estilo filesystem)

Para uma API que retorna JSON, use achados **filesystem** e um único `run()` que busca endpoints, achata o JSON e chama `scan_column` em nomes de campo e valores amostrados. Veja `connectors/rest_connector.py` para o padrão completo:

- **Construtor:** `(target_config, scanner, db_manager, sample_limit=5)`.
- **Auth:** Leia `target_config["auth"]` (basic, bearer, oauth2_client, custom) e defina headers ou auth do client.
- **Descoberta:** paths fixos em config ou um `discover_url` que retorna uma lista de paths.
- **Por path:** GET, parse JSON, achatar em pares `(key, value)`, chamar `scanner.scan_column(key, value)`; se não for LOW, chamar `db_manager.save_finding("filesystem", target_name=..., path=..., file_name=f"GET {path} | {key}", ...)`.
- **Falhas:** `save_failure(target_name, "error", message)` em erros de conexão ou parse.
- **Dependência opcional:** Proteja com `try/import httpx` e registre apenas quando `httpx` estiver disponível.

Exemplo de config:

```yaml
targets:

- name: "API interna"

    type: api
    base_url: "https://api.example.com"
    auth:
      type: bearer
      token_from_env: "API_TOKEN"
    paths:

      - "/users"
      - "/orders"

```

---

## 7. Exemplo: conector HubSpot CRM (#1229)

CRM SaaS gerenciado (tier Pro). Descobre **todos** os nomes de propriedade (incluindo campos
customizados onde CPF/CNPJ costumam aparecer) e amostra objetos com paginação e backoff em 429.

- **Módulo:** `connectors/hubspot_connector.py`
- **Auth:** Private App Token via env (nunca commitar o token). Ver setup abaixo.
- **SSRF:** Todo HTTP de saída usa pin de host em `connectors/url_guard.py` (#1552) — mesma
  postura do conector REST.

### Criar o token de Private App (UI HubSpot, em 2026-08)

1. No HubSpot: **Settings → Integrations → Private Apps**.
   Se a UI tiver movido Private Apps para **Legacy Apps**, abra esse caminho e siga —
   o tipo de credencial continua sendo token de app **Private** (não app OAuth público).
2. Crie (ou abra) um app e escolha **Private** (não **Public**).
3. **Não** use **Service Key** no Data Boar. Service key é credencial ampla demais, sem os
   escopos CRM granulares que este conector espera.
4. Em escopos, marque **exatamente** estes seis escopos **.read** (sem write, sem webhooks):

   | Escopo | Para quê |
   | ------ | -------- |
   | `crm.objects.contacts.read` | Amostrar **valores** de propriedades de contato |
   | `crm.objects.companies.read` | Amostrar **valores** de propriedades de empresa |
   | `crm.objects.deals.read` | Amostrar **valores** de propriedades de negócio |
   | `crm.schemas.contacts.read` | Descobrir **nomes** de propriedades de contato (incl. custom) |
   | `crm.schemas.companies.read` | Descobrir **nomes** de propriedades de empresa (incl. custom) |
   | `crm.schemas.deals.read` | Descobrir **nomes** de propriedades de negócio (incl. custom) |

5. Gere o token e guarde só em variável de ambiente / cofre de segredos — nunca em YAML
   commitado.

**Least privilege:** o conector é **somente leitura e sob demanda** (sem webhooks HubSpot).
`crm.objects.*.read` devolve valores de campo; `crm.schemas.*.read` é obrigatório para a
**descoberta** de propriedades. Sem os escopos de schema, campos customizados (onde CPF/CNPJ
costumam ficar) nem entram na lista — e portanto nunca são amostrados (lacuna silenciosa).

> **O nome da env var tem que bater exatamente.** Por padrão o conector lê
> ``HUBSPOT_PRIVATE_APP_TOKEN`` (ou o nome em ``token_from_env`` /
> ``auth.token_from_env``). Um nome *parecido mas errado* (por exemplo ``HUBSPOT_ACCESS_TOKEN``)
> **não** gera erro claro de “variável errada”: o ``connect()`` roda, a API responde **401**,
> e não há findings — a maior fonte de atrito ao configurar este conector. Confirme o nome
> exportado antes de depurar escopos.

Exemplo de config:

```yaml
targets:
  - name: crm-hubspot
    type: hubspot
    objects: [contacts, companies, deals]
```

Chaves opcionais: `base_url` (padrão `https://api.hubapi.com`), `token_from_env`
(nome da env var), `allow_private_networks` (somente lab).

---

## 8. Checklist

- [ ] Novo módulo em `connectors/<nome>_connector.py`.
- [ ] Classe com `run()`, e opcionalmente `connect()`/`close()`.
- [ ] Uso de `self.scanner.scan_column(name, sample)` e `self.db_manager.save_finding(...)` / `save_failure(...)`.
- [ ] `register(<type>, <Class>, [required_config_keys])` (e mapeamento de driver em `connector_for_target` se for novo type ou driver).
- [ ] Dep opcional em `pyproject.toml` e guard de import + registro condicional.
- [ ] Import em `core/engine.py` (com try/except se opcional).
- [ ] README ou este doc: comando de instalação, forma do target no config, exemplo YAML.

Com isso, o novo conector passa a ser usado automaticamente para alvos correspondentes e aparece nos mesmos relatórios Excel e heatmap dos conectores existentes.

**Ver também:** Índice da documentação (todos os tópicos, ambos os idiomas): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md). [TOPOLOGY.pt_BR.md](TOPOLOGY.pt_BR.md) ([EN](TOPOLOGY.md)) — topologia da aplicação; [TECH_GUIDE.md](TECH_GUIDE.md) · [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md); [TESTING.pt_BR.md](TESTING.pt_BR.md) ([EN](TESTING.md)); [COMMIT_AND_PR.pt_BR.md](ops/COMMIT_AND_PR.pt_BR.md) ([EN](ops/COMMIT_AND_PR.md)); [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](COMPLIANCE_FRAMEWORKS.md)).
