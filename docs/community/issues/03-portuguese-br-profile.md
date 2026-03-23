# Add Portuguese (Brazil) Profile Variant

## Context
Broadens accessibility support beyond English defaults.

## What to do
1. Add profile enum/config for PT-BR variant.
2. Update profile-name validation allowlist.
3. Add tests for profile selection path.

## Files to edit
- [neurobridge/core/profile.py](neurobridge/core/profile.py#L12)
- [neurobridge/core/profile.py](neurobridge/core/profile.py#L49)
- [neurobridge/core/validators.py](neurobridge/core/validators.py#L12)
- [tests/test_profiles.py](tests/test_profiles.py#L21)

## Definition of done
- New profile can be selected and validated.
- `python -m pytest tests/test_profiles.py -q` passes.
