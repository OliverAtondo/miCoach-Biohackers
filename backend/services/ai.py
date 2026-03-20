import httpx
import os
import json
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

_MODEL = os.getenv("AI_Model", "llama3:latest")
_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")

_TIMEOUT = 380.0

def _chat_completion(messages: List[Dict], json_mode: bool = False) -> str:
    """Call the configured OpenAI-compatible AI endpoint (Gemini or Kimi)."""
    headers = {
        "Content-Type": "application/json",
    }
    payload = {"model": _MODEL, "messages": messages}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.post(f"{_BASE_URL}/chat/completions", headers=headers, json=payload)
        if not resp.is_success:
            raise ValueError(f"AI API error {resp.status_code}: {resp.text}")
        return resp.json()["choices"][0]["message"]["content"]

def _format_repo_for_prompt(g: Dict) -> str:
    """Build a detailed repo section for the Gemini prompt."""
    lines = [
        f"### Repo: {g['name']}",
        f"- Description: {g.get('description', 'N/A')}",
        f"- Primary language: {g.get('language', 'Unknown')}",
    ]

    # Languages breakdown
    langs = g.get("languages", {})
    if langs:
        total = sum(langs.values()) or 1
        lang_pct = ", ".join(f"{l} {round(b/total*100)}%" for l, b in sorted(langs.items(), key=lambda x: -x[1]))
        lines.append(f"- Languages: {lang_pct}")

    # File tree (structure overview)
    tree = g.get("file_tree", [])
    if tree:
        lines.append(f"- File structure ({len(tree)} files total):")
        for p in tree[:20]:
            lines.append(f"  {p}")
        if len(tree) > 20:
            lines.append(f"  ... and {len(tree) - 20} more files")

    # README
    readme = g.get("readme", "").strip()
    if readme and readme not in ("No README.", "Could not fetch README."):
        lines.append(f"\n**README (excerpt):**\n{readme[:800]}")

    # Actual source code
    samples = g.get("code_samples", [])
    if samples:
        lines.append("\n**Source code samples:**")
        for s in samples:
            truncated = " (truncated)" if s.get("truncated") else ""
            lines.append(f"\n```{s['path']}{truncated}\n{s['content']}\n```")

    return "\n".join(lines)


def analyze_user_profile(name: str, career_path: str, cv_text: str, github_summaries: List[Dict]) -> str:
    """Generate a skill level analysis based on CV and GitHub projects."""
    if github_summaries:
        github_info = "\n\n".join(_format_repo_for_prompt(g) for g in github_summaries)
    else:
        github_info = "No GitHub projects provided."

    messages = [
        {
            "role": "system",
            "content": "You are an expert senior software engineer and tech mentor. Analyze code quality, patterns, and skill level with precision.",
        },
        {
            "role": "user",
            "content": f"""Analyze the following developer profile in detail and assess their current skill level.

## Name: {name}
## Career Goal: {career_path}

---

## CV / Resume:
{cv_text[:3000]}

---

## GitHub Projects (with actual source code):
{github_info}

---

Based on the CV and the **actual code** in their repositories, provide:

1. **Overall Level** (Beginner / Intermediate / Advanced) — justify with specific code evidence
2. **Technical Strengths** — specific patterns, practices or technologies demonstrated well in the code
3. **Code Quality Observations** — structure, naming, patterns, tests, documentation
4. **Skill Gaps** — what's missing or weak relative to their career goal of {career_path}
5. **Personalized Summary** — 3-4 sentences specific to this person
""",
        },
    ]
    return _chat_completion(messages)


def generate_roadmap(name: str, career_path: str, analysis: str) -> str:
    """Generate a personalized learning roadmap."""
    messages = [
        {
            "role": "system",
            "content": "You are an expert tech mentor. Create structured, actionable learning roadmaps in markdown.",
        },
        {
            "role": "user",
            "content": f"""Based on the following profile analysis, create a detailed learning roadmap.

**Name:** {name}
**Career Goal:** {career_path}

**Profile Analysis:**
{analysis}

Create a structured roadmap with:
1. **Phase 1 - Foundation** (weeks 1-4): Core skills to build first
2. **Phase 2 - Core Skills** (weeks 5-12): Main technologies and concepts
3. **Phase 3 - Advanced Topics** (weeks 13-20): Specialization
4. **Phase 4 - Portfolio & Job Ready** (weeks 21-24): Projects and interview prep

For each phase include:
- Specific topics/technologies to learn
- Recommended resources (courses, docs, books)
- Mini-project ideas to practice

Format with markdown for easy reading.
""",
        },
    ]
    return _chat_completion(messages)


