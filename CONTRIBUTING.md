# Contributing

## Adapting Skills to a Different Knowledge Tool

These skills default to **Heptabase** as the knowledge backend, accessed via its MCP server. If you use Obsidian, Notion, Logseq, or any other tool with an MCP server, you can swap out the MCP calls.

### Required MCP Operations

Both skills rely on three conceptual operations:

| Operation | What it does | Heptabase MCP call |
|-----------|-------------|-------------------|
| **Save card** | Create a new note/card | `mcp__heptabase__save_to_note_card` |
| **Search cards** | Find cards by semantic query | `mcp__heptabase__semantic_search_objects` |
| **Get card** | Retrieve full card content | `mcp__heptabase__get_object` |

### How to Adapt `/note`

In `note/skill.md`, Step 5 calls `mcp__heptabase__save_to_note_card` to save each card. Replace this with your MCP's equivalent save operation.

**Example for a hypothetical Obsidian MCP:**
```
# Original (Heptabase)
mcp__heptabase__save_to_note_card(content="# Card Title\n\n...")

# Adapted (Obsidian hypothetical)
mcp__obsidian__create_note(path="Knowledge/Card Title.md", content="# Card Title\n\n...")
```

### How to Adapt `/review`

In `review/skill.md`, Step 1 uses two MCP calls to discover cards:
- `mcp__heptabase__semantic_search_objects` — find cards by topic
- `mcp__heptabase__get_object` — fetch full content for registration

Replace these with your MCP's search and read operations.

The FSRS engine (`review/scripts/fsrs_engine.py`) is pure Python and MCP-agnostic — no changes needed there.

### Filtering Atomic Cards

The `/review` skill identifies "atomic cards" (vs. summary cards) by these heuristics:
- Title ≤ 50 characters
- Title does NOT contain "research summary" or similar map-card markers
- Content is 50–3000 characters
- Content contains `【】` brackets or `**bold**` markers

If your knowledge tool uses different conventions for atomic cards, update the filter logic in `review/skill.md` Step 1c.

---

## Submitting a PR

Have you adapted these skills for another tool and want to share?

1. Fork the repo
2. Add your adapted skill under `note/adapters/<tool-name>/` or `review/adapters/<tool-name>/`
3. Include a short README explaining the MCP requirements
4. Open a PR — adapters for popular tools (Obsidian, Notion, Logseq) are especially welcome

---

## Improving the FSRS Engine

The engine in `review/scripts/fsrs_engine.py` implements FSRS-6 using only Python stdlib. Improvements welcome:
- Better short-term learning (lapse recovery) logic
- Personalized parameter optimization
- Export/import from other SRS tools (Anki, etc.)

Please include unit tests for any changes to the core math.
