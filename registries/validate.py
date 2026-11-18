#!/usr/bin/env python3
"""Structural checks for registries/known-registries.json beyond what JSON Schema expresses.

Run with ``python3 -I registries/validate.py`` from the repository root.
Exits non-zero and prints one line per violation.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "registries" / "known-registries.json"
REPO_RAW = "https://raw.githubusercontent.com/agentnameservice/ans-spec/"


def local_bundle(url: str) -> Path | None:
    """Return the working-tree path of a bundle served from this repository, else None."""
    if not url.startswith(REPO_RAW):
        return None
    _ref, _, path = url[len(REPO_RAW):].partition("/")
    return ROOT / path


def check_identity_ca(label: str, ca: dict) -> list[str]:
    bundle = local_bundle(ca["url"])
    if bundle is None:
        return []
    if not bundle.is_file():
        return [f"{label}: identityCa.url names {ca['url']}, which is not a file in this repository"]
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    if digest != ca["sha256"]:
        return [f"{label}: identityCa.sha256 {ca['sha256']} != {digest} for {bundle.relative_to(ROOT)}"]
    return []


def check(registries: list[dict]) -> list[str]:
    problems: list[str] = []
    seen_ids: set[str] = set()
    seen_origins: dict[str, str] = {}

    for entry in registries:
        rid = entry.get("id", "<missing id>")
        if rid in seen_ids:
            problems.append(f"{rid}: duplicate id")
        seen_ids.add(rid)

        for name, env in entry["environments"].items():
            label = f"{rid}/{name}"
            for role in ("ra", "tl"):
                origin = env[role].lower()
                if origin in seen_origins:
                    problems.append(f"{label}: {role} {origin} already listed by {seen_origins[origin]}")
                seen_origins[origin] = label
            if "identityCa" in env:
                problems.extend(check_identity_ca(label, env["identityCa"]))

    return problems


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    problems = check(data["registries"])
    for line in problems:
        print(line, file=sys.stderr)
    if problems:
        return 1
    environments = sum(len(entry["environments"]) for entry in data["registries"])
    print(f"ok: {len(data['registries'])} registries, {environments} environments")
    return 0


if __name__ == "__main__":
    sys.exit(main())
