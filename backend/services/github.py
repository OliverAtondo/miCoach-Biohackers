import httpx
import re
import base64
from typing import List, Dict

# Extensions considered source code (not config/lock/binary)
SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rs", ".cpp", ".c",
    ".cs", ".rb", ".php", ".swift", ".kt", ".scala", ".vue", ".svelte",
    ".html", ".css", ".scss", ".sql", ".sh", ".ipynb",
}

# Files/dirs to skip
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".venv", "venv", "vendor"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock", ".gitignore"}

MAX_FILES = 8        # Max source files to fetch per repo
MAX_FILE_CHARS = 3000  # Max chars per file sent to Gemini


def extract_repo_info(github_url: str) -> Dict[str, str] | None:
    pattern = r"github\.com/([^/]+)/([^/\s]+)"
    match = re.search(pattern, github_url)
    if not match:
        return None
    owner, repo = match.group(1), match.group(2).rstrip(".git")
    return {"owner": owner, "repo": repo}


def _is_source_file(path: str) -> bool:
    parts = path.split("/")
    if any(part in SKIP_DIRS for part in parts[:-1]):
        return False
    filename = parts[-1]
    if filename in SKIP_FILES:
        return False
    ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
    return ext in SOURCE_EXTENSIONS


async def fetch_repo_summary(github_url: str) -> Dict:
    info = extract_repo_info(github_url)
    if not info:
        return {"name": github_url, "error": "Invalid GitHub URL"}

    owner, repo = info["owner"], info["repo"]
    gh_headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "MyCoach-App"}

    async with httpx.AsyncClient(timeout=15.0) as client:

        # 1. Repo metadata
        try:
            r = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=gh_headers)
            repo_data = r.json() if r.status_code == 200 else {}
        except Exception:
            repo_data = {}

        default_branch = repo_data.get("default_branch", "main")

        # 2. Languages breakdown
        try:
            r = await client.get(f"https://api.github.com/repos/{owner}/{repo}/languages", headers=gh_headers)
            languages = r.json() if r.status_code == 200 else {}
        except Exception:
            languages = {}

        # 3. README
        try:
            r = await client.get(f"https://api.github.com/repos/{owner}/{repo}/readme", headers=gh_headers)
            if r.status_code == 200:
                readme_raw = base64.b64decode(r.json().get("content", "")).decode("utf-8", errors="ignore")
            else:
                readme_raw = "No README."
        except Exception:
            readme_raw = "Could not fetch README."

        # 4. Full file tree
        try:
            r = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}",
                headers=gh_headers,
                params={"recursive": "1"},
            )
            tree = r.json().get("tree", []) if r.status_code == 200 else []
        except Exception:
            tree = []

        # 5. Pick source files and fetch their content
        source_paths = [
            item["path"] for item in tree
            if item.get("type") == "blob" and _is_source_file(item["path"])
        ]

        # Prioritize: shorter paths (top-level) and entry-point names first
        entry_names = {"main", "index", "app", "server", "api", "routes", "models"}
        def priority(path: str) -> tuple:
            depth = path.count("/")
            name = path.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
            is_entry = name in entry_names
            return (depth, not is_entry)

        source_paths.sort(key=priority)
        source_paths = source_paths[:MAX_FILES]

        code_samples = []
        for path in source_paths:
            try:
                r = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                    headers=gh_headers,
                )
                if r.status_code == 200:
                    encoded = r.json().get("content", "")
                    content = base64.b64decode(encoded).decode("utf-8", errors="ignore")
                    code_samples.append({
                        "path": path,
                        "content": content[:MAX_FILE_CHARS],
                        "truncated": len(content) > MAX_FILE_CHARS,
                    })
            except Exception:
                continue

    return {
        "name": f"{owner}/{repo}",
        "description": repo_data.get("description") or "No description.",
        "language": repo_data.get("language") or "Unknown",
        "languages": languages,
        "stars": repo_data.get("stargazers_count", 0),
        "readme": readme_raw[:1500],
        "file_tree": [item["path"] for item in tree if item.get("type") == "blob"][:60],
        "code_samples": code_samples,
    }


async def fetch_all_repos(github_links: List[str]) -> List[Dict]:
    results = []
    for link in github_links:
        if link.strip():
            summary = await fetch_repo_summary(link.strip())
            results.append(summary)
    return results
