# /review — FSRS-6 Spaced Repetition

Never forget what you learn. The `/review` skill brings [FSRS-6](https://github.com/open-spaced-repetition/py-fsrs) spaced repetition directly into your Claude Code workflow.

## What It Does

When you type `/review`, the skill:

1. **Scans Heptabase** — discovers atomic cards created by `/note` (or manually)
2. **Schedules reviews** — FSRS-6 algorithm determines which cards are due today
3. **Quizzes you** — two modes: recall (title shown, describe from memory) or question (AI-generated question from content)
4. **Evaluates answers** — AI rates your response: Again / Hard / Good / Easy
5. **Updates schedule** — FSRS updates each card's stability and next review date

## Usage

```
/review                     # scan + review (default)
/review --mode=scan         # discover new cards only
/review --mode=stats        # show statistics
/review --topic=dopamine    # filter by topic
/review --limit=5           # max 5 cards this session
```

## How FSRS-6 Works

FSRS-6 models two card properties:
- **Stability (S)**: how long until 90% chance of recall — grows with successful reviews
- **Difficulty (D)**: intrinsic hardness — adjusts based on your ratings

The forgetting curve: `R(t) = (1 + factor × t / S)^(-w20)`

After each review, the algorithm computes the next interval by solving for when R drops to your target retention (default: 90%).

Rating → next interval (approximate, for a card with stability = 10 days):
- **Again**: ~1 day (lapse recovery)
- **Hard**: ~8 days
- **Good**: ~20 days
- **Easy**: ~40 days

## State File

Review progress is stored locally in `~/.claude/skills/review/state.json`. This file tracks:
- All registered cards (title, content snippet, FSRS state)
- Review history per card
- Session summaries

The file is created automatically on first run. You can back it up or move it — just update the path in `skill.md`.

## FSRS Engine

`scripts/fsrs_engine.py` is a pure Python implementation of FSRS-6, using only stdlib (no dependencies to install).

```bash
# CLI interface:
python3 fsrs_engine.py <state_file> <command> [args]

# Commands:
#   due --limit N                      list due cards
#   record --id ID --rating 1-4        record a review
#   bulk_register                      register cards from stdin JSON
#   record_session                     record session summary from stdin JSON
#   stats                              print statistics
```

## Card Discovery

The skill finds atomic cards via Heptabase semantic search, then filters by these heuristics:
- Title ≤ 50 characters
- Title does NOT contain "Research Summary"
- Body 50–3000 characters
- Body contains `【】` brackets or `**bold**`

Cards created by `/note` automatically match these criteria.

## Integration with `/note`

The complete knowledge flywheel:

```
Conversation
    ↓  /note
Heptabase: Research Summary + Atomic Cards
    ↓  /review (scans Heptabase)
FSRS scheduling → daily quiz sessions
    ↓
Long-term retention
```

## Requirements

- Claude Code with Heptabase MCP configured
- Python 3.7+ (for `fsrs_engine.py`)
- To use a different knowledge tool, see [CONTRIBUTING.md](../CONTRIBUTING.md)
