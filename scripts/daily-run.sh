#!/usr/bin/env bash
# daily-run.sh - Daily paper-tracker pipeline runner (for cron)
# Schedule: Every day at 10:00 AM KST
#
# Usage: ./scripts/daily-run.sh

set -euo pipefail

PROJECT_DIR="/home/roachbot/.openclaw/workspace/paper-tracker"
VENV_DIR="${PROJECT_DIR}/.venv"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/paper-tracker-$(date +%Y-%m-%d).log"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Start logging
exec &> >(tee -a "${LOG_FILE}")
echo "=========================================="
echo "Paper Tracker Daily Run"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=========================================="

# Activate virtual environment
source "${VENV_DIR}/bin/activate"

# Run the full pipeline: fetch → summarize → report
cd "${PROJECT_DIR}"
paper-tracker run 2>&1

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "Exit code: ${EXIT_CODE}"
echo "=========================================="

# Clean up old logs (keep 30 days)
find "${LOG_DIR}" -name "paper-tracker-*.log" -mtime +30 -delete 2>/dev/null || true

exit ${EXIT_CODE}
