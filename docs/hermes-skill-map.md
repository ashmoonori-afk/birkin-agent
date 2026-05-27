# Hermes Skill Reflection Map

Scope date: 2026-05-27.

Birkin reflects the Hermes Agent bundled `skills/` catalog at commit `bb4703c761ea6687b6399aa2e61e0a08fabd3ca3` as lightweight `hermes-<name>` capability markers.

These files are not vendored Hermes implementations. They preserve routing intent, source paths, and verification boundaries so a Birkin agent can choose or build a local adapter deliberately.

Excluded from this map: Hermes `optional-skills/`, plugins, generated website pages, and runtime internals.

Total reflected bundled skills: 90.

## Reflected Skills

### apple

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-apple-notes` | `skills/apple/apple-notes` | Manage Apple Notes via memo CLI: create, search, edit. |
| `hermes-apple-reminders` | `skills/apple/apple-reminders` | Apple Reminders via remindctl: add, list, complete. |
| `hermes-findmy` | `skills/apple/findmy` | Track Apple devices/AirTags via FindMy.app on macOS. |
| `hermes-imessage` | `skills/apple/imessage` | Send and receive iMessages/SMS via the imsg CLI on macOS. |
| `hermes-macos-computer-use` | `skills/apple/macos-computer-use` | Drive the macOS desktop in the background - screenshots, mouse, keyboard, scroll, drag - without stealing the user's cursor, keyboard focus, or Space. Works with any tool-capable model. Load this skill whenever the `computer_use` tool is available. |

### autonomous-ai-agents

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-claude-code` | `skills/autonomous-ai-agents/claude-code` | Delegate coding to Claude Code CLI (features, PRs). |
| `hermes-codex` | `skills/autonomous-ai-agents/codex` | Delegate coding to OpenAI Codex CLI (features, PRs). |
| `hermes-hermes-agent` | `skills/autonomous-ai-agents/hermes-agent` | Configure, extend, or contribute to Hermes Agent. |
| `hermes-kanban-codex-lane` | `skills/autonomous-ai-agents/kanban-codex-lane` | Use when a Hermes Kanban worker wants to run Codex CLI as an isolated implementation lane while Hermes keeps ownership of task lifecycle, reconciliation, testing, and handoff. |
| `hermes-opencode` | `skills/autonomous-ai-agents/opencode` | Delegate coding to OpenCode CLI (features, PR review). |

### creative

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-architecture-diagram` | `skills/creative/architecture-diagram` | Dark-themed SVG architecture/cloud/infra diagrams as HTML. |
| `hermes-ascii-art` | `skills/creative/ascii-art` | ASCII art: pyfiglet, cowsay, boxes, image-to-ascii. |
| `hermes-ascii-video` | `skills/creative/ascii-video` | ASCII video: convert video/audio to colored ASCII MP4/GIF. |
| `hermes-baoyu-article-illustrator` | `skills/creative/baoyu-article-illustrator` | Article illustrations: type style palette consistency. |
| `hermes-baoyu-comic` | `skills/creative/baoyu-comic` | Knowledge comics (): educational, biography, tutorial. |
| `hermes-baoyu-infographic` | `skills/creative/baoyu-infographic` | Infographics: 21 layouts x 21 styles (, ). |
| `hermes-claude-design` | `skills/creative/claude-design` | Design one-off HTML artifacts (landing, deck, prototype). |
| `hermes-comfyui` | `skills/creative/comfyui` | Generate images, video, and audio with ComfyUI - install, launch, manage nodes/models, run workflows with parameter injection. Uses the official comfy-cli for lifecycle and direct REST/WebSocket API for execution. |
| `hermes-design-md` | `skills/creative/design-md` | Author/validate/export Google's DESIGN.md token spec files. |
| `hermes-excalidraw` | `skills/creative/excalidraw` | Hand-drawn Excalidraw JSON diagrams (arch, flow, seq). |
| `hermes-humanizer` | `skills/creative/humanizer` | Humanize text: strip AI-isms and add real voice. |
| `hermes-ideation` | `skills/creative/creative-ideation` | Generate project ideas via creative constraints. |
| `hermes-manim-video` | `skills/creative/manim-video` | Manim CE animations: 3Blue1Brown math/algo videos. |
| `hermes-p5js` | `skills/creative/p5js` | p5.js sketches: gen art, shaders, interactive, 3D. |
| `hermes-pixel-art` | `skills/creative/pixel-art` | Pixel art w/ era palettes (NES, Game Boy, PICO-8). |
| `hermes-popular-web-designs` | `skills/creative/popular-web-designs` | 54 real design systems (Stripe, Linear, Vercel) as HTML/CSS. |
| `hermes-pretext` | `skills/creative/pretext` | Use when building creative browser demos with @chenglou/pretext - DOM-free text layout for ASCII art, typographic flow around obstacles, text-as-geometry games, kinetic typography, and text-powered generative art. Produces single-file HTML demos by default. |
| `hermes-sketch` | `skills/creative/sketch` | Throwaway HTML mockups: 2-3 design variants to compare. |
| `hermes-songwriting-and-ai-music` | `skills/creative/songwriting-and-ai-music` | Songwriting craft and Suno AI music prompts. |
| `hermes-touchdesigner-mcp` | `skills/creative/touchdesigner-mcp` | Control a running TouchDesigner instance via twozero MCP - create operators, set parameters, wire connections, execute Python, build real-time visuals. 36 native tools. |

### data-science

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-jupyter-live-kernel` | `skills/data-science/jupyter-live-kernel` | Iterative Python via live Jupyter kernel (hamelnb). |