def chat_with_mentor(
    name: str,
    career_path: str,
    analysis: str,
    roadmap: str,
    history: List[Dict[str, str]],
    user_message: str,
) -> str:
    """Continue a mentorship chat session."""
    messages = [
        {
            "role": "system",
            "content": f"""You are a personalized AI tech mentor for {name}.

Their career goal is: {career_path}

Their skill analysis:
{analysis[:1500]}

Their learning roadmap:
{roadmap[:1500]}

Be supportive, specific, and practical. Reference their roadmap and analysis when relevant.
Answer questions about their learning path, suggest resources, help debug concepts, and keep them motivated.
""",
        }
    ]

    # "model" role in DB maps to "assistant" in OpenAI-compatible API
    for msg in history:
        role = "assistant" if msg["role"] == "model" else msg["role"]
        messages.append({"role": role, "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})
    print(f"\n\n\nCHAT WITH MENTOR:\n{messages}\n\n\n")
    return _chat_completion(messages)


def generate_exercise(
    name: str,
    career_path: str,
    analysis: str,
    language: str,
    difficulty: str,
    previous_titles: List[str],
) -> Dict:
    """Generate a coding exercise tailored to the user's level. Returns a dict."""
    avoid = ", ".join(previous_titles[-10:]) if previous_titles else "none"

    messages = [
                {
                        "role": "system",
                        "content": "You are an expert coding interview coach. Generate practical coding exercises. Always respond with valid JSON only, no markdown.",
                },
                {
                        "role": "user",
                        "content": f"""Generate a {difficulty} coding exercise for:
Student: {name}
Career goal: {career_path}
Their level: {analysis[:600]}
Language: {language}
Avoid repeating: {avoid}

STRICT TESTING RULES for test_runner_code:
1. All tests must be independent, reproducible, and cover normal, edge, and error cases.
2. Include at least 3 test cases, with clear assertion messages for failures.
3. Do not depend on global state, files, or user input; tests must be self-contained.
4. Validate both correct and incorrect/edge inputs.
5. Use assert statements (Python) or strict equality checks (JS) with descriptive error messages.
6. Print a clear summary of passed/failed tests.
7. The user must only implement the solution function; never modify the tests.
8. The test runner must always call the student's function and check outputs automatically.
9. All tests must be correct and reflect the problem requirements exactly.
10. Never skip or comment out failing tests; always show all results.

Respond with ONLY this JSON structure (no markdown, no explanation):
{{
    "title": "Exercise title",
    "difficulty": "{difficulty}",
    "topic": "e.g. Arrays, Strings, OOP, Async, etc.",
    "description": "Full problem description with context",
    "examples": [
        {{"input": "example input", "output": "expected output", "explanation": "why"}}
    ],
    "constraints": ["list of constraints like time/space complexity"],
    "starter_code": "the starter code with function signature and docstring",
    "test_runner_code": "complete runnable code that defines the function stub, then runs at least 3 test cases using print/assert, so the student can see pass/fail output, following all STRICT TESTING RULES above."
}}

For test_runner_code: write it so the student's solution function is CALLED and results printed clearly. Follow all STRICT TESTING RULES above.
Example test_runner_code for python:
def solution(nums):
        pass  # student replaces this

assert solution([1,2,3]) == 6, "Test 1 failed: sum of [1,2,3] should be 6"
assert solution([]) == 0, "Test 2 failed: sum of [] should be 0"
assert solution([-1,1]) == 0, "Test 3 failed: sum of [-1,1] should be 0"
print("All tests passed!")
""",
                },
        ]
    raw = _chat_completion(messages, json_mode=True)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    data = json.loads(raw)
    import textwrap
    for field in ("starter_code", "test_runner_code"):
        if field in data and isinstance(data[field], str):
            data[field] = textwrap.dedent(data[field]).strip()
    return data


TOTAL_INTERVIEW_QUESTIONS = 5


def interview_next(
    name: str,
    career_path: str,
    turns: List[Dict],  # list of {"question": str, "answer": str|None}
) -> Dict:
    """Drive a mock technical interview. Returns {"question": str, "is_final": bool, "feedback": str|None, "score": str|None}."""
    turn_num = len(turns)

    history_text = ""
    for i, t in enumerate(turns):
        history_text += f"\nQ{i + 1}: {t['question']}\n"
        if t.get("answer"):
            history_text += f"A{i + 1}: {t['answer']}\n"

    if turn_num >= TOTAL_INTERVIEW_QUESTIONS:
        prompt = f"""You just completed a {TOTAL_INTERVIEW_QUESTIONS}-question technical mock interview with {name} for the {career_path} role.

Interview transcript:
{history_text}

Provide a comprehensive evaluation. Respond ONLY with this JSON (no markdown fences):
{{
  "is_final": true,
  "question": "",
  "feedback": "Detailed markdown evaluation: overall performance, key strengths, areas to improve, specific advice for each answer",
  "score": "X/10"
}}"""
    else:
        intro = "This is the very start of the interview. Begin with a warm professional greeting, then ask your first question." if turn_num == 0 else f"Previous Q&A so far:\n{history_text}\n\nAsk question {turn_num + 1} of {TOTAL_INTERVIEW_QUESTIONS}."
        prompt = f"""You are conducting a technical mock interview with {name} for the {career_path} role.
{intro}

Cover a mix of: technical knowledge, problem-solving approach, past experience, and one behavioral question.
Keep questions concise and clear (2-4 sentences max).

Respond ONLY with this JSON (no markdown fences):
{{
  "is_final": false,
  "question": "Your question here (just the question, no preamble like 'Question 1:')",
  "feedback": null,
  "score": null
}}"""

    messages = [
        {
            "role": "system",
            "content": f"You are a senior technical interviewer at a top tech company. You are conducting a mock interview for a {career_path} candidate. Always respond with valid JSON only.",
        },
        {"role": "user", "content": prompt},
    ]

    raw = _chat_completion(messages, json_mode=True)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)


def parse_roadmap_into_units(roadmap_text: str, career_path: str) -> List[Dict]:
    """Parse a markdown roadmap into structured units with project tasks. Returns list of dicts."""
    messages = [
        {
            "role": "system",
            "content": "You are an expert curriculum designer. Extract structured learning units from roadmaps. Always respond with valid JSON only.",
        },
        {
            "role": "user",
            "content": f"""Parse the following learning roadmap into structured units/phases.

**Career Goal:** {career_path}

**Roadmap:**
{roadmap_text}

For each phase/unit found in the roadmap, create a structured entry.
Respond ONLY with this JSON (array of units, no markdown fences):
[
  {{
    "unit_index": 0,
    "title": "Phase title (e.g. Phase 1 - Foundation)",
    "description": "Concise summary of topics and skills covered in this phase (2-4 sentences)",
    "project_description": "A specific, concrete project the student must build to demonstrate mastery of this phase. Describe what the project should do, what technologies/concepts it must use, and what a successful implementation looks like. Be specific and actionable (3-5 sentences)."
  }}
]

Extract all phases/units from the roadmap. Ensure project_description requires the student to demonstrate the actual skills from that phase.
""",
        },
    ]
    raw = _chat_completion(messages, json_mode=True)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    # The response might be wrapped in an object
    parsed = json.loads(raw)
    if isinstance(parsed, dict):
        # Try common wrapper keys
        for key in ("units", "phases", "roadmap", "items"):
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        # Fall back to values if it's a single-key dict
        vals = list(parsed.values())
        if len(vals) == 1 and isinstance(vals[0], list):
            return vals[0]
    return parsed


def evaluate_github_for_unit(
    name: str,
    career_path: str,
    unit_title: str,
    unit_description: str,
    project_description: str,
    github_data: Dict,
) -> Dict:
    """Evaluate a GitHub project to determine if user can advance past a roadmap unit.
    Returns {"passed": bool, "feedback": str, "score": str}."""
    repo_info = _format_repo_for_prompt(github_data)

    messages = [
        {
            "role": "system",
            "content": "You are a strict but fair technical evaluator assessing if a student's GitHub project demonstrates sufficient knowledge to advance to the next learning phase. Always respond with valid JSON only.",
        },
        {
            "role": "user",
            "content": f"""Evaluate whether this GitHub project demonstrates sufficient mastery to advance past the current learning unit.

**Student:** {name}
**Career Goal:** {career_path}

**Current Unit:** {unit_title}
**Unit Description:** {unit_description}

**Required Project:** {project_description}

**Submitted GitHub Repository:**
{repo_info}

Evaluate the project strictly. The student should only advance if they have genuinely demonstrated the skills required by this unit. Look for:
- Does the project actually implement what was required?
- Is the code quality appropriate for this learning stage?
- Are the key concepts from this unit applied correctly?
- Is there enough substance (not just a skeleton or boilerplate)?

Respond ONLY with this JSON (no markdown fences):
{{
  "passed": true or false,
  "score": "X/10",
  "feedback": "Detailed markdown feedback covering: what was done well, what's missing or insufficient, specific code observations, and clear guidance on what to improve if they did not pass. Be constructive and specific."
}}
""",
        },
    ]
    raw = _chat_completion(messages, json_mode=True)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)


