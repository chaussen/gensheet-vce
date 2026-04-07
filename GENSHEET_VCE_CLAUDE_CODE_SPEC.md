# GenSheet VCE — Claude Code Build Spec

**Product name:** GenSheet VCE
**Repo:** github.com/chaussen/gensheet-vce (new repo, separate from gensheet-drill)
**Purpose:** VCE Specialist Maths exam practice for Year 12 students.
**MVP goal:** Generate questions, show curriculum context, let students self-assess.
**No answer checking. No automated marking. No AI marking.**

---

## Step 0: Discovery

Before writing any code:
```bash
ls -la
cat package.json 2>/dev/null || cat requirements.txt 2>/dev/null || echo "blank repo"
```
Adapt to what you find. If blank, scaffold from scratch.

---

## What we are NOT building

- Automated answer checking
- Answer input fields (except a self-assessment rating)
- Subscription or payment
- Database or auth
- Mobile-specific layout

---

## What we ARE building

A question generation tool with two session types:

**1. Extended Response drill**
Mirrors VCE Specialist Exam 1 style. Generate 2–3 multi-part questions
on a chosen topic. Each question shows:
- The question text (LaTeX rendered via KaTeX)
- Curriculum context (what topic and skill this tests)
- A "Strategy hint" (first step only — not the solution)
- A "Show worked solution" button (reveals full solution after student attempts)
- A self-assessment: "How did you go? ✗ / ~ / ✓" (3-way radio)

**2. MCQ drill**
Mirrors Exam 2 Section A. Generate 5 MCQ questions on a chosen topic.
Student selects A/B/C/D for each. All feedback shown at the end.

Session summary at the end shows: self-assessed correct count (Extended)
or actual correct count (MCQ), per-question results, and a "Try again" button.

---

## Tech stack

- **Backend:** FastAPI (Python)
- **Frontend:** React 18 + Vite + Tailwind CSS (served as static by FastAPI)
- **AI:** Anthropic API, model: `claude-sonnet-4-6` for Extended Response,
  `claude-haiku-4-5-20251001` for MCQ (MCQ is simpler, Haiku is fine)
- **Math rendering:** KaTeX via CDN in the React frontend
- **Env vars:** `ANTHROPIC_API_KEY`
- **Deploy:** Render (single web service, same pattern as GenSheet Drill)

---

## File structure

```
/
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── extended.py       # /api/extended/* endpoints
│   │   └── mcq.py            # /api/mcq/* endpoints
│   └── services/
│       ├── extended_engine.py
│       └── mcq_engine.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── HomeScreen.jsx
│   │   │   ├── ExtendedSession.jsx
│   │   │   ├── MCQSession.jsx
│   │   │   └── SessionSummary.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── curriculum/
│   └── gensheet_vce_curriculum.json   ← READ THIS FILE, do not modify
├── requirements.txt
└── render.yaml
```

---

## Curriculum JSON

The file `curriculum/gensheet_vce_curriculum.json` is the authoritative
source for all topic names, content descriptors, key formulas, hints,
and question generation guidance.

**Read this file at startup.** Load it into memory as a Python dict.
Use it in ALL AI prompts to ground question generation in actual VCAA content.

```python
import json, os

with open("curriculum/gensheet_vce_curriculum.json") as f:
    CURRICULUM = json.load(f)

def get_topic(topic_code: str) -> dict:
    for aos in CURRICULUM["areas_of_study"]:
        for topic in aos["topics"]:
            if topic["code"] == topic_code:
                return topic
    return {}
```

---

## Topic selector

These are the selectable topics in the UI, mapped to curriculum codes:

```python
EXTENDED_TOPICS = {
    "implicit_differentiation": "SM_AOS4_T1",
    "integration_techniques":   "SM_AOS4_T2",
    "differential_equations":   "SM_AOS4_T3",
    "kinematics":               "SM_AOS4_T4",
    "complex_numbers":          "SM_AOS3_T1",
    "complex_loci":             "SM_AOS3_T2",
    "vectors_3d":               "SM_AOS5_T1",
    "lines_and_planes":         "SM_AOS5_T2",
    "logic_and_proof":          "SM_AOS1_T2",
    "induction":                "SM_AOS1_T3",
    "rational_functions":       "SM_AOS2_T1",
    "statistics":               "SM_AOS6_T3",
    "hypothesis_testing":       "SM_AOS6_T4",
    "pdf_and_sampling":         "SM_AOS6_T5",
}

MCQ_TOPICS = {
    "logic_and_proof":          "SM_AOS1_T1",
    "complex_numbers":          "SM_AOS3_T1",
    "integration":              "SM_AOS4_T2",
    "differential_equations":   "SM_AOS4_T3",
    "kinematics":               "SM_AOS4_T4",
    "vectors":                  "SM_AOS5_T1",
    "lines_and_planes":         "SM_AOS5_T2",
    "statistics":               "SM_AOS6_T1",
}
```