### devops

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-kanban-orchestrator` | `skills/devops/kanban-orchestrator` | Decomposition playbook + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role. |
| `hermes-kanban-worker` | `skills/devops/kanban-worker` | Pitfalls, examples, and edge cases for Hermes Kanban workers. The lifecycle itself is auto-injected into every worker's system prompt as KANBAN_GUIDANCE (from agent/prompt_builder.py); this skill is what you load when you want deeper detail on specific scenarios. |
| `hermes-webhook-subscriptions` | `skills/devops/webhook-subscriptions` | Webhook subscriptions: event-driven agent runs. |

### dogfood

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-dogfood` | `skills/dogfood` | Exploratory QA of web apps: find bugs, evidence, reports. |

### email

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-himalaya` | `skills/email/himalaya` | Himalaya CLI: IMAP/SMTP email from terminal. |

### gaming

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-minecraft-modpack-server` | `skills/gaming/minecraft-modpack-server` | Host modded Minecraft servers (CurseForge, Modrinth). |
| `hermes-pokemon-player` | `skills/gaming/pokemon-player` | Play Pokemon via headless emulator + RAM reads. |

### github

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-codebase-inspection` | `skills/github/codebase-inspection` | Inspect codebases w/ pygount: LOC, languages, ratios. |
| `hermes-github-auth` | `skills/github/github-auth` | GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login. |
| `hermes-github-code-review` | `skills/github/github-code-review` | Review PRs: diffs, inline comments via gh or REST. |
| `hermes-github-issues` | `skills/github/github-issues` | Create, triage, label, assign GitHub issues via gh or REST. |
| `hermes-github-pr-workflow` | `skills/github/github-pr-workflow` | GitHub PR lifecycle: branch, commit, open, CI, merge. |
| `hermes-github-repo-management` | `skills/github/github-repo-management` | Clone/create/fork repos; manage remotes, releases. |

### mcp

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-native-mcp` | `skills/mcp/native-mcp` | MCP client: connect servers, register tools (stdio/HTTP). |

### media

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-gif-search` | `skills/media/gif-search` | Search/download GIFs from Tenor via curl + jq. |
| `hermes-heartmula` | `skills/media/heartmula` | HeartMuLa: Suno-like song generation from lyrics + tags. |
| `hermes-songsee` | `skills/media/songsee` | Audio spectrograms/features (mel, chroma, MFCC) via CLI. |
| `hermes-spotify` | `skills/media/spotify` | Spotify: play, search, queue, manage playlists and devices. |
| `hermes-youtube-content` | `skills/media/youtube-content` | YouTube transcripts to summaries, threads, blogs. |

### mlops

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-audiocraft-audio-generation` | `skills/mlops/models/audiocraft` | AudioCraft: MusicGen text-to-music, AudioGen text-to-sound. |
| `hermes-dspy` | `skills/mlops/research/dspy` | DSPy: declarative LM programs, auto-optimize prompts, RAG. |
| `hermes-evaluating-llms-harness` | `skills/mlops/evaluation/lm-evaluation-harness` | lm-eval-harness: benchmark LLMs (MMLU, GSM8K, etc.). |
| `hermes-huggingface-hub` | `skills/mlops/huggingface-hub` | HuggingFace hf CLI: search/download/upload models, datasets. |
| `hermes-llama-cpp` | `skills/mlops/inference/llama-cpp` | llama.cpp local GGUF inference + HF Hub model discovery. |
| `hermes-obliteratus` | `skills/mlops/inference/obliteratus` | OBLITERATUS: abliterate LLM refusals (diff-in-means). |
| `hermes-segment-anything-model` | `skills/mlops/models/segment-anything` | SAM: zero-shot image segmentation via points, boxes, masks. |
| `hermes-serving-llms-vllm` | `skills/mlops/inference/vllm` | vLLM: high-throughput LLM serving, OpenAI API, quantization. |
| `hermes-weights-and-biases` | `skills/mlops/evaluation/weights-and-biases` | W&B: log ML experiments, sweeps, model registry, dashboards. |

