# =============================================================================
# ATS / Pool de Talentos -- atalhos globais (adicionar ao $PROFILE do PowerShell)
# =============================================================================
# Adicione ao seu perfil PowerShell:
#   code $PROFILE   (ou notepad $PROFILE)
#   . "C:\Users\<username>\Documents\dev\data-boar\scripts\ats-profile.ps1"
# Ou inclua direto com:
#   Add-Content $PROFILE '. "C:\path\to\scripts\ats-profile.ps1"'
# =============================================================================

$AtsRepoRoot = "C:\Users\<username>\Documents\dev\data-boar"
$AtsScript   = "$AtsRepoRoot\scripts\ats.ps1"
$LAB-ROUTER-01Script   = "$AtsRepoRoot\scripts\LAB-ROUTER-01.ps1"

# --- Funcao principal: ats ---
function ats {
    param(
        [Parameter(Position=0)] [string]$Command = "help",
        [Parameter(Position=1)] [string]$Arg1 = "",
        [Parameter(Position=2)] [string]$Arg2 = "",
        [switch]$Force,
        [switch]$JsonOnly
    )
    $args2 = @($Command)
    if ($Arg1)    { $args2 += $Arg1 }
    if ($Arg2)    { $args2 += $Arg2 }
    if ($Force)   { $args2 += "-Force" }
    if ($JsonOnly){ $args2 += "-JsonOnly" }
    powershell -ExecutionPolicy Bypass -File $AtsScript @args2
}

# --- Funcao LAB-ROUTER-01 ---
function LAB-ROUTER-01 {
    param(
        [Parameter(Position=0)] [string]$Command = "status",
        [string]$ApiKey = ""
    )
    $args2 = @($Command)
    if ($ApiKey) { $args2 += "-ApiKey"; $args2 += $ApiKey }
    powershell -ExecutionPolicy Bypass -File $LAB-ROUTER-01Script @args2
}

# --- Atalhos curtissimos ---
function ats-import    { ats import $args[0] }
function ats-scan      { ats scan $args[0] }
function ats-list      { ats list }
function ats-show      { ats show $args[0] }
function pool          { ats list }                    # alias: pool
function LAB-ROUTER-01-scan      { LAB-ROUTER-01 scan }
function LAB-ROUTER-01-clients   { LAB-ROUTER-01 clients }
function LAB-ROUTER-01-wifi      { LAB-ROUTER-01 wifi }

# --- Funcao de ajuda rapida ---
function ats-help {
    Write-Host @"
Atalhos ATS disponiveis:

  ats import <pdf>    Importar PDF de candidato
  ats import-all      Importar todos PDFs novos
  ats scan <nome>     Extrair dados de PDF (JSON)
  ats list / pool     Listar todos os candidatos
  ats show <nome>     Ver ATS de um candidato
  ats linkedin <slug> Abrir LinkedIn no browser
  ats LAB-ROUTER-01             Status do LAB-ROUTER-01
  ats LAB-ROUTER-01-scan        Scan completo da rede LAB-ROUTER-01
  LAB-ROUTER-01-clients         Lista clientes conectados na rede
  LAB-ROUTER-01-wifi            Lista redes Wi-Fi
"@ -ForegroundColor Cyan
}

Write-Host "[ATS+LAB-ROUTER-01] Atalhos carregados. Digite 'ats-help' para ver os comandos." -ForegroundColor DarkCyan
