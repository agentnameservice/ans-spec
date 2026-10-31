# Known ANS Registries

`known-registries.json` lists the public ANS registries that meet the
admission rules below. A registry is a Registration Authority (RA) and
the Transparency Log (TL) it publishes to. Verifiers, SDKs, and tooling
read this file to learn which logs exist and which keys sign their
checkpoints and receipts.

Being listed records that an operator met published, objective
criteria. It is not an endorsement, and no entry is a default. ANS is an
open specification that anyone may operate; this file is the project's
record of who does.

## Files

```text
registries/
├── README.md                     this document
├── known-registries.schema.json  JSON Schema 2020-12 for the data file
├── known-registries.json         the data
└── validate.py                   invariant checks run by CI
```

## Entry fields

| Field | Meaning |
|---|---|
| `id` | Stable identifier, `<operator>-<environment>`. Never reused, even after retirement. |
| `operator` | Who runs it: display name, home page, and an operational contact that is a role mailbox or reporting page, not a person. |
| `environment` | `production` or `test`. Test registries issue under test or production PKI as the operator documents; nothing registered there is production state. |
| `state` | Lifecycle state, see below. |
| `since` / `until` | Dates the entry entered and left the `usable` state. |
| `ra.baseUrl` | RA origin. ANS-1 routes are served under it. |
| `ra.apiVersions` | RA API lanes served (`v1`, `v2`). |
| `ra.auth` | Authorization schemes the RA accepts. |
| `tl.baseUrl` | TL origin. `/checkpoint`, `/root-keys`, and the ANS-4 read routes are served under it. The checkpoint origin line and every verification key's name prefix equal this URL's host. |
| `tl.verificationKeys` | C2SP signed-note verifier lines, copied verbatim from the log's `/root-keys`. Carried here so an offline verifier needs no network. |
| `identityCa` | Path to the PEM bundle in `pki/` that issues the registry's identity certificates, with its SHA-256. |

## States

| State | Verifiers | Registrants |
|---|---|---|
| `pending` | Do not trust. | May register for testing; nothing is attested yet. |
| `usable` | Trust. | Open. |
| `readonly` | Trust. | Closed. The log still serves and still verifies existing receipts. |
| `retired` | Do not trust. | Closed. Kept so the record of what was ever trusted is never lost. |

SDK and verifier defaults, where they exist, include exactly the
`usable` and `readonly` entries.

## Admission

An operator adds itself by opening a pull request that appends one entry
and nothing else. The pull request is merged by a maintainer who is not
affiliated with the applicant, with approval from two maintainers. It
must demonstrate, with links a reviewer can check:

1. `GET {tl.baseUrl}/root-keys` is publicly reachable and its content
   equals `tl.verificationKeys`.
2. `GET {tl.baseUrl}/checkpoint` verifies under one of those keys, and
   its origin line equals the host of `tl.baseUrl`.
3. The RA serves responses conformant to `api/api-spec-v2.yaml` for
   every lane listed in `ra.apiVersions`. Until a conformance suite
   exists, a public registration whose event appears in the log and
   verifies offline with a published verifier satisfies this.
4. A published log policy stating maximum merge delay, retention, and
   the incident contact.
5. An operator contact that is a role mailbox or a reporting page.

New entries enter as `pending`. A maintainer moves an entry to `usable`
after fourteen days of continuous checkpoint growth with no split view,
observed with an ANS-5 monitor.

## Changes and removal

- **Key rotation**: the operator opens a pull request that appends the
  new key to `tl.verificationKeys`. Old keys are not removed while any
  receipt they signed is within its validity window.
- **Voluntary shutdown**: the operator opens a pull request moving the
  entry to `readonly`, then to `retired` with `until` set once the log
  stops serving.
- **Compromise or split view**: any maintainer moves the entry to
  `retired` the same day, with `until` set, and opens an issue with the
  evidence. The operator may apply for re-admission under a new `id`.

## Validation

CI validates `known-registries.json` against the schema and runs
`validate.py`, which checks that identifiers are unique, every
verification key's name prefix equals the TL host, every `identityCa`
hash matches the bundle in `pki/`, and every `retired` entry has an
`until` date. Run both locally with:

```bash
check-jsonschema --schemafile registries/known-registries.schema.json registries/known-registries.json
python3 -I registries/validate.py
```

Neither check touches the network. Liveness of the listed endpoints is
an operational concern for monitors, not a gate on this repository.
