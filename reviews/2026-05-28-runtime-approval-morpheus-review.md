# Runtime, Approval Gate, and Morpheus Review

Scope date: 2026-05-28.

## Findings

No blocking findings after review.

## Review Coverage

- Reviewed the tool-calling runtime path in `src/birkin_agent/runtime.py`.
- Reviewed approval queue creation, approval resolution, and action executors in
  `src/birkin_agent/approvals.py`.
- Reviewed semantic Obsidian memory note creation, search, get, and wikilink updates in
  `src/birkin_agent/memory.py`.
- Reviewed Morpheus dry-run/no-key behavior, daemon schedule storage, and dashboard/API
  exposure.
- Reviewed Telegram env-only token handling, inbound opt-in polling, and outbound
  approval behavior for runtime-requested sends.
- Reviewed dashboard and gateway approval endpoints. The dashboard approval and Morpheus
  POST endpoints require a local client request; the gateway remains covered by its
  localhost/token policy.

## Verification Evidence

- `py -m compileall -q src tests`: passed.
- `py -m unittest discover -s tests`: 23 tests passed.
- `py -m pip install -e .`: passed.
- `birkin-codex morpheus --dry-run --json`: passed and wrote a Morpheus run record.
- `birkin-codex approvals list --json`: passed.
- `birkin-codex daemon status --json`: passed.
- `birkin-codex gateway routes`: includes approval, schedule, daemon, and Morpheus routes.
- `birkin-codex doctor`: ok with expected warnings for missing `OPENAI_API_KEY`,
  Telegram disabled, and first-write memory when applicable.
- `birkin-codex skills validate`: ok.
- `birkin-codex setup --json`: warning status only for expected optional setup items.
- `birkin-codex skills config --json`: upstream mirror reports 147 mirrored skills and
  0 missing directories.
- Dashboard smoke on `127.0.0.1:8767`: status API included Morpheus and approvals, HTML
  contained Morpheus and did not contain Nightly, and `POST /api/morpheus` returned
  dry-run status.
- Gateway smoke on `127.0.0.1:8771`: `/health` returned ok and `POST /api/morpheus`
  returned dry-run status.

## Residual Risk

- The real OpenAI-compatible `api-agent` path was tested with a local fake server. Live
  provider behavior should still be smoke-tested with the target provider before relying
  on long-running tool-agent sessions.
- Telegram inbound polling was configuration-tested without a live Telegram token.
