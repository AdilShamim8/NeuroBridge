# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Anxiety profile: the urgency filter now runs before the tone rewriter, so
  urgency signals are scored and softened instead of being silently rewritten
  away first
- Paragraph structure is preserved through the whole transform pipeline
  (chunker, sentence simplifier, tone rewriter, and urgency filter all
  collapsed paragraph breaks before)
- ADHD output: the priority reorderer no longer duplicates the last paragraph
  as both "Bottom line" and body text, no longer nests bold markers, and
  keeps code fences on their own line so they render as code
- Sentence tokenizer no longer orphans Markdown bold markers split across
  sentence boundaries (required the punkt fallback path)
- Markdown format adapter no longer turns closing code fences into opening
  fences with an info string, and no longer fakes `aria-label` inside image
  alt text
- Number contextualiser no longer emits the mathematically false
  "0 in every 1" for percentages under 2.5%
- Expected no-op transform modules no longer emit UserWarnings on every call
  (warnings remain in debug mode)
- OpenAI wrapper: `stream=True` now calls the real client and adapts the
  model's output (it previously streamed the adapted user prompt back and
  never contacted the API); the interactive quiz hang on missing profile was
  replaced by the bridge default plus a warning
- Anthropic wrapper: streaming responses are now adapted instead of passing
  through unmodified
- API server: CORS preflight requests succeed when API-key auth is enabled,
  and 401/429/504/413 responses carry CORS headers
- API server: per-request profile resolution - one request's `profile`
  parameter no longer changes the output of other users' requests
- API server: constant-time API-key comparison and a digest-based key
  identity instead of storing the key prefix
- API server: chunked request bodies are now size-limited like
  Content-Length bodies
- API server: invalid inputs (whitespace-only text, out-of-range quiz
  answers, malformed path user IDs) return 4xx instead of unhandled 500s
- API server: rate-limiter identity tables are bounded and evict stale
  entries
- API responses serialize the profile as the wire name (`dyslexia`), not
  `Profile.DYSLEXIA`
- JS SDK: profile configurations now match the Python defaults; anxiety
  softening produces grammatical output; number contexts use real fractions
  and magnitude comparisons instead of placeholders; the
  SentenceSimplifier is ported so maxSentenceWords is enforced
- JS SDK: the browser bundle no longer imports Node built-ins
- Website builds again (missing dependency, ref typing, typed routes); the
  shared-link API returns hashes its own schema accepts; playground output
  is HTML-escaped; the CSP no longer blocks the site's own accessibility
  fonts and analytics

### Changed
- Python 3.10+ is required (the code already used `dataclass(slots=True)`);
  the 3.9 claims and CI legs were removed
- README rewritten to describe the shipped package: fabricated integrations
  and modules removed, working quickstart, honest install instructions
- CODEOWNERS and FUNDING point at the real repository owner

### Added
- Vitest suite for the JavaScript SDK (31 tests; it previously had none)
- CI jobs for the JS SDK (typecheck, tests, build) and the website build
- Private vulnerability reporting instructions and the shipped-model pickle
  note in SECURITY.md
- Complete environment variable reference in .env.example
- README claims guard tests that fail CI if documented modules or extras
  do not exist

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
