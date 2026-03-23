# Add Reading Time Estimate to AdaptedResponse

## Context
Reading-time hints help users plan attention and cognitive effort.

## What to do
1. Add reading-time field to response model.
2. Populate in sync and streaming completion responses.
3. Add tests to verify presence and sensible values.

## Files to edit
- [neurobridge/core/bridge.py](neurobridge/core/bridge.py#L92)
- [neurobridge/core/bridge.py](neurobridge/core/bridge.py#L200)
- [neurobridge/core/bridge.py](neurobridge/core/bridge.py#L349)
- [tests/test_bridge.py](tests/test_bridge.py#L27)

## Definition of done
- Field exists and is non-negative.
- `python -m pytest tests/test_bridge.py tests/test_streaming.py -q` passes.
