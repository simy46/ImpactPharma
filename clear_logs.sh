set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"

if [[ ! -d "${LOG_DIR}" ]]; then
  echo "Logs directory not found: ${LOG_DIR}" >&2
  exit 1
fi

while IFS= read -r -d '' log_file; do
  : > "${log_file}"
done < <(find "${LOG_DIR}" -type f -print0)

echo "Cleared log file contents in ${LOG_DIR}"
