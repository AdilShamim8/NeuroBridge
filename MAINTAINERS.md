# Maintainer Playbook

## PR Review Checklist

Use this checklist for every PR:

1. Problem statement is clear and issue-linked.
2. Scope is small and focused.
3. Tests cover changed behavior.
4. No obvious regressions in API contracts.
5. Docs updated for user-visible changes.
6. `CHANGELOG.md` updated under Unreleased.
7. Security/privacy implications reviewed.
8. CI checks pass before merge.

## Release Process

1. Ensure tests, typing, linting, and formatting checks pass.
2. Build package artifacts:
   - `python -m build`
   - `python -m twine check dist/*`
3. Publish to TestPyPI and validate fresh install.
4. Publish to PyPI.
5. Tag release in git and push tag.
6. Create GitHub release notes and attach wheel + sdist.
7. Publish social launch posts and monitor feedback.

## Handling Security Reports

1. Acknowledge report quickly (target within 48 hours).
2. Reproduce and assess severity.
3. Coordinate fix in private branch or advisory flow.
4. Prepare patch release if needed.
5. Credit reporter in `CHANGELOG.md` when disclosure allows.
6. Update `SECURITY.md` if process needs improvement.

## Handling Breaking Changes

1. Mark breaking change clearly in PR and changelog.
2. Add migration guidance and examples.
3. Prefer deprecation period before removal when practical.
4. Bump version according to semver.
5. Announce prominently in release notes.

## Writing a Good Release Announcement

Include:

- Why this release matters for users.
- What changed (high-signal bullets).
- Upgrade steps or migration notes.
- Security and privacy notes when relevant.
- Links to docs, examples, and demo.
- Thank you section for contributors.
