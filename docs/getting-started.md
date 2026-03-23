# Getting Started

## Installation

```bash
pip install neurobridge
```

## Quick Example

```python
from neurobridge import NeuroBridge, Profile

bridge = NeuroBridge()
bridge.set_profile(Profile.ADHD)
print(bridge.chat("Explain observability").adapted_text)
```
