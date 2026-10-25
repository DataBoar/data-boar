# Espelho GitLab do GitHub (espelho só leitura, uma fonte da verdade)

**English:** [GITLAB_GITHUB_MIRROR.md](GITLAB_GITHUB_MIRROR.md)

## 1. Para que serve

- O **GitHub** é o **único** lugar onde as pessoas abrem PR e fazem merge (histórico canônico).
- O **GitLab** guarda um **espelho só leitura** do mesmo repositório Git (mesmos commits e tags).
- **Objetivos:** redundância extra, **segundo CI** opcional no GitLab, visibilidade em outro host — **sem** dois históricos a divergir.

**Não é objetivo:** duplicar Issues, discussões ou fluxo de PR no GitLab, salvo se decidirem isso mais tarde.

---

## 2. Pré-requisitos

| Item                  | Notas                                                                                                                             |
| ----                  | -----                                                                                                                             |
| Repositório no GitHub | Existe; tens **Admin** (ou direitos para secrets / webhooks se precisares).                                                       |
| GitLab                | Projeto vazio ou descartável na conta/grupo (ex.: **data-boar**), mesmo nome de branch padrão que no GitHub (normalmente `main`). |
| Decisão               | Escolher **uma** forma de sincronização abaixo (A ou B). **Não** configurar os dois a empurrar em sentidos opostos.               |

---

## 3. Opção A — GitLab puxa do GitHub (recomendado para “ligar e esquecer”)

O GitLab **busca** periodicamente (ou sob gatilho) a partir do GitHub. Ninguém faz push manual para o GitLab.

### 3.1 Passos manuais (interface GitLab)

1. Abrir o **projeto GitLab** (repo vazio, mesmo nome de branch que no GitHub).
1. Ir a **Definições → Repositório → Espelhamento de repositórios** (o caminho exato pode variar por versão do GitLab).
1. **Adicionar espelho:**
   - **URL do repositório Git:** URL HTTPS do repo GitHub, ex.: `<https://github.com/><org>/<repo>.git`
   - **Direção do espelho:** **Pull** (puxar)
   - **Autenticação:** usar um **Personal Access Token (classic)** do GitHub com scope **`repo`** (só leitura basta para repo **público**; **privado** precisa de acesso).
1. Guardar. Usar **“Atualizar agora”** / **“Sincronizar”** uma vez para testar.
1. Definir **intervalo** do espelho, se existir (ex.: alguns minutos), ou depender de sincronização manual + webhook opcional (GitHub → GitLab), conforme o plano do GitLab.

### 3.2 Token do GitHub (repo privado)

1. GitHub → **Definições → Definições de programador → Tokens de acesso pessoal**.
1. Criar token com pelo menos **`repo`** (leitura) para esse repositório.
1. **Nunca** commitar o token. Colar só no campo de credenciais do espelho no GitLab ou em secrets do GitHub Actions.

### 3.3 Trancar o GitLab contra push humano (recomendado)

1. **Definições → Repositório → Branches protegidos:** proteger `main` (e branches de release) para **ninguém** poder fazer push exceto **Maintainers** — ou restringir push a **nenhum** papel e confiar só no espelho (depende da edição do GitLab; no mínimo desativar **Permitido fazer push** para Developers).
1. **Definições → Geral → Visibilidade:** ajustar (muitas vezes espelho **privado** de GitHub público é aceitável).

---

## 4. Opção B — GitHub Actions empurra para o GitLab

Cada push na `main` do GitHub corre um workflow que faz **push** dos refs para o GitLab.

### 4.1 Lado GitLab

1. Criar **Deploy key** (read-write só nesse repo) **ou** **Project Access Token** com **`write_repository`**.
1. Adicionar a chave pública em **Definições → Repositório → Deploy keys** (SSH), **ou** usar token HTTPS no CI.
1. Manter proteção de branch alinhada com “só espelho” (igual §3.3).

### 4.2 Lado GitHub

1. Repositório → **Definições → Secrets and variables → Actions**.
1. Adicionar secrets, por exemplo:
   - `GITLAB_SSH_PRIVATE_KEY` (se push por SSH), **ou**
   - `GITLAB_USERNAME` + `GITLAB_TOKEN` (se push por HTTPS).
1. Adicionar arquivo de workflow (ex.: `.github/workflows/mirror-to-gitlab.yml`) que corre em `push` à `main` e executa `git push gitlab main` (e tags se quiserem). **Não** colar secrets no YAML; só `${{ secrets.* }}`.

