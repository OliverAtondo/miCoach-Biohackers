import httpx
import os
import json
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

_MODEL = os.getenv("AI_Model", "qwen2.5:7b")
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
    response = _chat_completion(messages)
    print(response)
    return response