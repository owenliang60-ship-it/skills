# Claude Code Skills: Knowledge Flywheel

> Two Claude Code skills that close the loop between **capturing** and **retaining** knowledge.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## The Problem

You have great conversations with Claude — research breakthroughs, concept deep-dives, sudden insights. Then you forget them.

These two skills fix that:

| Skill | Role | What it does |
|-------|------|--------------|
| [`/note`](./note/) | Capture | Distills conversations into atomic knowledge cards → saves to Heptabase |
| [`/review`](./review/) | Retain | FSRS-6 spaced repetition over your Heptabase cards → AI quizzes you |

```
Conversation → /note → Heptabase cards → /review → Long-term memory
```

---

## Quick Start

**Step 1: Clone this repo**
```bash
git clone https://github.com/owenliang60-ship-it/skills.git
```

**Step 2: Copy skills to Claude Code**
```bash
cp -r skills/note ~/.claude/skills/note
cp -r skills/review ~/.claude/skills/review
```

**Step 3: Use them in any Claude Code session**
```
/note              # save this conversation to Heptabase
/review            # start today's spaced repetition session
```

---

## Prerequisites

- **[Claude Code](https://docs.anthropic.com/claude-code)** — Anthropic's CLI for Claude
- **[Heptabase MCP](https://heptabase.com/)** — the default knowledge backend (see [CONTRIBUTING.md](./CONTRIBUTING.md) to swap it out)

---

## Skills

### `/note` — Atomic Knowledge Capture

Turns any conversation into a **research summary + atomic cards**, saved to Heptabase.

The design philosophy: every `/note` produces two layers:
- **Map card** — a narrative summary that preserves the reasoning chain
- **Stone cards** — standalone atomic facts that can be reviewed independently

**Trigger words:** `note`, `make notes`, `save to heptabase`, `atomic notes`

→ [Full documentation](./note/README.md)

---

### `/review` — FSRS-6 Spaced Repetition

Scans your Heptabase atomic cards, schedules reviews using the **FSRS-6 algorithm**, and quizzes you with AI-generated questions.

Supports two quiz modes:
- **Recall mode** — describe the card from memory (title shown)
- **Question mode** — answer a specific question derived from the card content

**Trigger words:** `review`, `spaced repetition`, `what to review today`

→ [Full documentation](./review/README.md)

---

## Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Knowledge backend | Heptabase (default) | Best atomic card + linking UX; swappable via MCP |
| Review algorithm | FSRS-6 | State-of-the-art open-source SRS, pure Python stdlib |
| State storage | Local JSON | Simple, portable, no server needed |
| Language | Bilingual skill prompts | Skills work with any language |

---

## Contributing

Want to adapt these skills for Obsidian, Notion, or another knowledge tool? See [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](./LICENSE).
