# Changelog

All notable changes to the WebScribe project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-04-26

### Added
- Airtable integration capabilities for direct syncing of parsed content
- Added support for personal access tokens for Airtable authentication
- Added record_id tracking between n8n and parser services
- Created utility scripts for Airtable setup and management
- Enhanced error handling for external service integrations
- Added detailed debugging tools for Airtable connectivity

### Changed
- Switched to direct n8n integration as the recommended approach
- Made webhook and Airtable integrations optional (disabled by default)
- Improved API response structure with additional metadata
- Updated documentation to emphasize direct integration benefits
- Enhanced middleware for more robust request handling

### Fixed
- Fixed recursive middleware error that was causing stability issues
- Improved error handling for large payload processing

## [1.0.0] - 2025-04-26

### Added
- Initial release of WebScribe
- FastAPI backend with two main endpoints:
  - `/api/v1/parse` for direct HTML parsing
  - `/api/v1/parse-url` for fetching and parsing URLs
- Intelligent content extraction using heuristics to identify main article content
- Markdown conversion with proper heading level preservation
- Metadata extraction (title, authors, publication date when available)
- Webhook integration for seamless workflow automation
  - HMAC signature verification for secure payloads
  - Configurable retry mechanism with exponential backoff
- Command line tools:
  - `parse_url.sh` for quick URL parsing
  - `run_test_parse.sh` for testing with webhook integration
  - `run_server.sh` with graceful shutdown and restart capabilities
- Environment-based configuration via `.env` file
- Comprehensive logging to both console and files
- Content size limiting and request timeouts for robustness
- CORS support for frontend integration
- Interactive API documentation via Swagger UI
- Optimized initial parsing for scientific articles with extensible architecture 