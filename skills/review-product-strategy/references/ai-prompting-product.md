---
Category: competencies
Tags: [skill, ai, prompting, product-management, productivity]
---

# AI Prompting for Product

The skill of leveraging AI tools to accelerate and enhance product management work across strategy, design, and execution.

## Definition

AI prompting for product is the ability to effectively use AI tools (Claude, ChatGPT, Cursor, etc.) to become faster, smarter, and gain superpowers beyond traditional PM skills. It includes knowing where AI excels, where it falls short, and how to craft prompts that produce high-quality output.

## Core Principle: Shape the Output

AI defaults to consensus-driven, generic responses. To get specific, high-quality output:

1. **Show AI what greatness looks like** — Provide expert frameworks and examples
2. **Give concrete context** — Your domain, constraints, preferences
3. **Iterate and critique** — First output is a draft, not final

> Generic prompts yield generic results. These patterns shape output toward excellence.

## Why It Matters

| Benefit         | Description                      | Impact                                   |
| --------------- | -------------------------------- | ---------------------------------------- |
| **Faster**      | Tasks in minutes vs hours        | 10x speed on synthesis, analysis         |
| **Smarter**     | AI critique finds blind spots    | Better strategies, fewer gaps            |
| **Superpowers** | Do data analyst, researcher work | Answer all 10 data questions, not just 3 |

## Core Techniques

### 1. Train on Excellence

Generic prompts produce generic output. Train AI on what "great" looks like:

**Method:**
1. Find authoritative source (book, course, expert framework)
2. Summarize or paste into project knowledge
3. Ask AI to use those principles

**Example:**
```
Before critiquing my product strategy, summarize Michael Porter's 
competitive strategy framework. Then use those principles to 
evaluate my strategy.
```

**Application:** Strategy critique, interview scripts, evaluation criteria

### 2. Devil's Advocate Mode

AI defaults to being nice. Override this for honest feedback:

**System Prompt:**
```
Your task is to play devil's advocate and point out flaws or 
limitations in the provided [document]. Don't be nice. Point out 
in detail why this may not work, what questions remain unaddressed, 
and where it falls short.
```

**Application:** Strategy critique, spec review, decision validation

### 3. Natural Language → SQL

Connect AI directly to your database for instant data answers:

**Setup:**
1. Configure MCP server for your database
2. Optionally: provide 10-30 example question→SQL pairs
3. Ask questions in plain English

**Example:**
```
How many users activated each month for the last 12 months, 
segmented by acquisition channel?
```

**Application:** Ad-hoc analytics, dashboards, trend analysis

### 4. Automated Synthesis

Feed raw data and request structured output:

**Input:** CSV of Net Promoter Score (NPS) responses with segmentation data
**Prompt:** "Generate an NPS analysis report with: score trend, segment breakdown, theme analysis, executive summary"
**Output:** HTML report with interactive charts

**Application:** NPS analysis, survey synthesis, interview transcripts

### 5. Example-Based Learning

Provide input-output pairs to teach AI your patterns:

**Method:**
1. Document 10-30 examples of question → correct output
2. Add to AI project knowledge
3. AI pattern-matches new requests to examples

**Example for SQL:**
```
Question: "How many users signed up last month?"
SQL: SELECT COUNT(*) FROM users WHERE created_at >= DATE_TRUNC('month', NOW() - INTERVAL '1 month')
```

**Why it works:** AI learns your database quirks, naming conventions, and query patterns from examples rather than generic training.

**Application:** SQL queries, data analysis, any repeated task with patterns

### 6. Project Knowledge Training

For repeated tasks, create a persistent AI workspace:

**Setup:**
1. **System instructions** — Define task and tone
2. **Knowledge base** — Upload best practices, documentation
3. **Examples** — Show what great output looks like

**Example: Strategy Critique Project**
- Instructions: "Play devil's advocate, don't be nice"
- Knowledge: Product strategy course content, Porter's framework
- Examples: Well-critiqued strategy documents

**Result:** Every new conversation starts with expert context.

### 7. Vibe Coding Prototypes

Use AI coding tools to build functional prototypes without engineering:

**Workflow:**
1. Describe desired user experience in natural language
2. AI generates interactive, working prototype
3. Test with real users
4. Iterate before engineering involvement

**Application:** Feature validation, UX testing, stakeholder demos

## Applicability by PM Dimension

| Dimension | AI Strength         | Primary Techniques                                     |
| --------- | ------------------- | ------------------------------------------------------ |
| Vision    | Weak                | Limited — requires human judgment                      |
| Strategy  | Research + Critique | Train on Excellence, Devil's Advocate                  |
| Design    | Strong              | Natural Language SQL, Automated Synthesis, Vibe Coding |
| Execution | Strong              | Meeting automation, status generation                  |

## Anti-Patterns

### Generic Prompting

**Bad:** "Critique this product strategy"
**Result:** Vague, people-pleasing feedback

**Good:** "Using these product strategy best practices [attached], critique this strategy. Be specific about where it violates the bullseye principle and where competitive advantage claims are unsupported."

### Asking AI for Vision/Strategy Generation

AI gives consensus-driven ideas. Winning strategies require non-consensus bets.

**Bad:** "Write me a product strategy for [idea]"
**Good:** "Here's my product strategy. Research competitors and critique where my differentiation is weak."

## Common Pitfalls

| Pitfall               | Problem                            | Solution                            |
| --------------------- | ---------------------------------- | ----------------------------------- |
| **Generic prompts**   | Generic output                     | Train on excellence, be specific    |
| **Trusting blindly**  | AI can hallucinate, especially SQL | Verify queries, spot-check results  |
| **Forcing fit**       | Using AI where it's weak (vision)  | Know AI's limits, use for strengths |
| **No context**        | AI doesn't know your schema/domain | Provide examples, documentation     |
| **One-shot**          | Accepting first output             | Iterate, critique, refine           |
| **No knowledge base** | Retyping context every time        | Create project or skill             |

## Depth Progression

| Level     | Expectation                                                               |
| --------- | ------------------------------------------------------------------------- |
| **P1-P2** | Basic prompting for meeting summaries, documentation                      |
| **P3**    | Effective use for customer insights, data analysis                        |
| **P4+**   | Advanced techniques: custom tools, MCP integrations, systematic workflows |

## Tools Ecosystem

| Tool                  | Use Case               | PM Application                            |
| --------------------- | ---------------------- | ----------------------------------------- |
| **Claude Projects**   | Persistent context     | Strategy critique with knowledge base     |
| **Claude Code**       | Agentic coding         | Data analysis, prototype building, skills |
| **MCP Servers**       | External system access | Database queries, API integration         |
| **Cursor / Windsurf** | IDE-integrated AI      | Prototype development                     |
| **Gamma**             | Presentation AI        | Auto-generated exec decks                 |
| **Dovetail / Grain**  | Interview AI           | Customer insight synthesis                |