---

## Extended Response engine

### `/api/extended/generate` POST

**Request:** `{ "topic_code": "SM_AOS4_T1", "difficulty": "standard" }`

**Response:**
```json
{
  "session_id": "abc123",
  "topic_name": "Implicit differentiation",
  "questions": [
    {
      "index": 0,
      "parts": [
        {
          "label": "a",
          "marks": 3,
          "question_latex": "Consider the curve xe^{-2y} + y^2e^x = 8e^4. Find \\frac{dy}{dx}.",
          "curriculum_tag": "SM_AOS4_T1 — Implicit differentiation using chain and product rules",
          "strategy_hint": "Differentiate both sides with respect to x. Apply the product rule to each term, remembering that d/dx[f(y)] = f'(y)·dy/dx by the chain rule.",
          "formula_reference": "Product rule: d/dx[uv] = u·v' + v·u'",
          "worked_solution_latex": "Differentiating implicitly: e^{-2y} - 2xe^{-2y}\\frac{dy}{dx} + 2ye^x\\frac{dy}{dx} + y^2e^x = 0..."
        },
        {
          "label": "b",
          "marks": 1,
          "question_latex": "Hence find the equation of the tangent at the point (4, -2).",
          "curriculum_tag": "SM_AOS4_T1 — Applying dy/dx to find tangent line equation",
          "strategy_hint": "Substitute x=4, y=−2 into your expression for dy/dx to find the gradient. Then use y − y₁ = m(x − x₁).",
          "formula_reference": "Tangent line: y − y₁ = m(x − x₁)",
          "worked_solution_latex": "Substituting (4,-2): gradient = \\frac{5}{12}. Tangent: y = \\frac{5}{12}x - \\frac{11}{3}"
        }
      ]
    }
  ]
}
```

### AI generation prompt for Extended Response

```python
EXTENDED_SYSTEM = """You are generating VCE Specialist Mathematics exam questions
for Year 12 students in Victoria, Australia.

You will receive a curriculum topic entry from the official VCAA study design.
Generate ONE multi-part question (2–3 parts labelled a, b, c) matching
the specified difficulty tier.

STRICT RULES:
- Never use 'show that' — use 'find', 'prove', 'determine', 'calculate'
- Never ask for a sketch — decompose into specific numeric/algebraic sub-questions
- Never ask for a direction arrow on a diagram
- Answers must be exact unless the question specifies decimal places
- Numbers must be workable by hand for standard difficulty
- LaTeX notation: use \\frac{}{}, \\sqrt{}, \\int, \\sum, e^{}, etc.
- Keep question text clear and self-contained

Respond in JSON only. No preamble, no markdown fences. Exact format:
{
  "parts": [
    {
      "label": "a",
      "marks": 3,
      "question_latex": "...",
      "curriculum_tag": "one sentence: what VCAA content descriptor this tests",
      "strategy_hint": "one sentence: the first step only, not the solution",
      "formula_reference": "the key formula from the curriculum, verbatim",
      "worked_solution_latex": "complete worked solution in LaTeX"
    }
  ]
}"""


async def generate_extended(topic_code: str, difficulty: str) -> dict:
    topic = get_topic(topic_code)
    if not topic:
        raise ValueError(f"Unknown topic code: {topic_code}")

    curriculum_context = f"""
TOPIC: {topic['name']}
VCAA CONTENT DESCRIPTORS:
{chr(10).join('- ' + c for c in topic['vcaa_content'])}

KEY FORMULAS:
{chr(10).join('- ' + f for f in topic['key_formulas'])}

DIFFICULTY TARGET ({difficulty}):
{topic['difficulty_tiers'][difficulty]}

EXAM QUESTION STYLE:
{topic['exam_question_style']}

QUESTION GENERATION NOTES:
{topic['question_generation_notes']}
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=EXTENDED_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Generate a {difficulty}-difficulty multi-part question for this topic:\n\n{curriculum_context}"
        }]
    )

    raw = message.content[0].text
    data = json.loads(raw)
    return data
```

