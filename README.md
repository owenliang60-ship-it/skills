# Knowledge MEMO: Future-Proof Personal Knowledge Engineering

> 知识MEMO化 — 让每一次阅读、每一次对话、每一个洞察，都变成可检索、可复习、可复利的资产。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## The Vision

We read constantly — papers, articles, conversations with AI — yet most knowledge evaporates within days.

**Knowledge MEMO** is a system of four Claude Code skills that form a closed-loop knowledge engine: **acquire → analyze → capture → retain**. It turns ephemeral reading into compounding intellectual capital.

```
        ┌─────────────────────────────────────────┐
        │         Knowledge MEMO Flywheel          │
        │                                          │
        │   /read ──→ /insights ──→ /note ──→ /review
        │   (理解)     (洞察)       (沉淀)     (巩固)
        │      ↑                                │
        │      └────────────────────────────────┘
        │              feedback loop               │
        └─────────────────────────────────────────┘
```

The thesis: **the bottleneck of personal knowledge is not access — it's retention and retrieval.** LLMs solved access. These skills solve the rest.

---

## The Four Skills

| Skill | Role | Input | Output |
|-------|------|-------|--------|
| [`/read`](./read/) | **Acquire** — deep reading | Papers, articles, PDFs | Structured analysis report |
| [`/insights`](./insights/) | **Analyze** — extract patterns | Business articles, reports | Actionable insights → Obsidian |
| [`/note`](./note/) | **Capture** — atomic distillation | Any conversation or research | Map (summary) + Stones (atomic cards) → Obsidian |
| [`/review`](./review/) | **Retain** — spaced repetition | Obsidian atomic cards | FSRS-6 scheduled quizzes |

Each skill is standalone. Together they form a flywheel.

---

## Quick Start

**1. Clone**
```bash
git clone https://github.com/owenliang60-ship-it/skills.git
```

**2. Install all skills**
```bash
cp -r skills/read ~/.claude/skills/read
cp -r skills/insights ~/.claude/skills/insights
cp -r skills/note ~/.claude/skills/note
cp -r skills/review ~/.claude/skills/review
```

**3. Use in any Claude Code session**
```
/read https://arxiv.org/abs/...     # deep-read a paper
/insights https://blog.com/...      # extract business insights from an article
/note                               # distill this conversation into atomic cards
/review                             # start today's spaced repetition session
```

---

## Prerequisites

- **[Claude Code](https://docs.anthropic.com/claude-code)** — Anthropic's CLI for Claude
- **[Obsidian](https://obsidian.md/)** + **Obsidian MCP server** — the knowledge backend for card storage, search, and tagging
- **Python 3** — for the FSRS-6 review engine (stdlib only, no dependencies)

---

## How the Flywheel Works

### /read — Understand Deeply

Simulates an expert reader's process: scan structure → trace arguments → evaluate methods → critique logic. Outputs a structured report you can discuss, then feed into `/note`.

- Supports: URLs, PDFs, Obsidian notes, pasted text
- Modes: `quick` (5-min overview) or `deep` (full analysis)
- Special lenses: `rosetta`, `method`, `critique`

### /insights — See What Others Miss

Reads business content like an analyst: surface information → deep logic → transferable patterns. Auto-saves to Obsidian.

- Focus modes: `general`, `ai`, `strategy`, `model`
- Every insight has three layers: evidence → logic → transferable pattern
- Prioritizes counter-intuitive and non-obvious findings

### /note — Crystallize Knowledge

Distills any conversation into two layers:
- **Map** — a narrative summary preserving the reasoning chain
- **Stones** — standalone atomic cards, each a single idea with `【】` markers for bi-directional linking

### /review — Make It Stick

FSRS-6 spaced repetition over your Obsidian atomic cards. AI generates questions, evaluates your answers, and schedules the next review.

- Two quiz modes: recall (describe from memory) and question (answer a specific question)
- Mastery tracking via Obsidian tags: `mastery/new` → `mastery/again` → `mastery/good` → `mastery/easy`
- Priority: learning cards (need reinforcement) > review cards (scheduled) > new cards

---

## Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Knowledge backend | Obsidian + MCP | Local-first, markdown-native, excellent linking |
| Note structure | Map + Stones | Summaries preserve context; atoms enable review and reuse |
| Review algorithm | FSRS-6 | State-of-the-art open-source SRS; pure Python stdlib |
| State storage | Local JSON | Simple, portable, no server needed |
| Insight storage | Auto-save to Obsidian | Zero-friction; analysis is the artifact |

---

## Philosophy

Knowledge MEMO is built on three beliefs:

1. **Reading without retention is entertainment, not learning.** The flywheel closes the gap.
2. **Atomic beats monolithic.** A single idea per card is harder to write but infinitely more useful.
3. **AI should augment the loop, not replace it.** The skills generate questions and structure — but *you* do the remembering.

---

## Contributing

Want to adapt these skills for Notion, Logseq, or another knowledge tool? See [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](./LICENSE).
