# Contributing

Reproduction reports, Linux setup corrections, protocol analysis and tests are
welcome. Start with the hardware and protocol documents.

This is an explicitly LLM-assisted project; see [AI_ASSISTANCE.md](AI_ASSISTANCE.md).
Disclose material LLM assistance in contributions and in any upstream proposal.
Do not present generated code or documentation as independently human-written
or reviewed. Respect each upstream project's policy on generated submissions.

```sh
python3 -m unittest -v test_keys
sh -n install-user install-device-access
```

Tests do not need a keyboard. Use a temporary home and
`install-user --no-service` when testing installation.

For hardware changes, record the exact model, VID/PID, descriptor and observed
result. Do not enable a product family based only on a similar name or VID.
Compare new commands with evidence before sending them. Establish profile
backup/restore and preservation of mappings/macros before adding storage writes.

Keep captures limited to the lighting interface and review them before sharing.
Full USB captures can contain typing and serials. Prefer small sanitized report
fixtures with source links. Do not commit local settings, logs, credentials or
device backups. Distinguish physical visual tests from mocked tests and inferred
behaviour in both reports and documentation.
