param(
    [Parameter(Mandatory = $true)]
    [string]$CandidatePdfPath,
    [string]$OutputDir = "docs/private/commercial/candidates",
    [switch]$LowPriorityCaution,
    [switch]$AdvisorRemote,
    [string]$OperatorRelationship = "",
    [switch]$Overwrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-SafeSlug {
    param([Parameter(Mandatory = $true)][string]$Name)
    $normalized = $Name.ToLowerInvariant()
    $normalized = $normalized -replace "[^a-z0-9]+", "-"
    $normalized = $normalized.Trim("-")
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        throw "Could not generate a safe slug from candidate name."
    }
    return $normalized
}

function Write-FileIfAllowed {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    if ((Test-Path -LiteralPath $Path) -and -not $Overwrite) {
        throw "File already exists: $Path. Use -Overwrite to replace."
    }
    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
}

function Get-OperatorRelationshipTag {
    param(
        [Parameter(Mandatory = $true)][string]$CandidateName,
        [string]$ExplicitOperatorRelationship
    )
    if (-not [string]::IsNullOrWhiteSpace($ExplicitOperatorRelationship)) {
        return $ExplicitOperatorRelationship.Trim().ToUpperInvariant()
    }

    return "NOT_DOCUMENTED"
}

function Get-OperatorRelationshipEvidence {
    param(
        [Parameter(Mandatory = $true)][string]$CandidateName,
        [Parameter(Mandatory = $true)][string]$RelationshipTag,
        [string]$ExplicitOperatorRelationship
    )
    if (-not [string]::IsNullOrWhiteSpace($ExplicitOperatorRelationship)) {
        return "Manual override via -OperatorRelationship."
    }
    if ($RelationshipTag -eq "NOT_DOCUMENTED") {
        return "No explicit relationship marker in source file name."
    }
    return "No explicit relationship provided."
}

$resolvedPdfPath = [System.IO.Path]::GetFullPath($CandidatePdfPath)
if (-not (Test-Path -LiteralPath $resolvedPdfPath)) {
    throw "Candidate PDF not found: $resolvedPdfPath"
}

$candidateName = [System.IO.Path]::GetFileNameWithoutExtension($resolvedPdfPath)
$slug = Get-SafeSlug -Name $candidateName

$resolvedOutputDir = [System.IO.Path]::GetFullPath($OutputDir)
if (-not (Test-Path -LiteralPath $resolvedOutputDir)) {
    New-Item -ItemType Directory -Path $resolvedOutputDir | Out-Null
}

$enPath = Join-Path $resolvedOutputDir "$slug.md"
$ptPath = Join-Path $resolvedOutputDir "$slug.pt_BR.md"

$date = Get-Date -Format "yyyy-MM-dd"
$priorityMode = if ($LowPriorityCaution) { "LOW_PRIORITY_CAUTION" } else { "STANDARD" }
$collaborationMode = if ($AdvisorRemote) { "REMOTE_ADVISOR" } else { "STANDARD_ENGAGEMENT" }
$operatorRelationshipTag = Get-OperatorRelationshipTag -CandidateName $candidateName -ExplicitOperatorRelationship $OperatorRelationship
$operatorRelationshipEvidence = Get-OperatorRelationshipEvidence -CandidateName $candidateName -RelationshipTag $operatorRelationshipTag -ExplicitOperatorRelationship $OperatorRelationship
$enCautionBlock = if ($LowPriorityCaution) {
@"

## 0) Priority posture and caution mode

- Priority posture: **LOW PRIORITY** (do not rely on this profile by default for critical-path execution).
- If selected for a job, apply **extra monitoring** on delivery quality, cadence, and acceptance criteria.
- Required guardrail: assign an explicit reviewer/owner for weekly deliverable validation.
"@
} else {
@"

## 0) Priority posture and caution mode

- Priority posture: **STANDARD**.
- Apply normal quality gates and role-fit checks.
"@
}
$ptCautionBlock = if ($LowPriorityCaution) {
@"

## 0) Postura de prioridade e modo de cautela

- Postura de prioridade: **BAIXA PRIORIDADE** (não contar com este perfil por padrão para trilha crítica).
- Se entrar em um trabalho, aplicar **monitoramento reforçado** de qualidade de entrega, cadência e critérios de aceite.
- Guardrail obrigatório: definir revisor/dono explícito para validação semanal de entregáveis.
"@
} else {
@"

## 0) Postura de prioridade e modo de cautela

- Postura de prioridade: **PADRÃO**.
- Aplicar gates normais de qualidade e checagem de encaixe de papel.
"@
}
$enAdvisorBlock = if ($AdvisorRemote) {
@"

## 0.1) Collaboration mode (remote/advisor)

- Collaboration mode: **REMOTE_ADVISOR**.
- Default scope: reviewer/advisor contributions (events, tips, experience, recommendations), not on-site customer execution.
- Guardrail: avoid workload that competes with the candidate's primary career obligations.
- Escalation rule: if customer-facing/on-site need appears, require explicit operator approval before assignment.
"@
} else {
@"

## 0.1) Collaboration mode (remote/advisor)

- Collaboration mode: **STANDARD_ENGAGEMENT**.
"@
}
$ptAdvisorBlock = if ($AdvisorRemote) {
@"

## 0.1) Modo de colaboração (remoto/conselheiro)

- Modo de colaboração: **REMOTE_ADVISOR**.
- Escopo padrão: contribuição como revisor(a)/conselheiro(a) (eventos, dicas, experiências, recomendações), sem execução presencial em cliente.
- Guardrail: evitar carga que concorra com a carreira principal da pessoa candidata.
- Regra de escalonamento: se surgir demanda presencial/customer-facing, exigir aprovação explícita do operador antes de alocar.
"@
} else {
@"

## 0.1) Modo de colaboração (remoto/conselheiro)

- Modo de colaboração: **STANDARD_ENGAGEMENT**.
"@
}
$enRelationshipBlock = @"

