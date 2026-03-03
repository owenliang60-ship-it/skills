---
name: review
description: 间隔重复复习系统。扫描Obsidian原子卡片，用FSRS-6算法安排复习，AI出题+评分。当用户说"review"、"复习"、"间隔重复"、"复习卡片"、"今天复习什么"时触发。
invocation: user
arguments:
  - name: mode
    description: "'start'（默认，扫描+复习）、'scan'（仅扫描新卡片）、'stats'（统计信息）"
    required: false
  - name: limit
    description: 单次最大卡片数，默认10
    required: false
  - name: topic
    description: 可选主题过滤，如"多巴胺"、"AI Agent"
    required: false
---

# /review Command

间隔重复复习系统 — 用 FSRS-6 算法复习 Obsidian 中的原子卡片（石头）。

## 定位

```
研究 → /note 存卡 → /review 复习 → 知识巩固
```

| Skill | 职责 | 输出 |
|-------|------|------|
| `/note` | 知识沉淀 — 研究摘要 + 原子卡片 | Obsidian 卡片组 |
| `/review` | 知识巩固 — 间隔重复复习 | 本地 review_state.json |
| `/journal` | 进度记录 — 做了什么 | 本地 journal + Obsidian journal |

## 文件路径

- **FSRS 引擎**: `~/.claude/skills/review/scripts/fsrs_engine.py`
- **状态文件**: `~/CC workspace/Research/.claude/review_state.json`

## Usage

```
/review                     # 扫描 + 复习（默认）
/review --mode=scan         # 仅扫描新卡片，不复习
/review --mode=stats        # 查看统计信息
/review --topic=多巴胺      # 只复习某主题
/review --limit=5           # 本次最多复习5张
```

## Behavior

### Step 1: 扫描注册新卡片

**每次 `/review` 自动执行（除 mode=stats）。**

#### 1a. 获取当前状态

```bash
python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  "~/CC workspace/Research/.claude/review_state.json" stats
```

从返回的 `known_card_ids` 得知已注册卡片。

#### 1b. 列出 Cards/ 目录发现新卡片

**唯一识别标准：文件名含【】= 原子卡片。**

```
obsidian files folder="Cards"
```

从返回的文件名列表中，过滤出文件名含 `【` 的文件 = 原子卡片候选。

如果用户指定了 topic，进一步过滤：文件名或后续读取的内容中包含 topic 关键词。

#### 1c. 排除已注册卡片

对比 `known_card_ids`，只保留未注册的新卡片。

#### 1d. 注册新卡片

对新卡片分批调用 `mcp__obsidian__read_multiple_notes`（每批 ≤ 10 个，批量读取允许使用 MCP）获取完整内容，然后批量注册：

```bash
echo '<JSON>' | python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  "~/CC workspace/Research/.claude/review_state.json" bulk_register
```

输入 JSON 格式：`[{"id": "Cards/{title}.md", "title": "...", "content": "..."}]`

**注意：始终使用 `bulk_register`（stdin JSON），即使只有一张卡片。不要使用 `register` CLI 命令注册含特殊字符的卡片内容。**

#### 1d-2. 为新注册卡片打 mastery/new 标签

对每张新注册的卡片，并行调用：
```
obsidian property:set path="Cards/{title}.md" name="tags" value="{existing_tags},mastery/new" type=list
```

#### 1e. 报告扫描结果

```
扫描完成 — 发现 N 张新卡片，卡片池共 M 张
```

**如果 mode=scan，到此结束。**

### Step 2: 获取待复习卡片

```bash
python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  "~/CC workspace/Research/.claude/review_state.json" due --limit <limit>
```

- 如果 0 张到期 → 显示"今天没有待复习的卡片"+ 下次复习日期 → 结束
- 如果 > 0 → 进入复习会话

如果用户指定了 `topic`，从到期卡片中过滤：
- 有 `domain/` 标签 → 精确匹配 `domain/{topic}`
- 无标签 → fallback 到标题/内容文本匹配

### Step 3: 复习会话（循环每张卡片）

#### 3a. 选择提问模式

- **新卡片**（reps=0）→ **强制提问模式**（用户还没见过内容，回忆无意义）
- **老卡片**（reps>0）→ **随机切换**：约 50% 回忆模式，50% 提问模式

#### 3b. 展示问题

**回忆模式：**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/8] 回忆模式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请凭记忆描述这张卡片的核心内容：

  【多巴胺】编码动机而非快乐
```

**提问模式：**
从卡片内容中提取一个关键知识点，生成具体问题：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/8] 提问模式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Kent Berridge 的研究区分了大脑中哪两套独立的奖励系统？
```

提问要求：
- 问题必须有明确答案（从卡片内容可得）
- 避免"是/否"问题
- 覆盖卡片核心知识点

**等待用户回答。**

#### 3b-2. 淘汰机制

