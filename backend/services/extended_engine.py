import json
import logging
import os
import pathlib
import uuid
import re
import anthropic
from backend.services.session_limiter import check_and_increment, SessionLimitExceeded

logger = logging.getLogger(__name__)

# Load curriculum once at module level — path is relative to this file, not cwd
_CURRICULUM_PATH = pathlib.Path(__file__).parent.parent.parent / "curriculum" / "gensheet_vce_curriculum.json"
try:
    with open(_CURRICULUM_PATH) as f:
        CURRICULUM = json.load(f)
    logger.info("Loaded curriculum from %s", _CURRICULUM_PATH)
except Exception as e:
    logger.critical("Failed to load curriculum from %s: %s", _CURRICULUM_PATH, e)
    raise

# Use AsyncAnthropic for non-blocking calls
try:
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    logger.info("Anthropic client initialised (extended)")
except KeyError:
    logger.critical("ANTHROPIC_API_KEY not set — backend cannot start")
    raise

_extended_sessions: dict[str, dict] = {}

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
- LaTeX notation: ALWAYS wrap math in delimiters. Use $...$ for inline math and $$...$$ for block/display math.
- Example: "Consider the function $f(x) = \\sin(x)$. Find the value of $f(\\pi)$."
- Use ONLY $...$ and $$...$$ delimiters. NEVER use \\[...\\] or \\(...\\) delimiters.
- Do NOT use markdown formatting in text fields: no **bold**, no bullet lists, no headings.
- Keep question text clear and self-contained
- formula_reference must contain ONLY a LaTeX expression wrapped in $$...$$. No surrounding text, no prose.
- Generate EXACTLY 2–3 parts labelled a, b, c in order.

Respond in VALID JSON only. Ensure all backslashes in LaTeX are escaped (e.g., \\\\frac instead of \\frac).
Exact format:
{
  "parts": [
    {
      "label": "a",
      "marks": 3,
      "question_latex": "...",
      "curriculum_tag": "...",
      "formula_reference": "$$...$$",
      "worked_solution_latex": "..."
    }
  ]
}"""

def parse_json(text: str) -> dict:
    """Extract JSON from text, handling markdown fences and surrounding text."""
    text = text.strip()
    
    # Try finding content inside markdown fences
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # If failing, fall through to broader search
            pass
            
    # Try finding the largest JSON-like structure (between { and })
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # If failing, try to fix common issues like trailing commas
            # (simple fix for common LLM error)
            cleaned = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

    # Final fallback: direct load
    return json.loads(text)

VALID_LABELS = {"a", "b", "c"}

def _validate_extended_data(data: dict) -> str | None:
    """Return an error string if data is invalid, else None."""
    parts = data.get("parts")
    if not isinstance(parts, list) or not (2 <= len(parts) <= 3):
        return f"'parts' must be 2–3 items, got {parts!r}"
    for i, p in enumerate(parts):
        if p.get("label") not in VALID_LABELS:
            return f"part[{i}].label '{p.get('label')}' not in a/b/c"
        if not isinstance(p.get("marks"), int) or p["marks"] < 1:
            return f"part[{i}].marks invalid: {p.get('marks')!r}"
        for field in ("question_latex", "curriculum_tag", "worked_solution_latex"):
            if not isinstance(p.get(field), str) or not p[field].strip():
                return f"part[{i}].{field} empty/missing"
        fr = p.get("formula_reference")
        if not isinstance(fr, str) or not fr.strip().startswith("$$"):
            return f"part[{i}].formula_reference must start with $$"
    return None

_DISPLAY_RE = re.compile(r'\\\[(.*?)\\\]', re.DOTALL)
_INLINE_RE  = re.compile(r'\\\((.*?)\\\)')

def _norm(text: str) -> str:
    """Normalize \\[...\\] → $$...$$ and \\(...\\) → $...$."""
    text = _DISPLAY_RE.sub(r'$$\1$$', text)
    text = _INLINE_RE.sub(r'$\1$', text)
    return text

def _sanitize_parts(parts: list[dict]) -> list[dict]:
    """Apply delimiter normalization to all text fields in each part."""
    fields = ("question_latex", "curriculum_tag", "formula_reference", "worked_solution_latex")
    out = []
    for p in parts:
        sp = dict(p)
        for f in fields:
            if isinstance(sp.get(f), str):
                sp[f] = _norm(sp[f])
        out.append(sp)
    return out


def get_topic(topic_code: str) -> dict:
    for aos in CURRICULUM["areas_of_study"]:
        for topic in aos["topics"]:
            if topic["code"] == topic_code:
                return topic
    return {}


async def generate_extended(topic_code: str, difficulty: str) -> dict:
    topic = get_topic(topic_code)
    if not topic:
        raise ValueError(f"Unknown topic code: {topic_code}")

    curriculum_context = f"""TOPIC: {topic['name']}
