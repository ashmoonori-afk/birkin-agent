---
name: image-lab
description: Prepare image-generation or image-editing workflows with asset provenance and QA notes.
version: 0.1.0
platforms: [windows, linux, macos]
metadata: {"hermes": {"tags": ["image", "creative"], "category": "creative"}, "openclaw": {"alwaysInclude": true}}
---

# Image Lab

## When to Use

Use this skill when a workflow creates, edits, or verifies bitmap image assets.

## Procedure

1. Define image purpose, dimensions, style, and usage constraints.
2. Keep generated assets in a dedicated workspace path.
3. Record prompts or source references when provenance matters.
4. Verify the asset appears correctly in the target UI or document.

## Pitfalls

- Do not use generated images as factual evidence.
- Do not leave temporary assets in the repo root.

## Verification

- The asset path and usage context are documented.
