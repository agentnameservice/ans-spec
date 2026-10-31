#!/usr/bin/env python3
"""Invariant checks for registries/known-registries.json beyond what JSON Schema expresses.

Run with ``python3 -I registries/validate.py`` from the repository root.
Exits non-zero and prints one line per violation.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "registries" / "known-registries.json"


def host_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def check(registries: list[dict]) -> list[str]:
    problems: list[str] = []
    seen_ids: set[str] = set()
    seen_tl: set[str] = set()

    for entry in registries:
        rid = entry.get("id", "<missing id>")

        if rid in seen_ids:
            problems.append(f"{rid}: duplicate id")
        seen_ids.add(rid)

        tl_url = entry["tl"]["baseUrl"]
        tl_host = host_of(tl_url)
        if tl_host in seen_tl:
            problems.append(f"{rid}: tl.baseUrl host {tl_host} already listed")
        seen_tl.add(tl_host)

        for key in entry["tl"]["verificationKeys"]:
            name = key.split("+", 1)[0]
            if name != tl_host:
                problems.append(f"{rid}: verification key name {name!r} != tl host {tl_host!r}")

        bundle = ROOT / entry["identityCa"]["bundle"]
        if not bundle.is_file():
            problems.append(f"{rid}: identityCa.bundle {entry['identityCa']['bundle']} not found")
        else:
            digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
            if digest != entry["identityCa"]["sha256"]:
                problems.append(f"{rid}: identityCa.sha256 {entry['identityCa']['sha256']} != {digest}")

        if entry["state"] == "retired" and not entry.get("until"):
            problems.append(f"{rid}: retired entry has no until date")
        if entry["state"] != "retired" and entry.get("until"):
            problems.append(f"{rid}: until is set but state is {entry['state']}")

    return problems


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    problems = check(data["registries"])
    for line in problems:
        print(line, file=sys.stderr)
    if problems:
        return 1
    print(f"ok: {len(data['registries'])} registries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
