"""
Two-Stage Feedback Evaluation System.

Stage 0: Clean & translate (Hinglish → English, filter abuse).
Stage 1: Validates if feedback is meaningful and actionable.
Stage 2: Extracts structured feedback split across agent categories.

Uses OpenRouter LLM for all evaluation.
"""

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


class FeedbackValidator:
    """
    Three-stage LLM-powered feedback processor (OpenRouter).

    Stage 0 — Clean: Translate Hinglish → English, remove abusive language.
    Stage 1 — Validation: Is the feedback actionable?
    Stage 2 — Extraction: Split into agent-specific categories.
    """

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.1,  # Low temp for precise evaluation
            )
        else:
            self.llm = None
            print("   ⚠️ FeedbackValidator: No OPENROUTER_API_KEY found.")

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Helper to call the OpenRouter LLM and return raw text."""
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        content = response.content.strip()
        # Strip markdown code fences if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content

    def clean_and_translate(self, feedback_text: str) -> dict:
        """
        Stage 0: Clean the feedback.
        - Translate Hinglish/Hindi to English.
        - Remove all abusive, vulgar, and offensive language.
        - Preserve the core actionable meaning.

        Returns:
            {
                "cleaned_text": "clean English version",
                "original_language": "hinglish" | "hindi" | "english",
                "had_abuse": true/false
            }
        """
        if not self.llm:
            return {"cleaned_text": feedback_text, "original_language": "unknown", "had_abuse": False}

        prompt = f"""You are a feedback pre-processor for an AI ad generation system.

Your job:
1. If the text is in Hindi or Hinglish (mix of Hindi + English), translate it fully to English.
2. REMOVE any abusive, vulgar, offensive, or inappropriate words completely. Do NOT include them in the output.
3. Keep ONLY the constructive, actionable part of the feedback.
4. If the entire feedback is just abuse with no actionable content, set cleaned_text to empty string "".

User Feedback:
"{feedback_text}"

Return ONLY valid JSON:
{{
  "cleaned_text": "clean English feedback with abuse removed",
  "original_language": "hinglish" or "hindi" or "english",
  "had_abuse": true or false
}}"""

        try:
            content = self._call_llm("You are a language translator and content moderator. Return ONLY valid JSON.", prompt)
            result = json.loads(content)
            if result.get("had_abuse"):
                print(f"   🚫 Abuse detected and filtered from feedback")
            if result.get("original_language") != "english":
                print(f"   🌐 Translated from {result.get('original_language')} to English")
            return result
        except Exception as e:
            print(f"   ⚠️ Clean/translate failed: {e}. Using original text.")
            return {"cleaned_text": feedback_text, "original_language": "unknown", "had_abuse": False}

    def validate(self, feedback_text: str) -> dict:
        """
        Stage 1: Check if feedback is valid and actionable.

        Returns:
            {
                "valid": True/False,
                "reason": "explanation",
                "confidence": 0.0 - 1.0
            }
        """
        if not self.llm:
            return {"valid": False, "reason": "No LLM client available", "confidence": 0.0}

        prompt = f"""You are evaluating user feedback for an AI ad generation system.

Determine if the feedback is meaningful and actionable.

### What is Actionable?
Feedback is **actionable** if it provides specific direction for one of our agents (Research, Strategy, Creative, Production).
- **Research**: "Target only luxury car buyers in Berlin."
- **Strategy**: "Make the brand voice more ironic and witty." 
- **Creative**: "Make the opening hook about saving time."
- **Production**: "Use my provided avatar," "make the background blue," "music should be upbeat."

### What is NOT Actionable?
Feedback that is vague, purely emotional, or non-descriptive.
- "I don't like this."
- "Make it better."
- "Not good."

User Feedback:
"{feedback_text}"

Return ONLY valid JSON:
{{
  "valid": true or false,
  "reason": "brief explanation (e.g., 'Specifies avatar choice')",
  "confidence": 0.0 to 1.0
}}"""

        try:
            content = self._call_llm("You are a feedback quality evaluator. Return ONLY valid JSON.", prompt)
            result = json.loads(content)
            print(f"   🔍 Validation: valid={result.get('valid')}, confidence={result.get('confidence')}")
            return result
        except Exception as e:
            print(f"   ❌ Feedback validation failed: {e}")
            return {"valid": False, "reason": f"LLM error: {e}", "confidence": 0.0}

    def extract_structured(self, feedback_text: str) -> dict:
        """
        Stage 2: Convert validated feedback into structured agent-specific feedback.

        Returns:
            {
                "research_feedback": str or null,
                "strategy_feedback": str or null,
                "creative_feedback": str or null,
                "production_feedback": str or null
            }
        """
        if not self.llm:
            return {
                "research_feedback": None,
                "strategy_feedback": None,
                "creative_feedback": None,
                "production_feedback": None,
            }

        prompt = f"""You are an advanced analyst for an AI advertising agency. 