### Session storage

```python
_extended_sessions: dict[str, dict] = {}
# Stores the full generated question including worked solutions.
# Frontend only receives question text + hints initially.
# Worked solution retrieved separately via /api/extended/solution.
```

### `/api/extended/solution` POST

```json
{ "session_id": "abc123", "question_index": 0, "part_label": "a" }
```

Returns the `worked_solution_latex` for that part.
This endpoint is called when the student clicks "Show worked solution".

---

## MCQ engine

### `/api/mcq/generate` POST

**Request:** `{ "topic_code": "SM_AOS5_T1" }`

**Response:**
```json
{
  "session_id": "xyz789",
  "topic_name": "Vectors",
  "questions": [
    {
      "index": 0,
      "question_latex": "For non-zero vectors \\mathbf{a} and \\mathbf{b}, if \\mathbf{a} \\cdot \\mathbf{b} = |\\mathbf{a} \\times \\mathbf{b}|, the angle between them is",
      "options": {
        "A": "0",
        "B": "\\frac{\\pi}{4}",
        "C": "\\frac{\\pi}{2}",
        "D": "\\frac{3\\pi}{4}"
      }
    }
  ]
}
```

Correct answers and explanations stored server-side only.

### `/api/mcq/submit` POST

```json
{ "session_id": "xyz789", "answers": ["B", "A", "D", "B", "C"] }
```

Returns score + per-question results including explanation.

### MCQ generation prompt

```python
MCQ_SYSTEM = """You are generating VCE Specialist Mathematics multiple choice
questions for Year 12 students in Victoria, Australia.

You will receive a curriculum topic. Generate exactly 5 MCQ questions
matching VCE Specialist Exam 2 Section A difficulty and style.

RULES:
- One correct answer per question, three plausible distractors
- Distractors should reflect common student errors (not random wrong answers)
- Questions require calculation or reasoning, not recall only
- Use LaTeX notation in question and option text
- Do not include 'all of the above' or 'none of the above'

Respond in JSON only. No preamble, no markdown fences:
{
  "questions": [
    {
      "question_latex": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct": "B",
      "explanation_latex": "brief explanation of why B is correct and why distractors are wrong"
    }
  ]
}

If the AI response is not valid JSON, retry once. On second failure return
a structured error: {"error": "generation_failed"}"""
```

---

## Frontend spec

### HomeScreen

Two cards side by side (stack on narrow viewport):

**Extended Response**
- Title: "Extended Response"
- Subtitle: "Multi-part questions — Exam 1 style"
- Topic dropdown: all EXTENDED_TOPICS listed by display name
- Difficulty toggle: Standard / Hard (default: Standard)
- Button: "Generate Questions →"

**MCQ**
- Title: "Multiple Choice"
- Subtitle: "5 questions — Exam 2 Section A style"
- Topic dropdown: all MCQ_TOPICS listed by display name
- Button: "Generate Questions →"

Small text below both cards:
"No login required. GenSheet VCE • Part of the GenSheet suite"

### ExtendedSession

Layout: full-width, one question at a time (if multiple questions generated).

Per part:
```
[Q1a — 3 marks]                [SM_AOS4_T1 · Implicit differentiation]

[Question text rendered with KaTeX]

📌 Strategy hint: Differentiate both sides with respect to x...
📐 Formula: Product rule: d/dx[uv] = u·v' + v·u'

[           Show worked solution           ]   ← button, greyed until clicked

─── Worked solution ───────────────────────   ← appears after button click
[Worked solution rendered with KaTeX]
───────────────────────────────────────────

How did you go?   [✗ Wrong]  [~ Partial]  [✓ Correct]   ← 3-way self-assessment
```

Navigation: "Next part →" after self-assessment selected.
After all parts: show SessionSummary.

### MCQSession

One question at a time. Large radio buttons A/B/C/D. No feedback until all 5 done.
Progress: "Question 2 of 5" at top.
After Q5: auto-submit → SessionSummary.

