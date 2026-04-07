import json
import os
import uuid
import anthropic

# Reuse the already-loaded curriculum from extended_engine if available,
# otherwise load it here.
with open("curriculum/gensheet_vce_curriculum.json") as f:
    CURRICULUM = json.load(f)

def _client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

_mcq_sessions: dict[str, dict] = {}

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
}"""


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

    raw = None
    for attempt in range(2):
        try:
            message = _client().messages.create(
                model=os.environ.get("MCQ_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=3000,
                system=MCQ_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": f"Generate 5 MCQ questions for this topic:\n\n{curriculum_context}"
                }]
            )
            raw = message.content[0].text.strip()
            data = json.loads(raw)
            break
        except (json.JSONDecodeError, Exception):
            if attempt == 1:
                return {"error": "generation_failed"}

    session_id = str(uuid.uuid4())[:8]

    # Store full data server-side (correct answers + explanations)
    _mcq_sessions[session_id] = {
        "topic_name": topic["name"],
        "topic_code": topic_code,
        "questions": [
            {
                "index": i,
                "question_latex": q["question_latex"],
                "options": q["options"],
                "correct": q["correct"],
                "explanation_latex": q["explanation_latex"],
            }
            for i, q in enumerate(data["questions"])
        ]
    }

    # Return questions WITHOUT correct answers or explanations
    safe_questions = [
        {
            "index": i,
            "question_latex": q["question_latex"],
            "options": q["options"],
        }
        for i, q in enumerate(data["questions"])
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
    results = []
    score = 0

    for i, q in enumerate(questions):
        student_answer = answers[i] if i < len(answers) else ""
        correct = q["correct"]
        is_correct = student_answer == correct
        if is_correct:
            score += 1
        results.append({
            "index": i,
            "correct": is_correct,
            "student_answer": student_answer,
            "correct_answer": correct,
            "explanation_latex": q["explanation_latex"],
        })

    return {
        "session_id": session_id,
        "topic_name": session["topic_name"],
        "score": score,
        "total": len(questions),
        "results": results,
    }
