#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# Launch the Scientific HTML Parser API with verbose logging.
# -----------------------------------------------------------------------------
# 1. Loads environment variables from .env (if present).
# 2. Creates/activates virtual environment and installs dependencies.
# 3. Ensures a logs/ directory exists.
# 4. Starts Uvicorn with host/port/logging defined in env variables.
# 5. Pipes full stdout/stderr to both console and timestamped log file.
# -----------------------------------------------------------------------------

set -euo pipefail

# Load .env if it exists
if [[ -f ".env" ]]; then
  # shellcheck disable=SC2046
  export $(grep -v "^#" .env | xargs -d "\n")
fi

# Set defaults for required variables
HOST="${HOST}"
PORT="${PORT}"
LOG_LEVEL="${LOG_LEVEL:-info}"
DEBUG="${DEBUG:-False}"
VENV_NAME="${VENV_NAME:-parserVenv}"
LOG_DIR="logs"
mkdir -p "${LOG_DIR}"

# Check for and gracefully shut down any existing uvicorn instance on the same port
echo "Checking for previous uvicorn instances on port ${PORT}..."
PREV_PID=$(lsof -i:${PORT} -t 2>/dev/null || echo "")
if [[ -n "${PREV_PID}" ]]; then
  echo "Found existing process (PID: ${PREV_PID}) using port ${PORT}, shutting down gracefully..."
  if kill -15 ${PREV_PID} 2>/dev/null; then
    echo "Sent SIGTERM to process ${PREV_PID}"
    # Wait for the process to terminate (max 5 seconds)
    for i in {1..5}; do
      if ! ps -p ${PREV_PID} > /dev/null 2>&1; then
        echo "Process terminated successfully"
        break
      fi
      echo "Waiting for process to terminate... (${i}/5)"
      sleep 1
    done
    # Force kill if still running
    if ps -p ${PREV_PID} > /dev/null 2>&1; then
      echo "Process still running, sending SIGKILL..."
      kill -9 ${PREV_PID} 2>/dev/null || true
    fi
  else
    echo "Failed to send SIGTERM, process may have terminated already"
  fi
  
  # Small delay to ensure the port is released
  sleep 1
fi

# Virtual environment setup
if [ ! -d "${VENV_NAME}" ]; then
  echo "Creating virtual environment: ${VENV_NAME}"
  python3 -m venv "${VENV_NAME}"
else
  echo "Using existing virtual environment: ${VENV_NAME}"
fi

# Activate virtual environment
echo "Activating virtual environment"
# shellcheck disable=SC1090
source "${VENV_NAME}/bin/activate"

# Install or update dependencies
echo "Installing/updating dependencies"
pip install -q -r requirements.txt

# Convert log level to lowercase for uvicorn
LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL}" | tr '[:upper:]' '[:lower:]')

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="${LOG_DIR}/api_${TIMESTAMP}.log"

echo "Starting API at ${HOST}:${PORT} with log level ${LOG_LEVEL}. Logs: ${LOG_FILE}"

# Determine whether to use --reload based on DEBUG
RELOAD_FLAG=""
if [[ "${DEBUG}" == "True" || "${DEBUG}" == "true" ]]; then
  RELOAD_FLAG="--reload"
  echo "Debug mode enabled, hot-reloading activated"
fi

# Run Uvicorn with environment-configured settings
exec uvicorn app:app \
  --host "${HOST}" \
  --port "${PORT}" \
  --log-level "${LOG_LEVEL_LOWER}" \
  ${RELOAD_FLAG} \
  2>&1 | tee -a "${LOG_FILE}" 