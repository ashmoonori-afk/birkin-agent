# Verified Learning and Reliability

Scope date: 2026-05-28.

Birkin is a verified-learning, reliability-first agent OS. The implementation is built
to prevent three common agent failures:

- Learning a wrong or temporary fact as permanent behavior.
- Mutating memory or skills without enough evidence.
- Failing silently in a gateway, delivery, or scheduled workflow.

## Verified Learning Loop

Learning events are appended to:

```text
learning/events.jsonl
```

Learning proposals are stored under:

```text
learning/proposals/pending
learning/proposals/history
```

Every memory, skill, or self-improvement change can carry:

- Evidence links: conversation, run, file, test, approval, feedback, or manual source.
- Confidence and evidence strength.
- TTL and expiry metadata.
- Scope fields for user, project, machine, channel, thread, and profile.
- Author, agent, timestamp, reason, and blame.
- Rollback metadata when Birkin can restore a previous file body.

Commands:

```sh
birkin-codex learning list
birkin-codex learning events
birkin-codex learning show <proposal-id>
birkin-codex learning approve <proposal-id>
birkin-codex learning reject <proposal-id>
birkin-codex learning rollback <event-id>
```

Morpheus uses this loop directly. High-confidence memory updates with strong evidence can
apply; weak evidence and all skill updates become reviewable proposals.

## Memory OS

Obsidian notes now include typed and scoped frontmatter:

```yaml
kind: feedback
type: workflow
confidence: 0.900
version: 2
scope: {"project": "birkin_codex", "profile": "morpheus"}
evidence: [{"type": "run", "ref": "runs/example.json"}]
ttlDays: 7
expires: "20260604T000000Z"
author: "user"
agent: "morpheus"
reason: "verified recurring workflow"
blame: ""
```

Supported memory types are User, Project, Environment, Workflow, Ephemeral, Negative,
Conversation, Run, Error, and Feedback. Negative memory gets revalidation metadata so a
temporary failure does not become permanent learned helplessness.

Search filters:

```sh
birkin-codex memory search "Playwright" \
  --type negative \
  --scope project \
  --min-confidence 0.8 \
  --tag browser \
  --source runs/
```

## Approval and Risk UX

Approval items include risk tier, evidence count, affected resources, dry-run preview,
and rollback hint. Risk tiers are:

- `safe`
- `review`
- `dangerous`
- `external`
- `irreversible`

Tool-agent requests for shell, external web fetch, Telegram send, scheduling, and file
writes/deletes are queued unless the action was explicitly user-triggered outside the
agent runtime.

## Reliability Control Plane

Reliability events are appended to:

```text
reliability/events.jsonl
```

The dashboard and CLI expose:

- Trace timeline: user, agent, tool, subagent, approval, delivery, and result stages.
- Health checks for gateway, Morpheus, Telegram, memory, ledger, models, and API.
- Delivery status, replay records, and silent-failure warnings.
- Budget status for per-run, daily, and monthly token limits.
- Model-routing visibility through the active default model profile.

Commands:

```sh
birkin-codex reliability health
birkin-codex reliability traces
birkin-codex reliability log
birkin-codex reliability budget
```

Gateway routes:

```text
GET /api/learning
POST /api/learning
GET /api/reliability
```
