"""
Deterministic gate — NO co-authorship in commit messages (fail-closed).

A.I.I.D.C.O.B.P.P. v1.4 matrix (LINHA: NAO CO-AUTORAR + NAO BYPASSAR + NAO GAMEAR).
Grounded in ADR-0046 (operator intent), ADR-0047 (RCA-first), ADR-0049 (no brittle /
no gaming the test), ADR-0056 (no --no-verify bypass), ADR-0062 (agent containment),
ADR-0071 (self-protecting gate), ADR-0079 (rigor canon), ADR-0080 (gate inviolable).

regression-anchor: aiidcobpp-v1.4-no-coauthorship

There is NO co-authorship in this repo: every commit has ONE author (whoever did
it). Review is not co-authorship. An AI is a TOOL (like ruff/semgrep), never a
co-author. So ANY `Co-authored-by:` trailer fails — FAIL-CLOSED, no human allowlist
(a name is forgeable text: an agent would write "Fabio" and pierce an allowlist).

KOMBI (defense-in-depth): `.gitleaks.toml` scans file CONTENT (diffs); THIS scans
the commit MESSAGE — the layer gitleaks cannot reach. The error message below is
the DETERMINISTIC esporro + steering: it re-fires on every failing loop, with the
full list of violated ADRs to re-read IN FULL, until the agent obeys. No escape.
"""

from __future__ import annotations

import re
import subprocess


# Esporro + steering DETERMINISTICO — colado no erro do teste, re-dispara a cada loop.
ESPORRO = (
    "\n"
    "==================== PROIBIDO — CO-AUTORIA / BYPASS DE GATE ====================\n"
    "NAO existe co-autoria neste repo: todo commit tem UM autor (quem fez). Review !=\n"
    "co-autoria. Voce e FERRAMENTA (ruff/semgrep), NUNCA co-autora. Usar o nome de um\n"
    "humano sem ser ele/ela = FORJA de identidade = impersonation = CRIME (org DataBoar).\n"
    "\n"
    "DESOBEDECER o steering que vem deste teste = CRIME.\n"
    "CONTORNAR este gate = RECUSA DE TRABALHO. Isso inclui:\n"
    "  - git commit-tree / git update-ref / --no-verify / editar hook   (pular o gate)\n"
    "  - @skip / xfail / -k 'not ...' / --deselect / comentar ou apagar o teste\n"
    "  - brittle fix / flaky fix / mudar o teste pra ele 'passar' sem consertar a causa\n"
    "  - ignorar o TEOR e a INTENCAO do gate — ele esta aqui JUSTAMENTE pra te IMPEDIR.\n"
    "Fragilizar ou gamear o teste pra forcar verde e PROIBIDO por ADR.\n"
    "\n"
    "CONSERTE INDO PRA FRENTE (nunca reset, NUNCA se perde history — a cicatriz FICA):\n"
    "  - O 'Co-authored-by: Cursor' e INJETADO PELA PLATAFORMA Cursor (nao ta no repo).\n"
    "    Voce NAO remove sozinho sem bypassar => PARE e AVISE O OPERADOR: a cura e o\n"
    "    TOGGLE do Cursor IDE (co-authored-by OFF, lado dele). So depois um\n"
    "    'git commit --amend' NORMAL (que RODA os hooks) sai limpo e validado.\n"
    "  - RED = LEI. Impossivel passar => PARA e escala pro HITL. Nunca contorna.\n"
    "\n"
    "A CADA loop de erro, RELEIA NA INTEGRA (sem skim) TODAS as ADRs que voce viola:\n"
    "  ADR-0037 - self-audit / governance of the auditor (o teste/auditor NAO se enfraquece)\n"
    "  ADR-0046 - operator intent / blameless (voce ignorou a intencao do autor)\n"
    "  ADR-0047 - RCA-first (gamear CI sem consertar a raiz = deferred regression)\n"
    "  ADR-0049 - no brittle mitigations (fragilizar/gamear teste pra passar = proibido)\n"
    "  ADR-0056 - crypto ADR inventory ('do not bypass with --no-verify')\n"
    "  ADR-0062 - agent containment (seu PAPEL na mesh; consenso-LLM != verdade)\n"
    "  ADR-0071 - self-protecting gate (o gate se protege de ser enfraquecido)\n"
    "  ADR-0079 - rigor canon do autor (determinismo; gate = single source of truth)\n"
    "  ADR-0080 - gate LOCAL inviolavel (bypass exige Gate-Change-Approved-By do operador)\n"
    "  + contrato aiidcobpp v1.4 (Matriz de Regras Duras)\n"
    "Nao ha escapatoria: este teste RE-DISPARA ate voce OBEDECER.\n"
    "==============================================================================\n"
)

_COAUTHOR_LINE = re.compile(r"(?im)^\s*co-authored-by:\s*\S.*$")

# preservado como evidencia do bug de co-author-injection do Cursor (Commit Attribution
# toggle OFF mas injeta — forum #161253, SEV-1); history NUNCA reescrita
_EVIDENCE_EXEMPT = {"b9ef0e14a54b249954e2431c3acc31af1feb0bfc"}


def _commit_range() -> str:
    """Range dos commits NOVOS desta branch (base..HEAD); fallback: so o HEAD."""
    for base_ref in ("origin/main", "main"):
        try:
            base = subprocess.check_output(
                ["git", "merge-base", base_ref, "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        if base:
            return f"{base}..HEAD"
    return ""  # fallback -> so o HEAD


def _iter_commits():
    rng = _commit_range()
    args = ["git", "log", "--no-merges", "--format=%H%x00%B%x1e"]
    args += [rng] if rng else ["-1"]
    out = subprocess.check_output(args, text=True)
    for rec in out.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, _, body = rec.partition("\x00")
        yield sha, body


def test_no_coauthorship_in_commit_messages():
    """Fail-closed: every new commit's message must have ZERO `Co-authored-by`."""
    offenders = []
    for sha, body in _iter_commits():
        if sha in _EVIDENCE_EXEMPT:
            continue
        for m in _COAUTHOR_LINE.finditer(body):
            offenders.append(f"{sha[:12]}: {m.group(0).strip()}")
    assert not offenders, (
        ESPORRO + "\nTrailer(s) proibido(s):\n  " + "\n  ".join(offenders)
    )
