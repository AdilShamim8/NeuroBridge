# Add --version Flag to CLI

## Context
Version visibility is a standard CLI expectation and helps bug reporting.

## What to do
1. Add root-level `--version` option.
2. Print semantic version and exit 0.
3. Add CLI tests.

## Files to edit
- [neurobridge/cli.py](neurobridge/cli.py#L28)
- [neurobridge/cli.py](neurobridge/cli.py#L218)
- [tests/test_cli.py](tests/test_cli.py#L12)

## Definition of done
- `neurobridge --version` prints version.
- `python -m pytest tests/test_cli.py -q` passes.
