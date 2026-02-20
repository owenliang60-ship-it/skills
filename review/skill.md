---
name: review
description: Spaced repetition review system. Scans Heptabase atomic cards, schedules reviews using the FSRS-6 algorithm, AI-generated questions + scoring. Triggered when user says "review", "spaced repetition", "what to review today", "review cards".
invocation: user
arguments:
  - name: mode
    description: "'start' (default: scan + review), 'scan' (discover new cards only), 'stats' (show statistics)"
    required: false
  - name: limit
    description: Maximum cards per session, default 10
    required: false
  - name: topic
    description: Optional topic filter, e.g. "dopamine", "AI Agent"
    required: false
---

# /review Command

Spaced repetition review system — reviews atomic cards (stones) in Heptabase using the FSRS-6 algorithm.

## Positioning

```
Research → /note saves cards → /review reviews → knowledge retained
```

| Skill | Role | Output |
|-------|------|--------|
| `/note` | Knowledge capture — research summary + atomic cards | Heptabase card set |
| `/review` | Knowledge retention — spaced repetition | Local `state.json` |
| `/journal` | Progress log — what was done | Local journal + Heptabase journal |

## File Paths

- **FSRS Engine**: `~/.claude/skills/review/scripts/fsrs_engine.py`
- **State File**: `~/.claude/skills/review/state.json`

> The state file is created automatically on first run. You can move it anywhere by passing a different path to `fsrs_engine.py` — but keep it consistent across sessions.

## Usage

```
/review                     # scan + review (default)
/review --mode=scan         # discover new cards only, no review
/review --mode=stats        # show statistics
/review --topic=dopamine    # only review cards matching a topic
/review --limit=5           # max 5 cards this session
```

## Behavior

### Step 1: Scan and Register New Cards

**Runs automatically every `/review` (except mode=stats).**

#### 1a. Get Current State

```bash
python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  ~/.claude/skills/review/state.json stats
```

Read `known_card_ids` from the response to know which cards are already registered.

#### 1b. Search Heptabase for New Cards

Use `mcp__heptabase__semantic_search_objects` in multiple waves:

> **Default MCP: Heptabase** — calls `mcp__heptabase__semantic_search_objects` and `mcp__heptabase__get_object`
> To use a different knowledge tool, see [CONTRIBUTING.md](../CONTRIBUTING.md).

**Wave 1 — Domain keywords (always run)**:
```
queries: ["knowledge point research finding", "mechanism concept principle"]
resultObjectTypes: ["card"]
```

**Wave 2 — Expand from known cards (if cards already exist)**:
Extract 【】 keywords from registered card titles, use them as search queries.

**Wave 3 — Topic-targeted (if user specified topic)**:
```
queries: ["<topic> knowledge point", "<topic> mechanism principle"]
resultObjectTypes: ["card"]
```

#### 1c. Filter for Atomic Cards (stones vs. maps)

From search results, keep only atomic cards:
- Title ≤ 50 characters
- Title does NOT contain "Research Summary"
- Body 50–3000 characters
- Contains 【】 markers or bold (`**`)

Exclude already-registered cards (compare against `known_card_ids`).

#### 1d. Register New Cards

For each new card, fetch full content with `mcp__heptabase__get_object`, then batch-register:

```bash
echo '<JSON>' | python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  ~/.claude/skills/review/state.json bulk_register
```

Input JSON format: `[{"id": "<hb_id>", "title": "...", "content": "..."}]`

**Always use `bulk_register` (stdin JSON), even for a single card. Do not use the `register` CLI command for cards with special characters.**

#### 1e. Report Scan Results

```
Scan complete — discovered N new cards, pool now has M cards
```

**If mode=scan, stop here.**

### Step 2: Get Cards Due for Review

```bash
python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  ~/.claude/skills/review/state.json due --limit <limit>
```

- 0 cards due → show "No cards due today" + next review date → stop
- > 0 cards → enter review session

If user specified `topic`, filter the due cards by title/content match.

### Step 3: Review Session (one card at a time)

#### 3a. Choose Quiz Mode

- **New card** (reps=0) → **Force question mode** (user hasn't seen content yet, recall is meaningless)
- **Old card** (reps>0) → **Random switch**: ~50% recall mode, ~50% question mode

#### 3b. Present the Question

**Recall mode:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/8] Recall mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

From memory, describe the core content of this card:

  【dopamine】encodes motivation, not pleasure
```

**Question mode:**
Extract a key knowledge point from the card content and generate a specific question:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/8] Question mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What two independent reward systems did Kent Berridge's research distinguish in the brain?
```

Question requirements:
- Must have a definite answer (derivable from card content)
- Avoid yes/no questions
- Cover the card's core knowledge point

**Wait for user's answer.**

#### 3c. AI Evaluates the Answer

Compare against the card's original text (`content_snippet`), evaluate on three dimensions:
1. **Core knowledge coverage** — how many key concepts were mentioned
2. **Accuracy** — any factual errors
3. **Precision** — vague impression vs. precise recall

Rating mapping:

| Rating | Value | Condition |
|--------|-------|-----------|
| Again | 1 | Completely forgotten / core entirely wrong |
| Hard | 2 | Right direction but >50% key details missing |
| Good | 3 | Core knowledge points basically correct |
| Easy | 4 | Fully accurate including key details |

#### 3d. Show Feedback + Record

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rating: Good (3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Correct: wanting vs liking distinction
Missed: Salamone's supplementary finding (dopamine-depleted mice still enjoy sweet food)

Full card content:
> [content_snippet]

Next review: in 3 days (2026-02-23)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Record the rating:
```bash
python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  ~/.claude/skills/review/state.json record \
  --id <card_id> --rating 3
```

**If user disputes the rating** (e.g., "this should be Hard"), re-call record with the user's override.

#### 3e. Next Card

Continue to the next card until all due cards are reviewed or limit is reached.

### Step 4: Session Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Review Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This session: 8 cards
Rating breakdown: Again 1 | Hard 2 | Good 4 | Easy 1
Avg retrievability: 82%

Weak cards:
- 【extinction learning】— Again, review tomorrow
- 【prefrontal cortex】— Hard, review in 2 days

Next review: 3 cards due tomorrow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Record session to state file:

```bash
echo '{"date":"YYYY-MM-DD","cards_reviewed":8,"ratings":{"Again":1,"Hard":2,"Good":4,"Easy":1},"avg_retrievability":0.82}' | \
  python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  ~/.claude/skills/review/state.json record_session
```

### Step 5: mode=stats Output

```bash
python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  ~/.claude/skills/review/state.json stats
```

Formatted output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Review Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Card pool: M cards (new X / learning Y / review Z)
Due today: N cards
Next due: YYYY-MM-DD

Historical rating breakdown:
Again: XX | Hard: XX | Good: XX | Easy: XX

Avg difficulty: X.X / 10
Avg stability: X.X days

Total reviews: XX
Total sessions: XX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Key Rules

1. **Wait for user's answer** — after presenting a question, must wait for user input; never answer for them
2. **Rating is overridable** — when user says "this should be Hard", use their rating
3. **One card at a time** — never batch-display; show one card's question per turn
4. **Show full content** — after rating, always show the original card text to reinforce learning
5. **State file path is fixed** — always use `~/.claude/skills/review/state.json` (unless you deliberately moved it)

## Notes

- Heptabase semantic search returns ~45 results max per query; large card pools need multiple sessions to fully discover
- `content_snippet` is fixed at registration time; edits to the original HB card do not sync automatically
- FSRS parameters use global defaults; no personalized training currently
- First run auto-creates `state.json`
