<#
.SYNOPSIS
    Abre perfis LinkedIn de candidatos no browser em lote ou individualmente.
    Quando o Cursor tiver browser autenticado, use junto com o agente de IA
    para enriquecer os arquivos ATS com dados ao vivo.

.PARAMETER Names
    Lista de apelidos de candidatos (separados por virgula). Padrao: todos.

.PARAMETER Delay
    Delay em segundos entre abertura de cada perfil. Padrao: 3.

.PARAMETER Top
    Abrir apenas os N primeiros da lista.

.EXAMPLE
    # Abrir um apelido do pool (exemplo):
    .\scripts\linkedin-review-batch.ps1 -Names "candidate_a"

    # Abrir top 5 candidatos prioritarios:
    .\scripts\linkedin-review-batch.ps1 -Top 5

    # Abrir todos (com delay de 5s):
    .\scripts\linkedin-review-batch.ps1 -Delay 5
#>

param(
    [string]$Names = "",
    [int]$Delay = 3,
    [int]$Top = 0
)

# Mapa minimo tracked + carga opcional do pool privado
$pool = [ordered]@{
    "example"      = "example"
}

$repoRoot = Split-Path $PSScriptRoot -Parent
$privatePoolPath = Join-Path $repoRoot "docs\private\commercial\linkedin_review_pool.json"
if (Test-Path -LiteralPath $privatePoolPath) {
    try {
        $privatePool = Get-Content -Raw -LiteralPath $privatePoolPath | ConvertFrom-Json -AsHashtable
        foreach ($k in $privatePool.Keys) {
            $pool[$k] = [string]$privatePool[$k]
        }
    } catch {
        Write-Warning "Falha ao carregar pool privado em '$privatePoolPath': $($_.Exception.Message)"
    }
}

# Filtrar candidatos
$selected = if ($Names) {
    $nameList = $Names -split "," | ForEach-Object { $_.Trim().ToLower() }
    $pool.GetEnumerator() | Where-Object { $_.Key -in $nameList }
} else {
    $pool.GetEnumerator()
}

if ($Top -gt 0) { $selected = $selected | Select-Object -First $Top }

Write-Host "Abrindo $(@($selected).Count) perfis LinkedIn..." -ForegroundColor Cyan
Write-Host "Delay entre perfis: ${Delay}s" -ForegroundColor Gray
Write-Host ""
Write-Host "INSTRUCAO PARA O AGENTE:" -ForegroundColor Yellow
Write-Host "  Apos abrir os perfis, use no Cursor:" -ForegroundColor Yellow
Write-Host "  'Revise o LinkedIn de [nome] e atualize o ATS com os dados ao vivo'" -ForegroundColor Yellow
Write-Host ""

$i = 0
foreach ($entry in $selected) {
    $i++
    $slug = [string]$entry.Value
    $url = "https://www.example.com/profile/redacted"
    Write-Host "[$i/$(@($selected).Count)] Abrindo: $($entry.Key) -> $url"
    Start-Process $url
    if ($i -lt @($selected).Count) { Start-Sleep -Seconds $Delay }
}

Write-Host ""
Write-Host "Concluido. $i perfis abertos no browser." -ForegroundColor Green
Write-Host "Dica: Use 'ats show [nome]' para ver o ATS atual de cada candidato." -ForegroundColor Cyan
