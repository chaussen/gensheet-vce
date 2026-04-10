import pytest
import json
import os
from unittest.mock import AsyncMock, patch
from backend.services.mcq_engine import generate_mcq, _mcq_sessions
from backend.services.extended_engine import generate_extended, _extended_sessions

@pytest.mark.asyncio
async def test_mcq_generation_parsing():
    # Mock response from AI containing markdown fences and mixed LaTeX
    mock_raw_response = """
```json
{
  "questions": [
    {
      "question_latex": "What is $\\\\int x dx$?",
      "options": {
        "A": "$\\\\frac{x^2}{2}$",
        "B": "$x$",
        "C": "$x^2$",
        "D": "$1$"
      },
      "correct": "A",
      "explanation_latex": "The power rule gives $\\\\int x^n dx = \\\\frac{x^{n+1}}{n+1}$."
    }
  ]
}
```
"""
    
    # Setup mock client
    with patch("backend.services.mcq_engine.client") as mock_client:
        mock_msg = AsyncMock()
        mock_msg.content = [AsyncMock(text=mock_raw_response)]
        # Correct way to mock an awaited method
        mock_client.messages.create = AsyncMock(return_value=mock_msg)
        
        # We need a valid topic code from the curriculum
        # From earlier exploration: SM_AOS1_T1
        topic_code = "SM_AOS1_T1"
        
        result = await generate_mcq(topic_code)
        
        assert "session_id" in result
        assert result["topic_name"] == "Propositional logic"
        assert len(result["questions"]) == 1
        
        # Verify LaTeX is preserved (it should be as we removed the wrapping in components)
        q0 = result["questions"][0]
        assert "$\\int x dx$" in q0["question_latex"]
        assert "$\\frac{x^2}{2}$" in q0["options"]["A"]
        
        # Verify correct answer is NOT in the public result
        assert "correct" not in q0
        
        # Verify it IS in the session storage
        sid = result["session_id"]
        assert sid in _mcq_sessions
        assert _mcq_sessions[sid]["questions"][0]["correct"] == "A"

@pytest.mark.asyncio
async def test_extended_generation_parsing():
    # Mock response for extended response
    mock_raw_response = """
{
  "parts": [
    {
      "label": "a",
      "marks": 3,
      "question_latex": "Consider $f(x) = x^2$. Find $f'(2)$.",
      "curriculum_tag": "Derivatives",
      "strategy_hint": "Use power rule.",
      "formula_reference": "$$\\\\frac{d}{dx}x^n = nx^{n-1}$$",
      "worked_solution_latex": "Solution: $f'(x) = 2x$, so $f'(2) = 4$."
    },
    {
      "label": "b",
      "marks": 2,
      "question_latex": "Find $f''(x)$.",
      "curriculum_tag": "Derivatives",
      "strategy_hint": "Differentiate again.",
      "formula_reference": "$$\\\\frac{d}{dx}ax = a$$",
      "worked_solution_latex": "Solution: $f''(x) = 2$."
    }
  ]
}
"""
    
    with patch("backend.services.extended_engine.client") as mock_client:
        mock_msg = AsyncMock()
        mock_msg.content = [AsyncMock(text=mock_raw_response)]
        mock_client.messages.create = AsyncMock(return_value=mock_msg)
        
        topic_code = "SM_AOS4_T1"
        result = await generate_extended(topic_code, "standard")
        
        assert "session_id" in result
        assert len(result["questions"][0]["parts"]) == 2
        
        part = result["questions"][0]["parts"][0]
        assert "$f(x) = x^2$" in part["question_latex"]
        
        # Verify worked_solution_latex is HIDDEN from initial response
        assert "worked_solution_latex" not in part
        
        # Verify it is in session storage
        sid = result["session_id"]
        assert _extended_sessions[sid]["questions"][0]["parts"][0]["worked_solution_latex"] == "Solution: $f'(x) = 2x$, so $f'(2) = 4$."
