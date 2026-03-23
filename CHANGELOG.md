# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-03-23
### Added
- Initial release with 5 cognitive profiles
- OpenAI, Anthropic, LangChain integrations
- REST API server
- ProfileQuiz engine
- SQLite and Redis memory backends
- Streaming adaptation endpoint and async APIs
- HuggingFace Space demo app in [demo/](demo/)
- Colab-ready quickstart notebook in [notebooks/NeuroBridge_Quickstart.ipynb](notebooks/NeuroBridge_Quickstart.ipynb)
- Expanded test coverage with property, integration, and API edge-case tests
- Coverage gate and CI quality checks
- Security and privacy documentation: [SECURITY.md](SECURITY.md), [docs/PRIVACY_POLICY.md](docs/PRIVACY_POLICY.md)

### Changed
- Centralized input validators for text, user IDs, and profile names
- API authentication switched to Bearer token semantics when API key is enabled
- Server middleware adds request-size cap, timeout guard, and security headers
- Website API routes enforce Zod validation with shared per-IP rate limiting
- Feedback persistence stores hashed content references and delta metrics only

### Security
- Added responsible disclosure policy in [SECURITY.md](SECURITY.md)
- Added CSP and browser security headers in website configuration
- Added dependency audit guidance and latest advisory snapshot
