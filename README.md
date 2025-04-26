# Scientific HTML Parser

A robust HTML parser specifically designed for scientific and technical content. The parser converts HTML into clean, well-structured markdown while preserving important metadata.

## Features

- **Clean Conversion**: Converts HTML to clean, structured markdown
- **Metadata Extraction**: Extracts title, authors, publication date, DOI, and more
- **Format Options**: Multiple output formats including standard, semantic, and YAML-frontmatter
- **Section Recognition**: Intelligently identifies document sections (abstract, methods, results, etc.)
- **Entity Recognition**: Identifies entities such as physiological parameters, body systems, exercise types
- **Domain Detection**: Automatically detects therapeutic domains of content
- **Study Type Detection**: Identifies the type of study (RCT, meta-analysis, cohort study, etc.)
- **Keyword Generation**: Extracts relevant keywords based on content analysis
- **Reference Formatting**: Proper formatting of scientific references

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/html-parser.git
   cd html-parser
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv parserVenv
   source parserVenv/bin/activate  # On Windows: parserVenv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```
   HOST=0.0.0.0
   PORT=8877
   WEBHOOK_URL=
   WEBHOOK_SECRET=
   SAVE_LOCAL_FILES=true
   OUTPUT_DIR=output/md
   USE_API_OPTIMIZATION=true
   # YAML Preprocessing (for n8n integration)
   ENABLE_YAML_PREPROCESSING=true
   CONVERT_TO_JSON=false
   N8N_WEBHOOK_URL=https://your-n8n-endpoint.com/webhook/path
   ```

## Usage

### Starting the Server

```bash
./run_server.sh
```

### Command Line Interface

#### Single URL Parsing

Parse a single URL:

```bash
./parse_url.sh https://example.com/article
```

Parse a URL and save to a specific file:

```bash
./parse_url.sh https://example.com/article output_file.md
```

Parse a URL with a specific format:

```bash
./parse_url.sh https://example.com/article output_file.md yaml
```

#### Batch URL Parsing

Process multiple URLs from a file:

```bash
./batch_parse.sh urls.txt
```

Process multiple URLs with a specific format:

```bash
./batch_parse.sh urls.txt semantic
```

### Output Formats

The parser supports three output formats:

1. **standard** (default): Basic markdown output with minimal structure
2. **semantic**: Enhanced semantic markup with entities and mechanisms detected
3. **yaml**: YAML front matter with structured metadata

#### YAML Format Example

```markdown
---
title: "Example Article Title"
source_url: "https://example.com/article"
date_processed: "2023-07-20T14:30:00Z"
doi: "10.1234/example.5678"
journal: "Journal of Examples"
publication_date: "2023-05-15"
authors:
  - "Smith, John"
  - "Doe, Jane"
document_type: "research_article"
therapeutic_domains:
  - "infrared_therapy"
  - "detoxification"
study_type:
  - "rct"
  - "clinical_trial"
sections:
  - id: "abstract"
    heading: "Abstract"
    keywords:
      - "infrared radiation"
      - "detoxification"
      - "sweat"
  - id: "introduction"
    heading: "Introduction"
    keywords:
      - "heat therapy"
      - "toxin elimination"
  # ... more sections
entities:
  physiological_parameter:
    - "heart rate"
    - "blood pressure"
  body_system:
    - "cardiovascular"
    - "integumentary"
  # ... more entity types
mechanisms:
  cellular_mechanisms:
    - "mitochondrial biogenesis"
    - "ATP production"
  # ... more mechanism types
---

# Example Article Title

## Abstract

Lorem ipsum dolor sit amet, consectetur adipiscing elit...
```

## API Endpoints

The server exposes the following API endpoints:

- `POST /api/v1/parse`: Parse raw HTML into markdown
- `POST /api/v1/parse-url`: Fetch and parse content from a URL
- `POST /api/v1/parse-url/enhanced`: Parse with enhanced semantic markup
- `GET /health`: Health check endpoint

## YAML Preprocessing for n8n Integration

The parser now includes a preprocessing feature that simplifies the YAML front matter for better compatibility with n8n JavaScript processing. This feature:

- Flattens nested structures for easier access in n8n workflows
- Ensures consistent indentation and array formatting
- Converts complex YAML structures into direct key-value pairs
- Optionally converts YAML to JSON format for direct JSON parsing

### Configuring YAML Preprocessing

Add these options to your `.env` file:

```
# YAML Preprocessing (for n8n integration)
ENABLE_YAML_PREPROCESSING=true
CONVERT_TO_JSON=false
N8N_WEBHOOK_URL=https://your-n8n-endpoint.com/webhook/path
```

### How YAML Preprocessing Works

The preprocessing transforms complex nested YAML structures into a simplified format:

**Before Preprocessing:**
```yaml
entities:
  physiological_parameter:
    - "heart rate"
    - "blood pressure"
  body_system:
    - "cardiovascular"
    - "integumentary"
```

**After Preprocessing:**
```yaml
physiological_parameters:
  - "heart rate"
  - "blood pressure"
body_systems:
  - "cardiovascular"
  - "integumentary"
```

### Integration with Webhook Delivery

When enabled, the YAML preprocessing happens automatically after webhook_v3.py generates the response and before sending to n8n. The integration:

1. Extracts the YAML front matter from the markdown field
2. Processes it for simplified structure
3. Repackages the response with processed YAML
4. Forwards the processed response to n8n

This makes parsing the data in n8n JavaScript nodes much easier, as all data is available at predictable paths with consistent formatting.

## File Output

Processed files are saved in the following structure:

```
output/md/
  └── DOMAIN/
      ├── ArticleTitle_Original.md
      ├── ArticleTitle_ChunkOptimized.md (for standard format)
      ├── ArticleTitle_Semantic.md (for semantic format)
      └── ArticleTitle_YAML.md (for yaml format)
```

The `DOMAIN` directory is automatically created based on the source URL.

## Dependencies

- FastAPI: Web framework
- BeautifulSoup4: HTML parsing
- Requests: HTTP requests
- NLTK: Natural language processing
- Python-dotenv: Environment variable management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 