#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run_schemathesis.sh — Run Schemathesis contract tests against any REST API
#
# Usage:
#   bash ~/.agents/skills/ticket-to-tests/tools/run_schemathesis.sh
#   bash ~/.agents/skills/ticket-to-tests/tools/run_schemathesis.sh "/items/{itemId}"
#
# Environment variables:
#   BASE_URL     e.g. https://api.example.com  (required)
#   API_TOKEN    Bearer token (optional)
#   OPENAPI_SPEC Path to OpenAPI spec (overrides team_config.yaml)
#   AUTH_TYPE    "bearer" | "basic" | "apikey" (default: bearer)
#   AUTH_HEADER  Custom header for API key auth (e.g. X-API-Key)
#
# Reads from team_config.yaml (CWD) if available:
#   openapi.spec_path
# ---------------------------------------------------------------------------
set -euo pipefail

REPORT_DIR="schemathesis-reports"

_DEFAULT_SPEC=""
if command -v python3 &>/dev/null && [[ -f "team_config.yaml" ]]; then
    _DEFAULT_SPEC=$(python3 - <<'PY'
import yaml, sys
try:
    cfg = yaml.safe_load(open("team_config.yaml"))
    print(cfg.get("openapi", {}).get("spec_path", ""))
except Exception:
    print("")
PY
)
fi

SPEC="${OPENAPI_SPEC:-${_DEFAULT_SPEC}}"

if [[ -z "${SPEC:-}" ]]; then
    echo "ERROR: OpenAPI spec path is not set."
    echo "Set OPENAPI_SPEC=<path> or configure openapi.spec_path in team_config.yaml."
    exit 2
fi

if [[ ! -f "$SPEC" ]]; then
    echo "ERROR: Spec file not found: $SPEC"
    exit 2
fi

if [[ -z "${BASE_URL:-}" ]]; then
    echo "ERROR: BASE_URL is not set."
    echo "Set it: export BASE_URL=https://api.example.com"
    exit 2
fi

AUTH_TYPE="${AUTH_TYPE:-bearer}"
AUTH_ARGS=()

if [[ -n "${API_TOKEN:-}" ]]; then
    case "$AUTH_TYPE" in
        bearer)  AUTH_ARGS=(--auth-type bearer --auth "$API_TOKEN") ;;
        basic)   AUTH_ARGS=(--auth "$API_TOKEN") ;;
        apikey)  HEADER="${AUTH_HEADER:-X-API-Key}"
                 AUTH_ARGS=(--header "$HEADER: $API_TOKEN") ;;
        *)       echo "WARNING: Unknown AUTH_TYPE '$AUTH_TYPE'. Running without auth." ;;
    esac
else
    echo "WARNING: API_TOKEN is not set. Running without authentication."
fi

PATH_FILTER="${1:-}"
if [[ -n "$PATH_FILTER" ]]; then
    FILTER_ARGS=(--include-path "$PATH_FILTER")
    echo "Path filter: $PATH_FILTER"
else
    FILTER_ARGS=()
    echo "Path filter: all paths"
fi

mkdir -p "$REPORT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JUNIT_FILE="$REPORT_DIR/schemathesis_${TIMESTAMP}.xml"

echo "Spec:     $SPEC"
echo "Base URL: $BASE_URL"
echo "Report:   $JUNIT_FILE"
echo ""

schemathesis run "$SPEC" \
    --base-url "$BASE_URL" \
    "${AUTH_ARGS[@]}" \
    "${FILTER_ARGS[@]}" \
    --checks all \
    --stateful=links \
    --max-response-time=30000 \
    --junit-xml "$JUNIT_FILE" \
    --show-errors-tracebacks \
    --validate-schema true

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo ""
    echo "Schemathesis: all checks passed. Report: $JUNIT_FILE"
else
    echo ""
    echo "Schemathesis: FAILURES detected. Review $JUNIT_FILE for details."
fi

exit $EXIT_CODE
