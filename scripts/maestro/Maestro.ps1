#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Maestro.ps1

.SYNOPSIS
 Orquestrador Central Agnóstico e inteligente do Lab-Op. [cite: 0]

.DESCRIPTION
 Controla sub-orquestradores baseando atividades nas Personas possíveis. [cite: 1]
 Parametrizado pelo inventory.json escondido em docs/private/homelab/data. [cite: 8]
 Aceita o parâmetro -Ref para testes de versões efêmeras, operando a wrking Tree por padrão. [cite: 14]
 Precisamos buscar liçoes aprendidas [cite: 10]
#>

param(
    [string]$Ref = "WorkingTree",
    [switch]$Collect, # <--- NOVA FLAG SRE
    [switch]$Deep     # <--- NOVA FLAG PARA TESTES RC
)

# 1. Localização do Inventário Privado (Zero PII no código)[cite: 8, 14, 16]
$inventoryPath = "$PSScriptRoot/../../docs/private/homelab/data/inventory.json"

# [cite: 1, 8]
if (-not (Test-Path $inventoryPath)) {
    Write-Error "ERRO: Inventário privado não encontrado em $inventoryPath"
    exit 1
}

# 2. Carregamento dos dados do Lab-Op [cite: 8, 16]
$inventory = Get-Content $inventoryPath | ConvertFrom-Json
Write-Host "--- [Maestro] Iniciando Turno no Lab-Op (Ref: $Ref) ---" -ForegroundColor Cyan

# SRE FIX: Fase de Pre-flight Global (Evita build redundante)
if (-not $Collect) {
    & "$PSScriptRoot/Build-ContainerArtefact.ps1"
}

# 3. Processamento dos Membros do Laboratório
$globalReport = foreach ($node in $inventory.lab_members) {

    # Pre-flight Check: Injetando PII via argumentos (Agnosticismo)[cite: 14, 16]
    $status = & "$PSScriptRoot/Get-LabStatus.ps1" -TargetHost $node.hostname -TargetUser $node.user

    # SRE FIX: Se estivermos apenas coletando (-Collect), NÃO dispare a orquestração de novo!
    if ($status.SSH -eq "UP" -and -not $Collect) {

        # Sincronismo da Árvore de Arquivos
        # Inteligente: Prepara o terreno (WorkingTree ou Pasta Efêmera)
        & "$PSScriptRoot/Sync-WorkingTree.ps1" -Node $node -Ref $Ref

        # SRE FIX: Condicional rígida para Deploy de Container
        $isContainerHost = ($node.personas -contains "docker") -or ($node.personas -contains "podman") -or ($node.personas -contains "dockerswarm")
        if ($isContainerHost) {
            & "$PSScriptRoot/Sync-ContainerArtefact.ps1" -Node $node
        }

        # Despacho para Handlers baseados em Persona [cite: 1]
        foreach ($persona in $node.personas) {
            $handler = "$PSScriptRoot/handlers/Handle-$persona.ps1"

            if (Test-Path $handler) {
                # O Node contém o path atualizado pelo Sync-WorkingTree (Injeção de Contexto) [cite:1]
		# PowerShell exige que você cole o valor no nome do parâmetro usando dois pontos (:), sem espaços!
		# Assim ele não vai achar no Handler que tem uma variável sobrando sem motivo (ex: sshfs, nfs, etc.)
		& $handler -Node $node -Ref $Ref -Deep:$Deep
            }
        }
    }

    $status # Acumula para o relatório final [cite: 10]
}

# 4. --- [Fase de Coleta SRE] ---
if ($Collect) {
    Write-Host "`n--- [Maestro] Iniciando Coleta de Artefatos (Post-Flight) ---" -ForegroundColor DarkCyan

    foreach ($node in $inventory.lab_members) {
        if ($node.personas -contains "baremetal" -or $node.personas -contains "docker" -or $node.personas -contains "podman" -or $node.personas -contains "target_sshfs" -or $node.personas -contains "target_nfs") {
             & "$PSScriptRoot/Collect-Artifacts.ps1" -Node $node
        }
    }

    # Prepara o Template para o Cursor atuar
    $templatePath = "$PSScriptRoot/../../docs/private/homelab/COMPLETAO_SESSION_TEMPLATE.pt_BR.md"
    $newSessionPath = "$PSScriptRoot/../../docs/private/homelab/reports/COMPLETAO_SESSION_$(Get-Date -Format 'yyyy-MM-dd').md"

    if ((Test-Path $templatePath) -and -not (Test-Path $newSessionPath)) {
        Copy-Item $templatePath $newSessionPath
        Write-Host "   [Docs] Template instanciado em: $newSessionPath" -ForegroundColor Magenta
    }
}

# 5. Relatório Final Consolidado (Feedback Visual SRE) [cite: 10, 16]
Write-Host "`n--- [Status Final do Lab-Op] ---" -ForegroundColor Cyan
$globalReport | Format-Table -AutoSize