**Nota:** o workflow concreto é outro commit; este documento descreve **o que** configurar. Pedir ao assistente ou mantenedor um workflow mínimo quando os secrets estiverem prontos.

---

## 5. Qual opção escolher

| Situação                                        | Preferir                                                    |
| --------                                        | ---------                                                   |
| Mudanças mínimas no GitHub                      | **A (pull no GitLab)**                                      |
| Espelho quase imediato após cada push no GitHub | **B (push por Actions)** ou **A + webhook** (se disponível) |
| Evitar guardar PAT do GitHub no GitLab          | **B** (só o GitLab recebe pushes)                           |

---

## 6. CI duplo (GitHub Actions + GitLab CI)

- **Possível:** os dois correm nos mesmos commits depois do espelho atualizado.
- **Custo:** minutos duplicados, secrets duplicados (Sonar, tokens de teste, etc.).
- **Recomendação:** primeiro estabilizar o espelho; ativar **`.gitlab-ci.yml`** só quando houver disposição para manter **paridade** com os workflows do GitHub (ou um **subconjunto** de jobs).

---

## 7. Verificação (sem secrets no chat)

1. Depois do sync, comparar o **SHA do commit** na `main` do GitHub e na `main` do GitLab (deve ser igual).
1. Comparar a **última tag** se espelharem tags (alguns espelhos precisam de **“espelhar todos os refs”** ou job separado para tags).

---

## 8. Homelab / lab-op (opcional)

- **Não é obrigatório** para espelhar: GitHub e GitLab tratam do sync na cloud.
- **Opcional:** script na LAN (ou job CI agendado) que **compara** URLs `git ls-remote` e alerta se os SHAs divergirem além de N minutos — útil como **saúde**, não como mecanismo principal de sync.

---

## 9. Resolução de problemas

| Sintoma                       | Verificar                                                                                                                 |
| -------                       | ---------                                                                                                                 |
| Espelho falha na autenticação | Scope do token, expiração, 2FA, listas de IP.                                                                             |
| GitLab vazio                  | Nome de branch padrão diferente (`main` vs `master`).                                                                     |
| Drift                         | Alguém fez push no GitLab; remover permissão de escrita; reset do projeto GitLab a partir do GitHub uma vez (mantenedor). |

---

## 10. Documentos relacionados

- [REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md) — hábitos locais de `git remote`; o espelho **não** substitui o `origin` nas máquinas de desenvolvimento.
- [COMMIT_AND_PR.md](COMMIT_AND_PR.md) — o fluxo de PR continua no GitHub.

---

## 11. Política de bloqueio forte (baseline anti-caos)

Aplicar estes controles no GitLab para ele não virar fonte alternativa de verdade:

1. **Desativar push direto** na branch padrão para qualquer papel humano abaixo de Maintainer.
1. Proteger `main` e definir:
   - **Allowed to merge:** apenas Maintainers (ou sem merge se o projeto for só espelho),
   - **Allowed to push:** ninguém além da identidade de automação do espelho.
1. **Desativar force push** em branches protegidas.
1. Desativar ou restringir **edição via web IDE** e **pipelines manuais em refs arbitrários**, quando possível.
1. Manter projeto **Private** salvo política explícita de espelho público.
1. Usar conta/token dedicado para escrita do espelho e girar periodicamente.
1. Desativar Issues/MRs se o repositório for estritamente espelho + CI.

Se algum item não for suportado no teu tier do GitLab, registar controle compensatório no runbook privado.

---

## 12. Arquitetura recomendada (safe default)

- **GitHub:** fonte da verdade, PR, merge, release, tags.
- **GitLab:** espelho + pipeline adicional opcional.
- **Sem caminho de escrita humana** para branch padrão no GitLab.
- **Sem espelhamento bidirecional.**

Fluxo:

1. Humano faz merge no GitHub.
1. Espelho atualiza GitLab (pull ou push por Actions).
1. GitLab CI roda checks extras não bloqueantes.
1. Achados retornam ao GitHub como issue/comentário ou nota privada de operação.

---

## 13. Verificação de saúde do espelho (script)

Usar `scripts/gitlab-mirror-health-check.ps1` para comparar SHA de `origin/main` e do espelho no GitLab:

```powershell
.\scripts\gitlab-mirror-health-check.ps1 -GitLabRepoUrl "git@gitlab.com:<grupo>/<repo>.git"
```

Você pode usar uma janela de tolerância opcional antes de alertar.
