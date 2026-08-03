## Description
Brief description of the change and why it is needed.

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactor / maintenance
- [ ] Other (describe):

## Issue linking (required)

GitHub **only** auto-closes issues that appear with a closing keyword in the **merge commit / PR body**.
A bare `#NNN`, “refs”, or “related” does **not** close. Putting `(#NNN)` at the **end of the PR title** is usually the **PR number** after squash-merge — not an issue.

Use **one issue per line** (comma-separated lists are unreliable — e.g. `Closes #1133, #1134` may only close the first):

```text
Closes #NNNN
```

If this PR must **not** close any issue (docs index, partial slice, epic child, tracking-only):

```text
No issue closed: <one-line reason>
```

- [ ] This PR links the issue with `Closes #NNNN` **or** documents `No issue closed:` above

## 🧱 Checklist de Integridade
- [ ] **Python:** `uv run pytest` e `uv run ruff check .` sem erros.
- [ ] **Rust Core:** `cargo clippy --locked` passou no motor nativo.
- [ ] **Performance:** Validei que o benchmark não caiu abaixo de **0.574x**.
- [ ] **Drift Doc:** O `README.pt_BR.md` reflete as mudanças atuais (LCM nível 1).
- [ ] **Léxico:** Verifiquei se não há "anglicismos sintáticos" ou traduções artificiais.
