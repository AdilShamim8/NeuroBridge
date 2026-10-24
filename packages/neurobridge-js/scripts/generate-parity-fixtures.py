"""Generate golden fixtures for the JS SDK parity test.

Run from the repository root:

    python packages/neurobridge-js/scripts/generate-parity-fixtures.py

It writes tests/fixtures/parity.json containing, for every built-in profile,
the Python pipeline's adapt() output over a fixed corpus. The vitest suite
asserts the JavaScript port reproduces exactly these strings, so any drift
between the two implementations fails CI.
"""

from __future__ import annotations

import json
from pathlib import Path

from neurobridge import NeuroBridge, Profile

CORPUS = [
    "You must immediately fix the critical bug. The deployment window closes in 2 hours. Revenue was 22% lower than target this quarter.",
    "This is urgent. You must finish the report immediately and provide a detailed breakdown of all budget percentages and assumptions.",
    "Deploy the service and verify the migration. Therefore the release is unblocked. The latency dropped by 35% after the cache change, which helped retention. For example, session length rose for 3 weeks.",
    "Oh great, the build broke again. At the end of the day, we need to touch base and bite the bullet on the refactor. It is worth noting that some modules use vague words like many and soon.",
    "The error rate is 0.8% and the cluster costs $1.2 million per year. Downtime lasted 3-4 days. The dataset is 500 GB. In summary, capacity planning must improve. Consider the failure domains.",
    "Keep calm. The backup restore finished and the data is intact.\n\nSecond paragraph mentions a risk of data loss which was mitigated. The deadline passed without incident.",
]

PROFILES = [Profile.ADHD, Profile.AUTISM, Profile.DYSLEXIA, Profile.ANXIETY, Profile.DYSCALCULIA]


def main() -> None:
    bridge = NeuroBridge()
    fixtures: list[dict[str, str]] = []
    for profile in PROFILES:
        bridge.set_profile(profile)
        for text in CORPUS:
            fixtures.append(
                {
                    "profile": profile.value,
                    "input": text,
                    "expected": bridge.adapt(text),
                }
            )

    out = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "parity.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fixtures, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(fixtures)} fixtures to {out}")


if __name__ == "__main__":
    main()
