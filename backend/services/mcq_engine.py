import json
import logging
import os
import pathlib
import uuid
import re
import anthropic

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
    logger.info("Anthropic client initialised (MCQ)")
except KeyError:
    logger.critical("ANTHROPIC_API_KEY not set — backend cannot start")
    raise

_mcq_sessions: dict[str, dict] = {}

MCQ_SYSTEM = """You are generating VCE Specialist Mathematics multiple choice
questions for Year 12 students in Victoria, Australia.

You will receive a curriculum topic. Generate exactly 5 MCQ questions
matching VCE Specialist Exam 2 Section A difficulty and style.

RULES:
- Each question must have exactly one clearly correct answer among A, B, C, D
- Only generate questions where a definitive correct answer exists — no trick questions or questions with debatable or non-existent answers
- Distractors should reflect common student errors (not random wrong answers)
- Questions require calculation or reasoning, not recall only
- LaTeX notation: ALWAYS wrap math in delimiters. Use $...$ for inline math and $$...$$ for block/display math.
- Example: "The value of $\\int_0^1 e^x dx$ is"
- Use ONLY $...$ and $$...$$ delimiters. NEVER use \\[...\\] or \\(...\\) delimiters.
- Do NOT use markdown formatting in text fields: no **bold**, no bullet lists, no headings.
- Do not include 'all of the above' or 'none of the above'
- Generate EXACTLY 5 questions — no more, no fewer.

Respond in JSON only. Exact format:
{
  "questions": [
    {
      "question_latex": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct": "B",
      "explanation_latex": "brief explanation with $...$ delimiters"
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
            cleaned = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

    # Final fallback: direct load
    return json.loads(text)

VALID_OPTIONS = {"A", "B", "C", "D"}

def _validate_mcq_data(data: dict) -> str | None:
    """Return an error string if data is invalid, else None."""
    questions = data.get("questions")
    if not isinstance(questions, list) or len(questions) == 0:
        return "'questions' missing or empty"
    for i, q in enumerate(questions):
        for field in ("question_latex", "explanation_latex"):
            if not isinstance(q.get(field), str) or not q[field].strip():
                return f"question[{i}].{field} empty/missing"
        opts = q.get("options")
        if not isinstance(opts, dict) or set(opts.keys()) != VALID_OPTIONS:
            return f"question[{i}].options keys must be A/B/C/D"
        for k, v in opts.items():
            if not isinstance(v, str) or not v.strip():
                return f"question[{i}].options[{k}] empty"
        if q.get("correct") not in VALID_OPTIONS:
            return f"question[{i}].correct '{q.get('correct')}' not in A/B/C/D"
    return None

_DISPLAY_RE = re.compile(r'\\\[(.*?)\\\]', re.DOTALL)
_INLINE_RE  = re.compile(r'\\\((.*?)\\\)')

def _norm(text: str) -> str:
    """Normalize \\[...\\] → $$...$$ and \\(...\\) → $...$."""
    text = _DISPLAY_RE.sub(r'$$\1$$', text)
    text = _INLINE_RE.sub(r'$\1$', text)
    return text

def _sanitize_mcq(questions: list[dict]) -> list[dict]:
    """Apply delimiter normalization to all text fields in each MCQ question."""
    out = []
    for q in questions:
        sq = dict(q)
        for f in ("question_latex", "explanation_latex"):
            if isinstance(sq.get(f), str):
                sq[f] = _norm(sq[f])
        if isinstance(sq.get("options"), dict):
            sq["options"] = {k: _norm(v) if isinstance(v, str) else v
                             for k, v in sq["options"].items()}
        out.append(sq)
    return out


def get_topic(topic_code: str) -> dict:
    for aos in CURRICULUM["areas_of_study"]:
        for topic in aos["topics"]:
            if topic["code"] == topic_code:
                return topic
    return {}

async def generate_mcq(topic_code: str) -> dict:
    topic = get_topic(topic_code)
    if not topic:
        raise ValueError(f"Unknown topic code: {topic_code}")

    curriculum_context = f"""TOPIC: {topic['name']}
VCAA CONTENT DESCRIPTORS:
{chr(10).join('- ' + c for c in topic['vcaa_content'])}

KEY FORMULAS:
{chr(10).join('- ' + f for f in topic['key_formulas'])}

EXAM QUESTION STYLE:
{topic['exam_question_style']}

QUESTION GENERATION NOTES:
{topic['question_generation_notes']}"""

    # Model names: spec had placeholders, using current standard ones
    model = os.environ.get("MCQ_MODEL", "claude-3-5-haiku-20241022")

    raw = None
    data = None
    for attempt in range(3):
        try:
            logger.info("MCQ generate attempt %d/%d — topic=%s model=%s", attempt + 1, 3, topic_code, model)
            message = await client.messages.create(
                model=model,
                max_tokens=4000,
                system=MCQ_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": f"Generate 5 MCQ questions for this topic:\n\n{curriculum_context}"
                }]
            )
            raw = message.content[0].text
            data = parse_json(raw)
            err = _validate_mcq_data(data)
            if err:
                logger.warning("MCQ attempt %d invalid: %s", attempt + 1, err)
                if raw:
                    logger.debug("Raw response (first 500): %s", raw[:500])
                data = None
                continue
            break
        except Exception as e:
            logger.error("MCQ generation attempt %d failed: %s", attempt + 1, e, exc_info=True)
            if raw:
                logger.debug("Raw response (first 500): %s", raw[:500])

    if data is None:
        logger.error("MCQ generation failed after 3 attempts — topic=%s", topic_code)
        return {"error": "generation_failed"}

    session_id = str(uuid.uuid4())[:8]
    sanitized = _sanitize_mcq(data["questions"])

    _mcq_sessions[session_id] = {
        "topic_name": topic["name"],
        "topic_code": topic_code,
        "questions": [
            {
                "index": i,
                "question_latex": q["question_latex"],
                "options": q["options"],
                "correct": q["correct"],
                "explanation_latex": q.get("explanation_latex", ""),
            }
            for i, q in enumerate(sanitized)
        ]
    }

    safe_questions = [
        {
            "index": i,
            "question_latex": q["question_latex"],
            "options": q["options"],
        }
        for i, q in enumerate(sanitized)
    ]

    return {
        "session_id": session_id,
        "topic_name": topic["name"],
        "questions": safe_questions
    }


def submit_mcq(session_id: str, answers: list[str]) -> dict:
    session = _mcq_sessions.get(session_id)
    if not session:
        raise KeyError("session_not_found")

    questions = session["questions"]
    results = [
        {
            "index": i,
            "student_answer": answers[i] if i < len(answers) else "",
            "correct_answer": q["correct"],
            "explanation_latex": q["explanation_latex"],
        }
        for i, q in enumerate(questions)
    ]

    return {
        "session_id": session_id,
        "topic_name": session["topic_name"],
        "results": results,
    }
