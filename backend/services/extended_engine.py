import json
import os
import uuid
import anthropic

with open("curriculum/gensheet_vce_curriculum.json") as f:
    CURRICULUM = json.load(f)

def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

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

    message = _client().messages.create(
        model=os.environ.get("EXTENDED_MODEL", "claude-sonnet-4-6"),
        max_tokens=2000,
        system=EXTENDED_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Generate a {difficulty}-difficulty multi-part question for this topic:\n\n{curriculum_context}"
        }]
    )

    raw = message.content[0].text.strip()
    data = json.loads(raw)

    session_id = str(uuid.uuid4())[:8]

    # Store full data server-side (including worked solutions)
    _extended_sessions[session_id] = {
        "topic_name": topic["name"],
        "topic_code": topic_code,
        "difficulty": difficulty,
        "questions": [{"index": 0, "parts": data["parts"]}]
    }

    # Return questions WITHOUT worked_solution_latex
    safe_parts = []
    for part in data["parts"]:
        safe_parts.append({
            "label": part["label"],
            "marks": part["marks"],
            "question_latex": part["question_latex"],
            "curriculum_tag": part["curriculum_tag"],
            "strategy_hint": part["strategy_hint"],
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
