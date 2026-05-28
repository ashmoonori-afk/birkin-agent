---
name: hermes-vllm
description: "vLLM: high-throughput LLM serving, OpenAI API, quantization."
version: 0.2.0
platforms: [linux, macos]
metadata: {"birkin":{"alwaysInclude":true,"capabilityLevel":"upstream-skill","upstreamMirror":"skills/upstream/hermes/mlops/inference/vllm"},"hermes":{"category":"mlops","tags":["hermes","bundled-skill","upstream-skill"],"upstreamCommit":"2d5dcfabc312d43f87a4f0f44c45f62cf24a09b2","upstreamPath":"skills/mlops/inference/vllm","upstreamSkill":"vllm"}}
---

# Hermes Upstream Skill: vllm

## Birkin Integration

The exact upstream skill directory is mirrored at `skills/upstream/hermes/mlops/inference/vllm`.

When a run asks to include skill bodies, Birkin loads the mirrored upstream `SKILL.md` from that directory.

## Verification

- Upstream source: `skills/mlops/inference/vllm`
- Upstream commit: `2d5dcfabc312d43f87a4f0f44c45f62cf24a09b2`
- The mirrored directory contains the exact upstream files fetched by `tools/sync_upstream_skills.py`.
