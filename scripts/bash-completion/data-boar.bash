# Data Boar Bash completion for published console scripts (#1952).
# Source from a clone after ``uv sync`` (see docs/TECH_GUIDE.md — Bash tab completion).
# Completes documented flags only; never expands scan targets or executes commands.

_data_boar_complete() {
  local cur prev
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  local flags="
    --version --check-extras --demo --config --web --port --host
    --https-cert-file --https-key-file --allow-insecure-http --reset-data
    --reconcile-integrity-anchor --confirm-upgrade-to --export-audit-trail
    --validate-config --plan --resume --prefilter-status --diff --fail-on-new-high
    --export-dsar --dsar-output --dsar-include-samples --export-l1 --l1-output
    --export-findings-sink --allow-sample-export --export-l3 --l3-grant --l3-persist
    --l3-column --l3-max-rows --l3-allow-unprotected --session
    --export-remediation-manifest --regenerate-report --governance-report
    --tenant --technician --scan-compressed --content-type-check --scan-stego
    --jurisdiction-hint --validate-crypto --progress --no-progress --help -h
  "
  COMPREPLY=( $(compgen -W "${flags}" -- "$cur") )
}

_data_boar_report_complete() {
  local cur prev
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  local formats="md docx pdf xlsx heatmap dsar json audit-trail all"
  local flags="
    --config --session-id --format --output --output-dir --sqlite
    --trial-rows-capped --dsar-include-samples --debug-traceback --help -h -o
  "
  case "$prev" in
    --format)
      COMPREPLY=( $(compgen -W "${formats}" -- "$cur") )
      return
      ;;
  esac
  COMPREPLY=( $(compgen -W "${flags}" -- "$cur") )
}

complete -F _data_boar_complete data-boar
complete -F _data_boar_report_complete data-boar-report
complete -F _data_boar_report_complete data-boar-xlsx
complete -F _data_boar_report_complete data-boar-pdf
complete -F _data_boar_report_complete data-boar-docx
complete -F _data_boar_report_complete data-boar-heatmap
complete -F _data_boar_report_complete data-boar-dsar
complete -F _data_boar_report_complete data-boar-audit
