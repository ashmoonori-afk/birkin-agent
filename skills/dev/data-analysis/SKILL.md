---
name: data-analysis
description: Inspect structured run records, JSON files, and reports with repeatable analysis steps.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["data", "analysis"], "category": "dev"}, "openclaw": {"alwaysInclude": true}}
---

# Data Analysis

## When to Use

Use this skill when examining run records, logs, benchmark outputs, or structured workspace data.

## Procedure

1. Prefer structured parsing over ad hoc string matching.
2. Preserve input files and write derived outputs separately.
3. State assumptions and filters.
4. Keep a reproducible command or script when analysis affects a decision.

## Pitfalls

- Do not mix raw evidence and interpretation in the same table without labels.
- Do not overwrite source data.

## Verification

- The analysis can be reproduced from workspace files.