### SessionSummary

**Extended:**
```
Session complete — [topic name]

You rated yourself: 3 / 5 correct  (based on self-assessment)

Q1a  ✓  Implicit differentiation + tangent — standard
Q1b  ~  Tangent line equation — standard
Q2a  ✗  Integration by substitution — standard
...

[Try another session]    [Different topic]    [Back to home]
```

**MCQ:**
```
Session complete — [topic name]

Your score: 3 / 5

Q1  ✓  Your answer: B  Correct: B
       The angle between vectors where |a·b| = |a×b| is π/4 because...
Q2  ✗  Your answer: A  Correct: C
       ...
...

[Try another session]    [Different topic]    [Back to home]
```

---

## KaTeX rendering

In `index.html` add to `<head>`:
```html
<link rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script defer
  src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script defer
  src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$', right: '$', display: false}
    ], throwOnError: false
  })">
</script>
```

In React: after setting HTML content via dangerouslySetInnerHTML or after
updating state that shows LaTeX, call:
```javascript
if (window.renderMathInElement) {
  window.renderMathInElement(document.body, {
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$', right: '$', display: false}
    ], throwOnError: false
  });
}
```

Wrap in useEffect with a small timeout (50ms) after content renders.

---

## Loading state

Both session types require an AI call that takes 3–8 seconds.
Show a spinner with rotating messages:
- "Generating your question..."
- "Checking curriculum alignment..."
- "Preparing hints..."

Do not show a blank screen during generation.

---

## Error handling

If AI generation fails or returns invalid JSON:
- Show: "Could not generate questions. Please try again."
- Retry button
- Log the error to console

If session_id not found on solution retrieval:
- Show: "Session expired. Please start a new session."

---

## render.yaml

```yaml
services:
  - type: web
    name: gensheet-vce
    env: python
    buildCommand: |
      pip install -r requirements.txt
      cd frontend && npm install && npm run build
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false
```

## requirements.txt

```
fastapi
uvicorn
anthropic
python-multipart
```

---

## Done criteria

Claude Code: you are done when ALL of these pass:

- [ ] `uvicorn backend.main:app` starts without errors
- [ ] `POST /api/extended/generate` returns a valid session with questions,
      curriculum tags, hints, and worked solutions (stored server-side)
- [ ] `POST /api/extended/solution` returns the worked solution for a given part
- [ ] `POST /api/mcq/generate` returns 5 questions without correct answers exposed
- [ ] `POST /api/mcq/submit` returns score + explanations
- [ ] `npm run build` completes without errors
- [ ] Home screen renders with both session type cards and topic dropdowns
- [ ] Extended session renders question text with KaTeX (not raw LaTeX strings)
- [ ] Strategy hint and formula reference display below each question
- [ ] "Show worked solution" button reveals solution and then hides button
- [ ] Self-assessment 3-way radio works and advances to next part
- [ ] MCQ session shows one question at a time, A/B/C/D options selectable
- [ ] Session summary shows per-question results with curriculum tag
- [ ] Curriculum JSON file is loaded and used in generation prompts
      (verify by checking that a generated question matches the topic)

---

## Notes for Claude Code

**On the curriculum JSON:** it is the single source of truth for everything
topic-related. The system prompt for question generation must include the
relevant topic entry from this file — vcaa_content, key_formulas,
difficulty_tiers, question_generation_notes. A question generated without
this context will be off-curriculum.

**On difficulty:** Standard difficulty uses Sonnet; this is intentional —
the question quality matters more than the cost. Haiku is fine for MCQ.

**On worked solutions:** these are generated by the AI in the same call as
the question. They are stored server-side and only sent when the student
requests them. This is important: the student should attempt the question
before seeing the solution, and the UI must enforce this ordering.

**On LaTeX:** the worked solution will contain LaTeX. The frontend must
trigger KaTeX rendering after it appears in the DOM. A useEffect with
a 50ms timeout calling renderMathInElement is the reliable pattern.

**On session storage:** in-memory dict is fine. Sessions expire naturally
when the server restarts. This is a zero-auth product.

**On style:** white background, clear typography, generous whitespace.
The brand colour for GenSheet VCE can be a muted teal or blue — different
from GenSheet Drill's neutral palette but part of the same family.
Keep it understated. This is a study tool.
