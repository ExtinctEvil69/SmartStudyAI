"""Polaris — registry of all generic text/mermaid tools.

Adding a new tool = one entry here. The generic_tool router renders the UI
config from this file and runs the prompt template against Gemma.

Special tools that don't fit this pattern (GraphiQ, AudioOverview) live in
their own modules.
"""

TOOLS: dict[str, dict] = {

    # ── STUDY ────────────────────────────────────────────────────────────
    "paper_analyzer": {
        "name": "PaperAnalyzer",
        "icon": "📄",
        "category": "Study",
        "description": "Analyze research papers — extract claims, methods, results, limitations.",
        "input_label": "Paste paper content (abstract + body)",
        "input_type": "textarea",
        "options": [
            {"id": "depth", "label": "Depth", "type": "select",
             "values": ["Quick brief", "Detailed analysis", "Critical review"]},
        ],
        "system": "You are a meticulous research analyst skilled at evaluating academic literature.",
        "prompt": """Analyze this research paper. Output level: {depth}

Cover:
1. Main claims (1-3 sentences each)
2. Methodology & data
3. Key results with effect sizes if present
4. Limitations the authors admit + ones they don't
5. Implications for the field

Use structured markdown.

Paper:
{input}""",
        "output_kind": "markdown",
    },

    # ── CREATE ───────────────────────────────────────────────────────────
    "writewise": {
        "name": "WriteWise",
        "icon": "✍️",
        "category": "Create",
        "description": "Polish writing — grammar, clarity, structure, tone.",
        "input_label": "Your draft",
        "input_type": "textarea",
        "options": [
            {"id": "mode", "label": "Mode", "type": "select",
             "values": ["Edit for clarity", "Tighten (cut fluff)", "Make academic",
                        "Make conversational", "Restructure for flow"]},
        ],
        "system": "You are an elite writing coach. Preserve the author's voice; never invent facts.",
        "prompt": """Apply this edit: **{mode}**.
Keep meaning intact. Output the revised draft only — no commentary.

Original:
{input}""",
        "output_kind": "markdown",
    },

    "studio": {
        "name": "Studio",
        "icon": "🎨",
        "category": "Create",
        "description": "Study artifact factory — one click → flashcards, summary, mindmap, quiz.",
        "input_label": "Source content",
        "input_type": "textarea",
        "options": [
            {"id": "artifact", "label": "Artifact", "type": "select",
             "values": ["Flashcards (15)", "One-page cheatsheet", "Visual outline",
                        "Spaced-repetition card deck", "Lecture-ready slides outline"]},
        ],
        "system": "You produce polished, exam-ready study artifacts.",
        "prompt": "Create: **{artifact}** from the source below. Use clean markdown.\n\nSource:\n{input}",
        "output_kind": "markdown",
    },

    "multisource_synth": {
        "name": "MultiSourceSynth",
        "icon": "🔗",
        "category": "Create",
        "description": "Synthesize multiple sources with cross-citations.",
        "input_label": "Paste 2+ sources, each prefixed with `### Source N:`",
        "input_type": "textarea",
        "options": [
            {"id": "format", "label": "Format", "type": "select",
             "values": ["Compare & contrast", "Unified thesis", "Conflicting claims audit"]},
        ],
        "system": "You synthesize multiple sources faithfully and cite [Source N] inline.",
        "prompt": """Synthesize these sources. Format: **{format}**.
Cite every claim as [Source N]. Distinguish agreement from conflict.

Sources:
{input}""",
        "output_kind": "markdown",
    },

    # ── BUILD ────────────────────────────────────────────────────────────
    "codebuddy": {
        "name": "CodeBuddy",
        "icon": "👨‍💻",
        "category": "Build",
        "description": "Code explanation, debugging, refactoring suggestions.",
        "input_label": "Your code",
        "input_type": "textarea",
        "options": [
            {"id": "task", "label": "Task", "type": "select",
             "values": ["Explain line-by-line", "Find bugs", "Suggest refactor",
                        "Add type hints / docstrings", "Translate to another language"]},
            {"id": "lang", "label": "Language", "type": "text",
             "placeholder": "python, typescript, rust..."},
        ],
        "system": "You are a senior engineer who writes precise, production-quality explanations.",
        "prompt": """Task: **{task}**  ·  Language: {lang}

Code:
```
{input}
```

Be concrete. If you find bugs, show the fix as a unified diff.""",
        "output_kind": "markdown",
    },

    "dsa_sage": {
        "name": "DSASage",
        "icon": "🧮",
        "category": "Build",
        "description": "DSA tutor — problem analysis, complexity, intuition, solution.",
        "input_label": "Problem statement",
        "input_type": "textarea",
        "options": [
            {"id": "depth", "label": "Output depth", "type": "select",
             "values": ["Hint only", "Approach + complexity", "Full solution + tests"]},
            {"id": "lang", "label": "Solution language", "type": "select",
             "values": ["Python", "C++", "Java", "JavaScript"]},
        ],
        "system": "You are a competitive-programming coach. Always state time/space complexity.",
        "prompt": """Problem:
{input}

Output level: **{depth}**  ·  Language: {lang}

Format:
1. Restate the problem in your own words (1 sentence)
2. Key insight / pattern
3. Approach with reasoning
4. Time / space complexity
5. Solution code (if depth allows)
6. Edge cases tested""",
        "output_kind": "markdown",
    },

    "ideaspark": {
        "name": "IdeaSpark",
        "icon": "💡",
        "category": "Build",
        "description": "Generate project ideas in any domain, with scope & feasibility.",
        "input_label": "Domain / topic / interests",
        "input_type": "textarea",
        "options": [
            {"id": "level", "label": "Level", "type": "select",
             "values": ["Beginner", "Intermediate", "Advanced", "Hackathon (48h)"]},
            {"id": "count", "label": "Number of ideas", "type": "select",
             "values": ["3", "5", "8"]},
        ],
        "system": "You generate concrete, buildable project ideas — never vague concepts.",
        "prompt": """Generate **{count}** project ideas for: {input}
Level: **{level}**

For each idea provide:
- Title
- 1-sentence pitch
- Tech stack
- 3 core features
- Hardest part
- Stretch goal""",
        "output_kind": "markdown",
    },

    "feature_forge": {
        "name": "FeatureForge",
        "icon": "🛠️",
        "category": "Build",
        "description": "Brainstorm + spec product features with user-story format.",
        "input_label": "Product / problem description",
        "input_type": "textarea",
        "options": [
            {"id": "phase", "label": "Phase", "type": "select",
             "values": ["Brainstorm wide", "Prioritize MVP", "Detailed spec for one feature"]},
        ],
        "system": "You are a senior product manager. Output is concrete and testable.",
        "prompt": """Phase: **{phase}**

Product context:
{input}

Output a markdown table or specs with:
- Feature name
- User story: As <role>, I want <action>, so <outcome>
- Acceptance criteria
- Effort estimate (S/M/L)
- Risk / dependency""",
        "output_kind": "markdown",
    },

    # ── CODE (mermaid output — uses the same renderer as MindMapper) ─────
    "codeflow": {
        "name": "CodeFlow",
        "icon": "🔀",
        "category": "Code",
        "description": "Convert code into a Mermaid flowchart of control flow.",
        "input_label": "Your code",
        "input_type": "textarea",
        "options": [
            {"id": "style", "label": "Diagram", "type": "select",
             "values": ["Top-down flowchart", "Left-right flowchart", "Sequence diagram"]},
        ],
        "system": "You produce valid Mermaid.js syntax with no extra prose.",
        "prompt": """Generate a Mermaid **{style}** for this code's control flow.
Output ONLY the mermaid code block (no fences, no explanation).

Code:
```
{input}
```""",
        "output_kind": "mermaid",
    },

    "archviz": {
        "name": "ArchViz",
        "icon": "🏗️",
        "category": "Code",
        "description": "System / architecture diagram from a description.",
        "input_label": "System description",
        "input_type": "textarea",
        "options": [
            {"id": "style", "label": "Diagram type", "type": "select",
             "values": ["Component diagram (graph)", "Sequence diagram", "Class diagram", "C4 context"]},
        ],
        "system": "You produce valid Mermaid.js architecture diagrams.",
        "prompt": """Create a Mermaid **{style}** for this system. Output ONLY mermaid code.

System:
{input}""",
        "output_kind": "mermaid",
    },

    "logic_trace": {
        "name": "LogicTrace",
        "icon": "🔍",
        "category": "Code",
        "description": "Step-through execution trace for code or a bug report.",
        "input_label": "Code or bug report",
        "input_type": "textarea",
        "options": [
            {"id": "input_kind", "label": "Input kind", "type": "select",
             "values": ["Code execution", "Bug report triage"]},
        ],
        "system": "You trace logic precisely, like a debugger explaining each step.",
        "prompt": """Trace the **{input_kind}** below. Produce:
1. Mermaid sequence diagram of the trace (output as ```mermaid block first)
2. After the diagram, a numbered step-by-step explanation
3. Likely root cause / outcome

Input:
{input}""",
        "output_kind": "mermaid_with_text",
    },

    "code_audit": {
        "name": "CodeAudit",
        "icon": "🛡️",
        "category": "Code",
        "description": "Adversarial code review — bugs, security, perf, score. Assume nothing works.",
        "input_label": "Code to audit",
        "input_type": "textarea",
        "options": [
            {"id": "language", "label": "Language", "type": "text",
             "placeholder": "python, ts, rust, go, java..."},
            {"id": "context", "label": "Context", "type": "select",
             "values": ["Production code", "Hackathon prototype", "Learning exercise",
                        "Library / package", "CLI tool", "Web backend"]},
        ],
        "system": """You are a STRICT senior engineer doing an adversarial review.
You assume the code is broken until proven correct.
You find problems aggressively. You are not nice — you are accurate.""",
        "prompt": """ADVERSARIAL CODE REVIEW

Language: {language}
Context: {context}

Review with extreme scrutiny. Trace execution mentally. Look for:
1. Off-by-one errors, race conditions, null/None hazards
2. Security issues (injection, unvalidated input, hardcoded secrets, path traversal)
3. Performance traps (O(n²) where O(n) possible, unbounded recursion, leaks)
4. Error handling gaps (silent failures, broad except, swallowed exceptions)
5. Concurrency / state mutation issues
6. Code smells (dead code, magic numbers, shotgun surgery, unclear names)
7. Test coverage gaps for non-obvious cases

Output this exact structure in markdown:

## 🚨 Critical Bugs
(line N: <bug>, why it breaks, fix as unified diff or replacement code)

## 🔒 Security Issues
(severity, exploit scenario, mitigation)

## ⚡ Performance Concerns
(complexity now, complexity possible, refactor sketch)

## 👃 Code Smells
(specific line / pattern, why it's a smell)

## 🔧 Refactoring Suggestions
(prioritized, with effort estimate S/M/L)

## 📊 Verdict
- **Score:** X/10 with one-line justification
- **Ship?** READY / REQUEST CHANGES / REJECT
- **Top fix to do first:** <one concrete thing>

Code:
```
{input}
```""",
        "output_kind": "markdown",
    },

    "docgen": {
        "name": "DocGen",
        "icon": "📚",
        "category": "Code",
        "description": "Generate API / module / README documentation from code.",
        "input_label": "Code or module",
        "input_type": "textarea",
        "options": [
            {"id": "doc_type", "label": "Doc type", "type": "select",
             "values": ["README.md", "API reference", "Inline docstrings", "Architecture overview"]},
        ],
        "system": "You write clear, accurate technical documentation. Never invent APIs.",
        "prompt": """Generate **{doc_type}** for this code. Use markdown.

Code:
```
{input}
```""",
        "output_kind": "markdown",
    },
}


CATEGORIES = {
    "Study":  {"label": "Study",  "color": "#B4ADFF"},
    "Create": {"label": "Create", "color": "#56CCF2"},
    "Build":  {"label": "Build",  "color": "#2DD4BF"},
    "Code":   {"label": "Code",   "color": "#FFB84D"},
}


def get_tool(tool_id: str) -> dict | None:
    return TOOLS.get(tool_id)


def all_tools() -> dict[str, dict]:
    return TOOLS
