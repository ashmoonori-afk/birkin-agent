---
name: weather
description: Retrieve weather facts with location, date, source, and uncertainty boundaries.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["weather", "lookup"], "category": "integrations"}, "openclaw": {"alwaysInclude": true}}
---

# Weather

## When to Use

Use this skill when the task asks for current, historical, or forecast weather.

## Procedure

1. Confirm location and date range.
2. Use a current weather source.
3. Include timestamp and units.
4. Avoid overstating forecast certainty.

## Pitfalls

- Do not answer weather questions from memory.
- Do not omit the date for relative terms like today or tomorrow.

## Verification

- The response includes source, location, date, and units.