def evaluate_submission(
    name: str,
    exercise_title: str,
    exercise_description: str,
    language: str,
    user_code: str,
    execution_output: str,
    passed: bool,
) -> str:
    """Give detailed feedback on a code submission."""
    status = "passed all tests" if passed else "has some failing tests or errors"

    messages = [
        {
            "role": "system",
            "content": "You are an expert code reviewer and mentor. Give constructive, educational feedback.",
        },
        {
            "role": "user",
            "content": f"""Review this coding exercise submission from {name}.

**Exercise:** {exercise_title}
**Description:** {exercise_description[:500]}
**Language:** {language}
**Status:** The code {status}

**Student's Code:**
```{language}
{user_code}
```

**Execution Output:**
```
{execution_output}
```

Provide feedback covering:
1. **Result** — Did it pass? If not, what went wrong?
2. **Code Quality** — Readability, naming, structure
3. **Approach** — Is the algorithm efficient? Any better approaches?
4. **What they did well** — Genuine positives
5. **Next step** — One specific improvement to try

Be encouraging but honest. Use markdown formatting.
""",
        },
    ]
    return _chat_completion(messages)


def suggest_careers(answers: Dict) -> List[str]:
    """Suggest career paths based on onboarding answers using Ollama."""
    
    # Formateamos las respuestas para el prompt
    answers_text = "\n".join(f"- {k}: {v}" for k, v in answers.items())
    
    # Lista de opciones permitidas (para validación y para el prompt)
    allowed_careers = [
        "Frontend Developer", "Backend Developer", "Full Stack Developer",
        "DevOps / Cloud Engineer", "Data Scientist", "Machine Learning Engineer",
        "Mobile Developer (iOS/Android)", "Cybersecurity Engineer",
        "Blockchain Developer", "QA / Test Engineer"
    ]

    messages = [
        {
            "role": "system",
            "content": f"""You are a Career Advisor Expert. Your task is to analyze user profile and select the top 5 best career paths.
            
            STRICT RULES:
            1. You MUST ONLY pick from this specific list: {allowed_careers}
            2. You MUST respond with a JSON array of strings.
            3. DO NOT include explanations, markdown, or any text outside the JSON array.
            
            EXAMPLE OUTPUT:
            ["Frontend Developer", "Full Stack Developer", "Mobile Developer (iOS/Android)"]"""
        },
        {
            "role": "user",
            "content": f"Analyze these user preferences and return the best matches from the allowed list:\n\n{answers_text}"
        }
    ]

    # Llamada a tu función de completion
    # Asegúrate de que json_mode=True pase el formato 'json' a Ollama
    raw = _chat_completion(messages, json_mode=True)

    try:
        parsed = json.loads(raw)
        
        # Si el modelo devuelve un diccionario en lugar de una lista, extraemos los valores
        if isinstance(parsed, dict):
            # Intentamos obtener una lista de cualquier llave que parezca contener los roles
            for key in ["roles", "suggestions", "career_paths"]:
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                # Si no hay llaves conocidas, tomamos todos los valores que sean strings
                parsed = [v for v in parsed.values() if isinstance(v, str)]

        if isinstance(parsed, list):
            # FILTRO CRÍTICO: Solo permitimos los que están en tu lista oficial
            # Esto elimina cualquier "alucinación" del modelo
            matches = [job for job in parsed if job in allowed_careers]
            
            if matches:
                return matches[:5] # Retornamos máximo 5

    except Exception as e:
        print(f"Error parsing Ollama response: {e}")

    # Fallback dinámico: si todo falla, devolvemos los más genéricos de TU lista
    return ["Full Stack Developer", "Backend Developer", "Frontend Developer"]

