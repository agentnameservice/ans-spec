# Known ANS Registries

`known-registries.json` is a directory of public ANS registries. A
registry is a Registration Authority (RA) and the Transparency Log (TL)
it publishes to; an operator usually runs a production and a test
environment of each. Tooling reads this file so a consumer can pick a
registry and environment by name instead of typing URLs.

Being listed records that a registry exists and where its endpoints
are. It is not an endorsement, it does not make the registry trusted,
and no entry is a default. The consumer chooses which registry to use
and which log keys and certificate authorities to accept.

## Files

```text
registries/
├── README.md                     this document
├── known-registries.schema.json  JSON Schema 2020-12 for the data file
├── known-registries.json         the data
└── validate.py                   structural checks run by CI
```

## Entry fields

One entry per registry.

| Field | Meaning |
|---|---|
| `id` | Stable identifier, never reused. Convention: the operator's name in lower case. |
| `operator` | Display name of the organization that runs the registry. |
| `documentation` | Optional. The operator's setup documentation for registrants and verifiers. |
| `environments` | One or both of `production` and `test`, each as below. Nothing registered in `test` is production state. |

Each environment:

| Field | Meaning |
|---|---|
| `ra` | RA origin. ANS-1 routes are served under it. |
| `tl` | TL origin. `/checkpoint`, `/root-keys`, and the ANS-4 read routes are served under it. |
| `identityCa` | Optional. The `url` of the PEM bundle the operator publishes for the CA certificates that issue this environment's identity certificates, and the `sha256` of its bytes. |

## What the directory does not carry

**Transparency Log keys.** The keys that sign a log's checkpoints are
served by the log itself at `{tl}/root-keys` and are not copied here,
so a rotation does not depend on a pull request to this repository or
on every consumer refreshing its copy of this file. A consumer fetches
the keys after selecting a registry and environment, validates them,
and keeps them for offline verification. Refreshing them is an explicit
operation, and older keys are retained so receipts they signed still
verify.

**Trust decisions.** `identityCa` says where an operator publishes its
CA bundle and what its bytes hash to. Downloading that bundle does not
make its roots trusted. A consumer explicitly configures the roots it
accepts, scoped to that registry and environment, and a routine refresh
of this directory or of the bundle must not add or replace trusted CAs
without that explicit step.

## Listing a registry

An operator adds, changes, or removes its entry by opening a pull
request that touches its entry and nothing else. CI checks structure
only, as described below. Maintainers do not assess how the registry
is operated, and merging an entry is not an endorsement.

## Validation

CI validates `known-registries.json` against the schema and runs
`validate.py`, which checks that identifiers are unique, that no two
environments share an RA or TL origin, and that every `identityCa.url`
served from this repository (`https://raw.githubusercontent.com/agentnameservice/ans-spec/main/...`)
names an existing file whose SHA-256 equals `identityCa.sha256`. Run
both locally with:

```bash
check-jsonschema --schemafile registries/known-registries.schema.json registries/known-registries.json
python3 -I registries/validate.py
```

Neither check touches the network. Bundles published elsewhere are
checked for shape only, and liveness of the listed endpoints is an
operational concern for monitors, not a gate on this repository.
