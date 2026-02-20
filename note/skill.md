---
name: note
description: Distills conversation content into a research summary + atomic knowledge cards, saved to Heptabase. The summary is the map; the cards are the stones. Use bold and 【】 brackets for key terms to enable bi-directional linking. Triggered when user says "note", "make notes", "save to heptabase", "atomic notes", "store this".
invocation: user
arguments:
  - name: topic
    description: Optional topic scope. If not provided, automatically extracts all noteworthy content from the current conversation.
    required: false
  - name: scope
    description: "Optional scope: 'all' (entire conversation), 'last' (most recent discussion), 'select' (let user choose). Default: 'all'"
    required: false
---

# /note Command

Distills conversation content into a **research summary + atomic knowledge cards**, saved to Heptabase.

## Core Philosophy: Map + Stones

Every `/note` produces two layers:

1. **Research Summary (Map)** — A complete, narrative card that preserves the conversation's arc, reasoning chain, and conclusions. Reading this card alone should recover 80% of the conversation's value.
2. **Atomic Cards (Stones)** — Independent knowledge units extracted from the summary. Each card stands alone, reusable without context. The summary references these cards via keyword markers.

**The map makes the stones meaningful; the stones make the map linkable.**

## Skill Positioning

| Skill | Role | Output |
|-------|------|--------|
| `/note` | Knowledge capture — research summary + atomic cards | Heptabase card set |
| `/log` | Memory capture — decisions, preferences, insights | Long-term memory file |
| `/journal` | Progress log — what was done | Local journal + Heptabase journal |

## Bi-directional Link Notation

- **【Key Term】**: Academic concepts, theory names, proper nouns, model names, genes/molecules/drugs
  - e.g.: 【reward prediction error】, 【Kent Berridge】, 【COMT Val158Met】, 【SSRI】
- **Bold**: Core conclusions or key insights
  - e.g.: **dopamine encodes "is it worth the effort", not pleasure itself**
- Both can be combined: **【extinction learning】is the neuroscientific basis of memory reconsolidation**

### Notation Quick Reference

| Content Type | Marker | Example |
|-------------|--------|---------|
| Academic concept / theory | 【】 | 【reward prediction error】, 【implementation intentions】 |
| Proper noun / person | 【】 | 【Wolfram Schultz】, 【Berridge】 |
| Gene / molecule / drug | 【】 | 【DRD4】, 【COMT】, 【SSRI】 |
| Core conclusion | **bold** | **receptor density 67% determined by genetics** |
| Key distinction | **bold** | **wanting ≠ liking** |
| Important concept + conclusion | combined | **【anhedonia】is the core feature of depression** |

## Behavior

### Step 1: Scan the Conversation, Understand the Research Arc

Review the conversation (or specified scope) and identify:
- What prompted the research and what the topic is
- What phases or turning points the discussion went through
- What key conclusions were reached
- Which knowledge points deserve their own standalone card

### Step 2: Write the Research Summary (Map Card)

The research summary is a **complete, detailed** card with this structure:

```markdown
# [Research Topic] — Research Summary

> Date: YYYY-MM-DD | Source: [conversation origin, e.g. "analysis of an article", "exploring a question"]

## Background

[1-2 paragraphs: why this topic was researched, what prompted it]

## Key Findings

### [Sub-topic 1]

[Detailed content: preserve key arguments, data, reasoning chain. Not abbreviated — refined. Remove redundancy but keep substance.]

### [Sub-topic 2]

[Same as above]

### [Sub-topic N]

[Same as above]

## Key Conclusions

[3-5 most important takeaways, numbered list]

## Open Questions

[Questions that surfaced but weren't explored deeply, for future investigation]

## Related Concepts

【Concept 1】【Concept 2】【Concept 3】... (list all keywords corresponding to atomic cards, as bi-link entry points)
```

**Summary writing principles:**

- **Completeness first**: Better longer than missing key information
- **Preserve reasoning chains**: Not just conclusions, but "why we reached this conclusion"
- **Preserve data**: Specific numbers, experimental designs, percentages — don't omit
- **Preserve disagreements**: If the conversation challenged or revised a view, record that process too
- **Natural 【】 embedding**: Use 【】 markers naturally in prose; they simultaneously serve as "signposts" pointing to atomic cards

### Step 3: Extract Atomic Cards (Stones)

From the research summary, extract knowledge points that deserve to stand alone. Each card structure:

```markdown
# [Card Title — declarative sentence containing 【keyword】, ≤ 50 chars]

[Body: 1-3 paragraphs, 50–3000 words, explaining this one concept clearly. Must use 【】 for proper nouns and **bold** for core conclusions.]

> Reference: [source]
```

**Hard format requirements (ensures `/review` can discover them):**
- Title ≤ 50 characters, contains at least one 【keyword】
- Body 50–3000 characters, contains at least one 【】 or `**` marker
- Title does NOT contain "Research Summary" (that's the map card identifier)

**Extraction priority (high → low):**

1. Factual knowledge — empirically supported scientific findings, data
2. Conceptual frameworks — theoretical models, classification systems
3. Causal mechanisms — A → B mechanism chains
4. Counter-intuitive insights — findings that contradict common sense
5. Actionable methods — executable strategies
6. Meta-cognition — insights about thinking itself

**Do NOT extract:**
- Pure subjective judgments
- Transitional discussion
- Information that was corrected or retracted

**Atomicity judgment:**
- Can it be understood independently without context? → Granularity is correct
- Does it contain two separately-citable concepts? → Split it
- Would splitting leave either half unable to stand alone? → Don't split

### Step 4: Show Summary, Wait for Confirmation

Present to the user:

```
Ready to create 1 research summary + N atomic cards:

📄 Research Summary: [title]

Atomic Cards:
1. [Card title 1] — [one sentence description]
2. [Card title 2] — [one sentence description]
...

Confirm save to Heptabase? (can adjust: remove / merge / add)
```

**Wait for user confirmation before Step 5.** If user says "just save it", skip confirmation.

### Step 5: Save to Heptabase

> **Default MCP: Heptabase** — calls `mcp__heptabase__save_to_note_card`
> To use a different knowledge tool, see [CONTRIBUTING.md](../CONTRIBUTING.md) for how to swap the MCP calls.

1. **Save research summary first** (call `mcp__heptabase__save_to_note_card`)
2. **Then save all atomic cards in parallel** (multiple parallel calls)

### Step 6: Output Confirmation

```
---
Saved to Heptabase: 1 summary + N atomic cards

📄 [Summary title]

1. ✓ [Card title 1]
2. ✓ [Card title 2]
...

Keyword index: 【term1】【term2】【term3】...
---
```

## Special Scenarios

### Article Analysis Conversations

The summary should include:
- The original article's core arguments (marking which are correct/incorrect)
- Fact-checking conclusions and evidence
- Overall assessment (accuracy, value, limitations)

Atomic cards: only extract knowledge points that survive fact-checking, or clearly label contested concepts.

### Conversations That Produced Comparison Tables or Frameworks

**Preserve table format** as a single atomic card — don't force it into prose. The table itself is atomic; its value lies in the parallel comparison.

### Multi-Topic Conversations

If a conversation covered multiple unrelated topics, create **multiple research summaries** — one per topic — each with its own atomic cards.

## Notes

- Atomic cards: recommend no more than 15 per session; if more, confirm priorities with user
- Research summary: no length limit, completeness is the principle
- 【】 markers should appear in both summary and atomic cards — the summary's 【】 are signposts pointing to atomic cards
- The same 【keyword】 appearing in multiple cards is normal and intended — this is exactly how bi-directional linking creates value