Your goal is to take raw user feedback and precisely divide it among our specialist agents.

### IMPORTANT: Overlapping Feedback
A single piece of feedback can belong to TWO OR MORE agents simultaneously. If a request affects multiple domains, you MUST assign the relevant instructions to EACH applicable agent.
Example: "Make the ad feel more luxury and premium"
- Strategy: Refine brand positioning to luxury.
- Creative: Use sophisticated and elegant language in the script.
- Production: Use high-end color palettes, cinematic lighting, and slow-paced editing.

### Step 1: Self-Explanation (Chain-of-Thought)
Carefully analyze the user feedback. In your own words, explain:
- What is the user's core intent?
- Which agents are affected by this request (remember: often more than one)?
- Why does this feedback overlap between these specific agents?

### Step 2: Agent Assignment
Assign specific, actionable instructions to ALL relevant agents.

**Agent Responsibilities:**
- **Research Agent**: Target audience (demographics, location), competitor comparisons, market trends.
- **Strategy Agent**: High-level approach, psychological triggers, brand positioning, emotional tone, "the big idea".
- **Creative Agent**: The script, dialogue, storytelling structure, hooks, CTA, and voiceover text.
- **Production Agent**: Visual style, avatar, background music, editing pace, colors, thumbnail, and transitions.

User Feedback:
"{feedback_text}"

Return ONLY valid JSON:
{{
  "self_explanation": "detailed analysis of intent and overlapping agent responsibilities",
  "logic_breakdown": {{
      "research": "logic for assignment or null",
      "strategy": "logic for assignment or null",
      "creative": "logic for assignment or null",
      "production": "logic for assignment or null"
  }},
  "research_feedback": "specifically extracted research instructions or null",
  "strategy_feedback": "specifically extracted strategy instructions or null",
  "creative_feedback": "specifically extracted creative instructions or null",
  "production_feedback": "specifically extracted production instructions or null"
}}

Set a field to null ONLY if the feedback has absolutely no relevance to that agent."""

        try:
            content = self._call_llm("You are a feedback categorizer. Return ONLY valid JSON.", prompt)
            result = json.loads(content)
            print(f"   📋 Extraction: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            print(f"   ❌ Feedback extraction failed: {e}")
            return {
                "research_feedback": None,
                "strategy_feedback": None,
                "creative_feedback": None,
                "production_feedback": None,
            }

    def evaluate(self, feedback_text: str) -> dict:
        """
        Full three-stage pipeline:
        0. Clean and translate (Hinglish → English, filter abuse)
        1. Validate feedback
        2. If valid, extract structured feedback

        Returns:
            {
                "valid": bool,
                "confidence": float,
                "reason": str,
                "cleaned_text": str,
                "had_abuse": bool,
                "structured_feedback": dict or None
            }
        """
        # Stage 0: Clean and translate
        clean_result = self.clean_and_translate(feedback_text)
        cleaned_text = clean_result.get("cleaned_text", "").strip()

        # If nothing left after cleaning (all abuse, no content)
        if not cleaned_text:
            print(f"   ⛔ Feedback was entirely abusive. Rejected.")
            return {
                "valid": False,
                "confidence": 0.0,
                "reason": "Feedback contained only abusive language with no actionable content",
                "cleaned_text": "",
                "had_abuse": True,
                "structured_feedback": None,
            }

        # Stage 1: Validation (on cleaned text)
        validation = self.validate(cleaned_text)

        if not validation.get("valid", False):
            print(f"   ⛔ Feedback rejected: {validation.get('reason')}")
            return {
                "valid": False,
                "confidence": validation.get("confidence", 0.0),
                "reason": validation.get("reason", "Invalid feedback"),
                "cleaned_text": cleaned_text,
                "had_abuse": clean_result.get("had_abuse", False),
                "structured_feedback": None,
            }

        # Stage 2: Structured extraction (on cleaned text)
        structured = self.extract_structured(cleaned_text)

        return {
            "valid": True,
            "confidence": validation.get("confidence", 0.0),
            "reason": validation.get("reason", ""),
            "cleaned_text": cleaned_text,
            "had_abuse": clean_result.get("had_abuse", False),
            "structured_feedback": structured,
        }
