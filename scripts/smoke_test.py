"""Smoke test every API blueprint end-to-end.

Assumes the Flask dev server is already running on 127.0.0.1:5057.
Run:

    .venv/Scripts/python.exe scripts/smoke_test.py
"""
from __future__ import annotations

import json
import sys

import requests

BASE = "http://127.0.0.1:5057/api"


def pp(label: str, obj) -> None:
    print(f"--- {label} ---")
    print(json.dumps(obj, indent=2, default=str)[:1200])
    print()


def main() -> int:
    r = requests.get(f"{BASE}/health", timeout=5)
    r.raise_for_status()
    pp("health", r.json())

    r = requests.get(f"{BASE}/chapters", timeout=5)
    r.raise_for_status()
    chapters = r.json()["chapters"]
    print(f"chapters: {len(chapters)} total")
    for c in chapters[:3]:
        print(
            f"  ch{c['number']:02d} {c['title']!r}: "
            f"{c['totals']['learn_doses']} doses, "
            f"{c['totals']['practice_exercises']} exercises"
        )
    print()

    r = requests.get(f"{BASE}/chapters/1", timeout=5)
    r.raise_for_status()
    ch = r.json()
    print(f"ch1 sections: {len(ch['sections'])}")
    for s in ch["sections"][:3]:
        print(f"  #{s['order_index']} '{s['title']}' (depth {s['depth']}, {s['char_count']} chars)")
    print()

    r = requests.get(f"{BASE}/chapters/1/micro-doses", timeout=5)
    r.raise_for_status()
    doses = r.json()
    print(f"ch1 micro-doses: {doses['count']}")
    first_id = doses["doses"][0]["id"]

    r = requests.get(f"{BASE}/micro-doses/{first_id}", timeout=5)
    r.raise_for_status()
    dose = r.json()
    print(f"dose #{dose['id']}: '{dose['title']}'")
    print(f"  hook: {dose['hook']!r}")
    print(f"  reading: {len(dose['reading'])} chars")
    print(f"  starter_code: {len(dose['starter_code'])} chars")
    if dose["starter_code"]:
        print(f"  starter preview: {dose['starter_code'][:120]!r}")
    print(f"  teach_back: {dose['teach_back_prompt']!r}")
    print(f"  progress.status: {dose['progress']['status']}")
    print()

    # Save some work.
    r = requests.post(
        f"{BASE}/micro-doses/{first_id}/save",
        json={"last_code": "print('hello')", "last_teach_back": "An expression is..."},
        timeout=5,
    )
    r.raise_for_status()
    print(f"save: status={r.json()['progress']['status']}")

    # Complete the dose.
    r = requests.post(f"{BASE}/micro-doses/{first_id}/complete", json={"score": 1.0}, timeout=5)
    r.raise_for_status()
    prog = r.json()["progress"]
    print(f"complete: status={prog['status']}, completed_at={prog['completed_at']}")
    print()

    # Practice endpoints.
    r = requests.get(f"{BASE}/chapters/1/practice", timeout=5)
    r.raise_for_status()
    prac = r.json()
    print(f"ch1 practice: {len(prac['exercises'])} exercises across {len(prac['sections'])} sections")
    for ex in prac["exercises"][:3]:
        print(f"  [{ex['id']}] {ex['kind']}: {ex['title']!r} (completed={ex['completed']})")
    # Submit the first exercise as passed.
    first_ex = prac["exercises"][0]["id"]
    r = requests.post(
        f"{BASE}/practice/{first_ex}/submit",
        json={"passed": True, "code": "print('pass')"},
        timeout=5,
    )
    r.raise_for_status()
    print(f"practice submit: {r.json()}")
    print()

    # Progress roll-up.
    r = requests.get(f"{BASE}/progress", timeout=5)
    r.raise_for_status()
    prog = r.json()
    print(f"progress: XP={prog['total_xp']}, level={prog['level']['name']} ({prog['level']['xp_into_level']} into), streak={prog['streak']['days']} (x{prog['streak']['multiplier']})")
    print(f"  overall_score: {prog['overall_score']}")
    ch1_stats = next(x for x in prog["chapters"] if x["number"] == 1)
    print(f"  ch1 rollup: learn {ch1_stats['learn']['completed']}/{ch1_stats['learn']['total']}, practice {ch1_stats['practice']['completed']}/{ch1_stats['practice']['total']}")
    print()

    r = requests.get(f"{BASE}/xp/events?limit=5", timeout=5)
    r.raise_for_status()
    evs = r.json()["events"]
    print(f"xp events (latest {len(evs)}):")
    for e in evs:
        print(f"  {e['occurred_at']}: {e['event_type']} +{e['amount']} (x{e['multiplier']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