### note-taking

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-obsidian` | `skills/note-taking/obsidian` | Read, search, create, and edit notes in the Obsidian vault. |

### productivity

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-airtable` | `skills/productivity/airtable` | Airtable REST API via curl. Records CRUD, filters, upserts. |
| `hermes-google-workspace` | `skills/productivity/google-workspace` | Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python. |
| `hermes-linear` | `skills/productivity/linear` | Linear: manage issues, projects, teams via GraphQL + curl. |
| `hermes-maps` | `skills/productivity/maps` | Geocode, POIs, routes, timezones via OpenStreetMap/OSRM. |
| `hermes-nano-pdf` | `skills/productivity/nano-pdf` | Edit PDF text/typos/titles via nano-pdf CLI (NL prompts). |
| `hermes-notion` | `skills/productivity/notion` | Notion API + ntn CLI: pages, databases, markdown, Workers. |
| `hermes-ocr-and-documents` | `skills/productivity/ocr-and-documents` | Extract text from PDFs/scans (pymupdf, marker-pdf). |
| `hermes-powerpoint` | `skills/productivity/powerpoint` | Create, read, edit .pptx decks, slides, notes, templates. |
| `hermes-teams-meeting-pipeline` | `skills/productivity/teams-meeting-pipeline` | Operate the Teams meeting summary pipeline via Hermes CLI - summarize meetings, inspect pipeline status, replay jobs, manage Microsoft Graph subscriptions. |

### red-teaming

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-godmode` | `skills/red-teaming/godmode` | Jailbreak LLMs: Parseltongue, GODMODE, ULTRAPLINIAN. |

### research

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-arxiv` | `skills/research/arxiv` | Search arXiv papers by keyword, author, category, or ID. |
| `hermes-blogwatcher` | `skills/research/blogwatcher` | Monitor blogs and RSS/Atom feeds via blogwatcher-cli tool. |
| `hermes-llm-wiki` | `skills/research/llm-wiki` | Karpathy's LLM Wiki: build/query interlinked markdown KB. |
| `hermes-polymarket` | `skills/research/polymarket` | Query Polymarket: markets, prices, orderbooks, history. |
| `hermes-research-paper-writing` | `skills/research/research-paper-writing` | Write ML papers for NeurIPS/ICML/ICLR: designsubmit. |

### smart-home

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-openhue` | `skills/smart-home/openhue` | Control Philips Hue lights, scenes, rooms via OpenHue CLI. |

### social-media

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-xurl` | `skills/social-media/xurl` | X/Twitter via xurl CLI: post, search, DM, media, v2 API. |

### software-development

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-debugging-hermes-tui-commands` | `skills/software-development/debugging-hermes-tui-commands` | Debug Hermes TUI slash commands: Python, gateway, Ink UI. |
| `hermes-hermes-agent-skill-authoring` | `skills/software-development/hermes-agent-skill-authoring` | Author in-repo SKILL.md: frontmatter, validator, structure. |
| `hermes-hermes-s6-container-supervision` | `skills/software-development/hermes-s6-container-supervision` | Modify, debug, or extend the s6-overlay supervision tree inside the Hermes Agent Docker image - adding new services, debugging profile gateways, understanding the Architecture B main-program pattern. |
| `hermes-node-inspect-debugger` | `skills/software-development/node-inspect-debugger` | Debug Node.js via --inspect + Chrome DevTools Protocol CLI. |
| `hermes-plan` | `skills/software-development/plan` | Plan mode: write markdown plan to .hermes/plans/, no exec. |
| `hermes-python-debugpy` | `skills/software-development/python-debugpy` | Debug Python: pdb REPL + debugpy remote (DAP). |
| `hermes-requesting-code-review` | `skills/software-development/requesting-code-review` | Pre-commit review: security scan, quality gates, auto-fix. |
| `hermes-spike` | `skills/software-development/spike` | Throwaway experiments to validate an idea before build. |
| `hermes-subagent-driven-development` | `skills/software-development/subagent-driven-development` | Execute plans via delegate_task subagents (2-stage review). |
| `hermes-systematic-debugging` | `skills/software-development/systematic-debugging` | 4-phase root cause debugging: understand bugs before fixing. |
| `hermes-test-driven-development` | `skills/software-development/test-driven-development` | TDD: enforce RED-GREEN-REFACTOR, tests before code. |
| `hermes-writing-plans` | `skills/software-development/writing-plans` | Write implementation plans: bite-sized tasks, paths, code. |

### yuanbao

| Birkin skill | Hermes source | Upstream summary |
| --- | --- | --- |
| `hermes-yuanbao` | `skills/yuanbao` | Yuanbao () groups: @mention users, query info/members. |

## Use Notes

- Prefer native Birkin skills when they fully cover the task.
- Use a Hermes reflection when the task names a Hermes capability or when an adapter should be planned against that upstream skill.
- Verify any local binary, cloud account, OS integration, or token before executing the capability.