## 0.2) Operator relationship and history control

- Operator relationship tag: **$operatorRelationshipTag**
- Relationship evidence source: $operatorRelationshipEvidence
- Rule: if relationship is not explicitly documented, keep as `NOT_DOCUMENTED` and avoid assumptions.
"@
$ptRelationshipBlock = @"

## 0.2) Controle de vinculo e historico com o operador

- Tag de vinculo com o operador: **$operatorRelationshipTag**
- Fonte da evidencia de vinculo: $operatorRelationshipEvidence
- Regra: se o vinculo nao estiver explicitamente documentado, manter como `NOT_DOCUMENTED` e evitar suposicoes.
"@

$enTemplate = @"
# Candidate dossier — $candidateName

> CONFIDENTIAL (private workspace only). Generated on $date by scripts/candidate-dossier-scaffold.ps1.
> Priority mode: **$priorityMode**
> Collaboration mode: **$collaborationMode**
$enCautionBlock
$enAdvisorBlock
$enRelationshipBlock

## 1) Source and confidence

- Source PDF: `$resolvedPdfPath`
- Currency assumption: almost up-to-date (operator input)
- Confidence notes: [fill]

## 2) Executive profile

- Seniority/trajectory: [fill]
- Core domains: [fill]
- Language fit: [fill]
- Relevant credentials: [fill]

## 3) Strategic strengths (go-to-market leverage)

| Strength | Practical leverage for offers |
| -------- | ----------------------------- |
| [fill] | [fill] |

## 4) Watchouts and mitigations

| Watchout | Mitigation |
| -------- | ---------- |
| [fill] | [fill] |

## 5) Fit by engagement archetype

| Archetype | Recommended role | Not recommended |
| --------- | ---------------- | --------------- |
| Lean | [fill] | [fill] |
| Governance-heavy | [fill] | [fill] |
| Delivery-heavy | [fill] | [fill] |

## 6) 30/60/90-day integration plan

- 30 days: [fill]
- 60 days: [fill]
- 90 days: [fill]

## 7) Commercial implications

- Pricing impact: [fill]
- Margin risk: [fill]
- Packaging guidance: [fill]

## 8) Next actions

- [ ] Validate assumptions with candidate conversation.
- [ ] Align role split against <lead-1>/<lead-2>/core technical lead.
- [ ] Update offer archetypes and proposal language.
"@

$ptTemplate = @"
# Dossiê de candidato — $candidateName

> CONFIDENCIAL (somente workspace privado). Gerado em $date por scripts/candidate-dossier-scaffold.ps1.
> Modo de prioridade: **$priorityMode**
> Modo de colaboração: **$collaborationMode**
$ptCautionBlock
$ptAdvisorBlock
$ptRelationshipBlock

## 1) Fonte e confiança

- PDF de origem: `$resolvedPdfPath`
- Premissa de atualização: quase atualizado (entrada do operador)
- Observações de confiança: [preencher]

## 2) Perfil executivo

- Senioridade/trajetória: [preencher]
- Domínios centrais: [preencher]
- Idiomas e comunicação: [preencher]
- Credenciais relevantes: [preencher]

## 3) Forças estratégicas (alavancas de go-to-market)

| Força | Alavancagem prática nas ofertas |
| ----- | ------------------------------- |
| [preencher] | [preencher] |

## 4) Pontos de atenção e mitigação

| Atenção | Mitigação |
| ------- | --------- |
| [preencher] | [preencher] |

## 5) Encaixe por arquétipo de oferta

| Arquétipo | Papel recomendado | Não recomendado |
| --------- | ----------------- | --------------- |
| Enxuto | [preencher] | [preencher] |
| Governança-pesada | [preencher] | [preencher] |
| Entrega-pesada | [preencher] | [preencher] |

## 6) Plano de integração 30/60/90 dias

- 30 dias: [preencher]
- 60 dias: [preencher]
- 90 dias: [preencher]

## 7) Implicações comerciais

- Efeito em precificação: [preencher]
- Risco de margem: [preencher]
- Diretriz de empacotamento: [preencher]

## 8) Próximas ações

- [ ] Validar premissas com conversa com o candidato.
- [ ] Alinhar split de papeis com <lead-1>/<lead-2>/lideranca tecnica.
- [ ] Atualizar arquétipos de oferta e linguagem de proposta.
"@

Write-FileIfAllowed -Path $enPath -Content $enTemplate
Write-FileIfAllowed -Path $ptPath -Content $ptTemplate

Write-Host "Created dossier templates:"
Write-Host " - $enPath"
Write-Host " - $ptPath"
