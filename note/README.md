# /note — Atomic Knowledge Capture

Turn any Claude Code conversation into a durable knowledge artifact.

## What It Does

When you type `/note`, the skill:

1. **Scans the conversation** — identifies the research arc, key findings, and quotable knowledge points
2. **Writes a Research Summary** — a narrative "map" card that preserves the full reasoning chain
3. **Extracts Atomic Cards** — standalone "stone" cards, one concept each, designed for spaced repetition
4. **Saves to Heptabase** — all cards saved via MCP in one shot
5. **Asks for confirmation** — shows you the card list before saving (can skip with "just save it")

## Usage

```
/note                    # save everything from this conversation
/note --topic=dopamine   # limit to a specific topic
/note --scope=last       # only the most recent discussion
```

## Output Format

### Research Summary (Map)

```markdown
# [Topic] — Research Summary

> Date: 2026-01-15 | Source: article analysis

## Background
...

## Key Findings
### [Sub-topic]
...

## Key Conclusions
1. ...

## Related Concepts
【concept-1】【concept-2】
```

### Atomic Card (Stone)

```markdown
# 【Dopamine】encodes motivation, not pleasure

Wolfram Schultz's landmark experiments showed that dopamine neurons fire in
anticipation of reward, not at reward delivery...

> Reference: conversation 2026-01-15
```

## Why Map + Stones?

- **Map alone**: you can navigate, but you can't build — too dense to review
- **Stones alone**: you have facts, but no context — you don't know why they matter
- **Map + Stones**: the summary explains why each stone is important; the stones become searchable and reviewable

The `/review` skill reads stones, not maps — this is intentional.

## Linking Convention

- `【Key Term】` — marks concepts that become their own stone cards (bidirectional linking)
- `**bold**` — marks core conclusions within a card
- Combined: `**【extinction learning】is the neuroscientific basis of memory reconsolidation**`

These conventions make cards discoverable by `/review`'s search heuristics.

## Integration with `/review`

Cards created by `/note` are automatically discovered by `/review` via Heptabase semantic search. The filter:
- Title ≤ 50 chars
- Title does NOT contain "Research Summary"
- Contains `【】` or `**` markers
- Body 50–3000 chars

As long as your atomic cards follow the format, `/review` will find and schedule them.

## Requirements

- Claude Code with Heptabase MCP configured
- To use a different knowledge tool, see [CONTRIBUTING.md](../CONTRIBUTING.md)
