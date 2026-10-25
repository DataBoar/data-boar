param(
    [string]$TodayDate = "",
    [switch]$IncludeCommits = $false,
    [string]$OutputMarkdown = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($TodayDate)) {
    $TodayDate = (Get-Date).ToString("yyyy-MM-dd")
}

function Get-WindowCommits {
    param([string]$SinceExpr)
    $out = git log --since="$SinceExpr" --pretty=format:"%h|%ad|%s" --date=short
    if ([string]::IsNullOrWhiteSpace($out)) { return @() }
    return @($out -split "`n" | Where-Object { $_ -match "\|" })
}

function Get-Front {
    param([string]$Subject)
    $s = $Subject.ToLowerInvariant()
    if ($s -match "feat\(|fix\(|detector|api|report|connector") { return "product" }
    if ($s -match "security|hardening|audit|aide|lynis|usbguard|zero trust|least privilege") { return "security_integrity" }
    if ($s -match "^docs|readme|compliance|decision-maker|brief|legal|pt_br|pt-br|locale") { return "docs_compliance" }
    if ($s -match "ops|workflow|lab-op|homelab|today-mode|carryover|script|automation|cursor") { return "ops_workflow" }
    if ($s -match "plan|plans|roadmap|milestone|pmo") { return "plans_governance" }
    return "other"
}

function Summarize-Window {
    param([string]$Label, [array]$Lines, [switch]$EmitObject)

    $rows = @()
    foreach ($line in $Lines) {
        $parts = $line.Split("|", 3)
        if ($parts.Count -lt 3) { continue }
        $rows += [PSCustomObject]@{
            Sha = $parts[0]
            Date = $parts[1]
            Subject = $parts[2]
            Front = Get-Front -Subject $parts[2]
        }
    }

    $counts = @{}
    foreach ($k in @("product","security_integrity","docs_compliance","ops_workflow","plans_governance","other")) {
        $counts[$k] = 0
    }
    foreach ($r in $rows) { $counts[$r.Front]++ }

    Write-Host "=== $Label ==="
    Write-Host "Total commits: $($rows.Count)"
    Write-Host ("- product: {0}" -f $counts["product"])
    Write-Host ("- security_integrity: {0}" -f $counts["security_integrity"])
    Write-Host ("- docs_compliance: {0}" -f $counts["docs_compliance"])
    Write-Host ("- ops_workflow: {0}" -f $counts["ops_workflow"])
    Write-Host ("- plans_governance: {0}" -f $counts["plans_governance"])
    Write-Host ("- other: {0}" -f $counts["other"])

    if ($IncludeCommits) {
        Write-Host ""
        foreach ($r in $rows) {
            Write-Host ("  {0} | {1} | {2}" -f $r.Sha, $r.Date, $r.Subject)
        }
    }
    Write-Host ""

    if ($EmitObject) {
        return [PSCustomObject]@{
            Label = $Label
            Total = $rows.Count
            Product = $counts["product"]
            SecurityIntegrity = $counts["security_integrity"]
            DocsCompliance = $counts["docs_compliance"]
            OpsWorkflow = $counts["ops_workflow"]
            PlansGovernance = $counts["plans_governance"]
            Other = $counts["other"]
        }
    }
}

$todayLines = Get-WindowCommits -SinceExpr "$TodayDate 00:00"
$threeDayLines = Get-WindowCommits -SinceExpr "3 days ago"
$sevenDayLines = Get-WindowCommits -SinceExpr "7 days ago"

$sToday = Summarize-Window -Label "today ($TodayDate)" -Lines $todayLines -EmitObject
$s3 = Summarize-Window -Label "last 3 days" -Lines $threeDayLines -EmitObject
$s7 = Summarize-Window -Label "last 7 days" -Lines $sevenDayLines -EmitObject

if (-not [string]::IsNullOrWhiteSpace($OutputMarkdown)) {
    $dir = Split-Path -Parent $OutputMarkdown
    if (-not [string]::IsNullOrWhiteSpace($dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $now = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $lines = @()
    $lines += "# Progress snapshot"
    $lines += ""
    $lines += "- Generated at: $now"
    $lines += "- Today anchor: $TodayDate"
    $lines += ""
    $lines += "| Window | Total | product | security_integrity | docs_compliance | ops_workflow | plans_governance | other |"
    $lines += "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    foreach ($s in @($sToday, $s3, $s7)) {
        $lines += "| $($s.Label) | $($s.Total) | $($s.Product) | $($s.SecurityIntegrity) | $($s.DocsCompliance) | $($s.OpsWorkflow) | $($s.PlansGovernance) | $($s.Other) |"
    }
    $lines += ""
    $lines += "## Notes"
    $lines += ""
    $lines += "- Category split is keyword-based and intentionally conservative."
    $lines += "- Use this as operational signal, not as legal/accounting evidence."
    Set-Content -Path $OutputMarkdown -Value ($lines -join "`n") -Encoding utf8
    Write-Host "Markdown snapshot written: $OutputMarkdown"
}