VCAA CONTENT DESCRIPTORS:
{chr(10).join('- ' + c for c in topic['vcaa_content'])}

KEY FORMULAS:
{chr(10).join('- ' + f for f in topic['key_formulas'])}

DIFFICULTY TARGET ({difficulty}):
{topic['difficulty_tiers'][difficulty]}

EXAM QUESTION STYLE:
{topic['exam_question_style']}

QUESTION GENERATION NOTES:
{topic['question_generation_notes']}"""

    # Model names: spec had placeholders, using current standard ones
    model = os.environ.get("EXTENDED_MODEL", "claude-3-5-sonnet-20241022")

    raw = None
    data = None
    for attempt in range(3):
        try:
            logger.info("Extended generate attempt %d/%d — topic=%s difficulty=%s model=%s", attempt + 1, 3, topic_code, difficulty, model)
            message = await client.messages.create(
                model=model,
                max_tokens=4000,
                system=EXTENDED_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": f"Generate a {difficulty}-difficulty multi-part question for this topic:\n\n{curriculum_context}"
                }]
            )
            raw = message.content[0].text
            data = parse_json(raw)
            err = _validate_extended_data(data)
            if err:
                logger.warning("Extended attempt %d invalid: %s", attempt + 1, err)
                if raw:
                    logger.debug("Raw response (first 500): %s", raw[:500])
                data = None
                continue
            break
        except Exception as e:
            logger.error("Extended generation attempt %d failed: %s", attempt + 1, e, exc_info=True)
            if raw:
                logger.debug("Raw response (first 500): %s", raw[:500])

    if data is None:
        logger.error("Extended generation failed after 3 attempts — topic=%s difficulty=%s", topic_code, difficulty)
        raise ValueError("generation_failed")

    check_and_increment()

    session_id = str(uuid.uuid4())[:8]
    sanitized = _sanitize_parts(data["parts"])

    # Store full data server-side (including worked solutions)
    _extended_sessions[session_id] = {
        "topic_name": topic["name"],
        "topic_code": topic_code,
        "difficulty": difficulty,
        "questions": [{"index": 0, "parts": sanitized}]
    }

    # Return questions WITHOUT worked_solution_latex
    safe_parts = []
    for part in sanitized:
        safe_parts.append({
            "label": part["label"],
            "marks": part["marks"],
            "question_latex": part["question_latex"],
            "curriculum_tag": part["curriculum_tag"],
            "formula_reference": part["formula_reference"],
        })

    return {
        "session_id": session_id,
        "topic_name": topic["name"],
        "questions": [{"index": 0, "parts": safe_parts}]
    }


def get_solution(session_id: str, question_index: int, part_label: str) -> str:
    session = _extended_sessions.get(session_id)
    if not session:
        raise KeyError("session_not_found")

    for q in session["questions"]:
        if q["index"] == question_index:
            for part in q["parts"]:
                if part["label"] == part_label:
                    return part["worked_solution_latex"]
    raise KeyError("part_not_found")
