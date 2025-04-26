#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# Parse a URL using the Scientific HTML Parser API.
# -----------------------------------------------------------------------------
# Usage: ./parse_url.sh [URL] [optional: output file]
# Example: ./parse_url.sh https://example.com/article my_article.md
# If no output file is specified, it will save to output/md/[domain]/[title].md
# -----------------------------------------------------------------------------

set -euo pipefail

# Check if URL is provided
if [ $# -lt 1 ]; then
  echo "Error: URL is required."
  echo "Usage: ./parse_url.sh [URL] [optional: output file]"
  exit 1
fi

URL="$1"
OUTPUT_FILE=""

# If second parameter is provided, use it as output file
if [ $# -gt 1 ]; then
  OUTPUT_FILE="$2"
fi

# Load .env if it exists
if [[ -f ".env" ]]; then
  # shellcheck disable=SC2046
  export $(grep -v "^#" .env | xargs -d "\n")
fi

# Set defaults from environment
HOST="${HOST}"
PORT="${PORT}"
VENV_NAME="${VENV_NAME:-parserVenv}"
API_URL="http://${HOST}:${PORT}/api/v1/parse-url"

# Activate virtual environment if it exists
if [ -d "${VENV_NAME}" ]; then
  echo "Activating virtual environment"
  # shellcheck disable=SC1090
  source "${VENV_NAME}/bin/activate"
else
  echo "Warning: Virtual environment '${VENV_NAME}' not found. Run run_server.sh first."
fi

echo "Parsing URL: ${URL} using API at ${API_URL}"
echo "This may take a moment depending on the size of the article..."

# Function to extract domain from URL
get_domain() {
  local url=$1
  local domain
  
  # Extract hostname
  domain=$(echo "$url" | sed -E 's|^https?://([^/]+).*|\1|')
  
  # Handle common scientific domains
  if [[ "$domain" == *"pubmed"* ]]; then
    echo "PubMed"
  elif [[ "$domain" == *"pmc"* ]]; then
    echo "PMC"
  elif [[ "$domain" == *"nature.com"* ]]; then
    echo "Nature"
  elif [[ "$domain" == *"science"* ]]; then
    echo "Science"
  else
    # Extract first part of domain
    echo "$domain" | cut -d. -f1 | tr '[:lower:]' '[:upper:]'
  fi
}

# Function to sanitize a filename
sanitize_filename() {
  echo "$1" | sed 's/[^a-zA-Z0-9._-]/_/g' | tr -s '_'
}

# Execute the API call
RESPONSE=$(curl -s -m 60 -X POST "${API_URL}" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${URL}\"}")

# Check if curl command succeeded
if [ $? -ne 0 ]; then
  echo "Error: Failed to connect to the API server at ${API_URL}"
  echo "Make sure the server is running on the specified host and port."
  exit 1
fi

# Check if response contains "markdown" field (aka success)
if [[ $RESPONSE == *"\"markdown\""* ]]; then
  # Extract the markdown content using jq if available, or basic sed otherwise
  if command -v jq &> /dev/null; then
    MARKDOWN=$(echo "$RESPONSE" | jq -r '.markdown')
    TITLE=$(echo "$RESPONSE" | jq -r '.metadata.title // "Untitled"')
  else
    # Fallback to basic extraction
    MARKDOWN=$(echo "$RESPONSE" | sed -n 's/.*"markdown":"\(.*\)","metadata".*/\1/p' | sed 's/\\n/\n/g' | sed 's/\\"/"/g')
    TITLE=$(echo "$RESPONSE" | sed -n 's/.*"title":"\([^"]*\)".*/\1/p')
    # Default title if not found
    TITLE=${TITLE:-"Untitled"}
  fi
  
  echo "Successfully parsed: ${TITLE}"
  
  # Save to file or auto-generate filename based on domain and title
  if [ -n "$OUTPUT_FILE" ]; then
    echo "$MARKDOWN" > "$OUTPUT_FILE"
    echo "Output saved to: $OUTPUT_FILE"
  else
    # Auto-generate filename
    DOMAIN=$(get_domain "$URL")
    SANITIZED_TITLE=$(sanitize_filename "$TITLE")
    
    # Create domain directory if it doesn't exist
    OUTPUT_DIR="output/md/$DOMAIN"
    mkdir -p "$OUTPUT_DIR"
    
    # Generate filename
    AUTO_FILENAME="$OUTPUT_DIR/${SANITIZED_TITLE}.md"
    
    # Save the file
    echo "$MARKDOWN" > "$AUTO_FILENAME"
    echo "Output saved to: $AUTO_FILENAME"
    
    # Also print to console
    echo "============ MARKDOWN OUTPUT PREVIEW ============"
    echo "$MARKDOWN" | head -n 20
    echo "..."
    echo "================================================="
  fi
  
  exit 0
else
  echo "Error parsing URL. Response:"
  echo "$RESPONSE"
  exit 1
fi 