如果用户回答"淘汰"、"skip"、"retire"或类似表达，执行淘汰流程而非评分：

1. 调用 retire 命令：
```bash
python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  "~/CC workspace/Research/.claude/review_state.json" retire \
  --id <card_id>
```

2. 更新 Obsidian 标签为 `mastery/retired`：
```
obsidian property:set path="Cards/{title}.md" name="tags" value="{updated_tags_with_mastery/retired}" type=list
```

3. 展示确认：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
已淘汰：【卡片标题】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
卡片保留在 Obsidian，不再出现在复习中。
```

4. 继续下一张卡片。

#### 3c. AI 评估回答

对照卡片原文（content_snippet），从三个维度评估：
1. **核心知识点覆盖率** — 提到了多少关键概念
2. **准确性** — 有无事实错误
3. **精确度** — 模糊印象 vs 精确回忆

评分映射：

| Rating | 值 | 条件 |
|--------|---|------|
| Again | 1 | 完全不记得 / 核心全错 |
| Hard | 2 | 方向对但关键细节缺失 >50% |
| Good | 3 | 核心知识点基本正确 |
| Easy | 4 | 完全准确含关键细节 |

#### 3d. 展示反馈 + 记录

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
评分：Good (3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

正确：wanting vs liking 的区分
遗漏：Salamone 的补充发现（多巴胺敲除鼠仍享受甜食）

卡片完整内容：
> [展示 content_snippet]

下次复习：3天后 (2026-02-23)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

记录评分：
```bash
python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  "~/CC workspace/Research/.claude/review_state.json" record \
  --id <card_id> --rating 3
```

**如果用户对评分有异议**（如"这个应该是 Hard"），用用户覆盖的评分重新调用 record。

#### 3d-2. 写回 mastery 标签到 Obsidian

每次 `record` 后，根据本次复习评分写回掌握等级到卡片 frontmatter：

| 标签 | 对应评分 | 含义 |
|------|----------|------|
| `mastery/new` | — | 从未复习 |
| `mastery/again` | Again (1) | 完全不记得 |
| `mastery/hard` | Hard (2) | 勉强想起，细节缺失 |
| `mastery/good` | Good (3) | 核心掌握 |
| `mastery/easy` | Easy (4) | 完全掌握 |
| `mastery/retired` | 淘汰 | 已从复习池移除 |

操作步骤（可与下一张卡片的提问并行）：

1. 读取当前标签：`obsidian tags path="Cards/{title}.md"`
2. 从结果中去掉旧 mastery 标签（mastery/new, mastery/again, mastery/hard, mastery/good, mastery/easy），加入新标签 `mastery/{level}`
3. 写回：`obsidian property:set path="Cards/{title}.md" name="tags" value="{updated_tags}" type=list`

> 仅当 Obsidian 应用未运行且 CLI 报 connection refused 时回退 MCP `mcp__obsidian__manage_tags`（remove + add 两步并行）。

#### 3e. 下一张卡片

继续下一张，直到所有到期卡片复习完或达到 limit。

### Step 4: 会话总结

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
复习完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

本次复习：8 张卡片
评分分布：Again 1 | Hard 2 | Good 4 | Easy 1
平均记忆保持率：82%

薄弱卡片：
- 【消退学习】— Again, 明天复习
- 【前额叶皮层】— Hard, 2天后复习

下次复习：明天有 3 张卡片到期
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

记录 session 到状态文件：

```bash
echo '{"date":"2026-02-20","cards_reviewed":8,"ratings":{"Again":1,"Hard":2,"Good":4,"Easy":1},"avg_retrievability":0.82}' | \
  python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  "~/CC workspace/Research/.claude/review_state.json" record_session
```

### Step 5: mode=stats 输出

```bash
python3 ~/.claude/skills/review/scripts/fsrs_engine.py \
  "~/CC workspace/Research/.claude/review_state.json" stats
```

格式化输出：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
复习统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

卡片池：M 张（新 X / 学习中 Y / 复习中 Z）
今日到期：N 张
下次到期：YYYY-MM-DD

历史评分分布：
Again: XX | Hard: XX | Good: XX | Easy: XX

平均难度：X.X / 10
平均稳定性：X.X 天

总复习次数：XX 次
总会话数：XX 次
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 关键规则

1. **等待用户回答** — 展示问题后必须等用户输入，不能自己回答
2. **评分可覆盖** — 用户说"这个应该是 Hard"时，用用户的评分
3. **一张一张来** — 不要批量展示，每次只展示一张卡片的问题
4. **展示完整内容** — 评分后必须展示卡片原文，帮助用户巩固
5. **状态文件路径固定** — 始终使用 `~/CC workspace/Research/.claude/review_state.json`

## Notes

- content_snippet 注册时固定，Obsidian 原卡修改后需重新 scan 同步
- FSRS 参数使用全局默认值，暂不做个性化训练
- 首次运行会自动创建 review_state.json
