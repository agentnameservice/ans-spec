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
REPO_REF = "main"


def local_bundle(url: str) -> Path | None:
    """Return the checkout path of a bundle served from this repository, or None
    for a bundle published elsewhere.

    Raises ValueError when the URL is under this repository but names a ref
    other than ``main`` or a path that resolves outside the checkout, so CI
    hashes the same file the URL serves.
    """
    if not url.startswith(REPO_RAW):
        return None
    ref, _, rel = url[len(REPO_RAW):].partition("/")
    if ref != REPO_REF:
        raise ValueError(f"uses ref {ref!r}; bundles in this repository must use {REPO_REF!r}")
    path = (ROOT / rel).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"path {rel!r} resolves outside the checkout")
    return path


def check_identity_ca(label: str, ca: dict) -> list[str]:
    try:
        bundle = local_bundle(ca["url"])
    except ValueError as err:
        return [f"{label}: identityCa.url {ca['url']} {err}"]
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
